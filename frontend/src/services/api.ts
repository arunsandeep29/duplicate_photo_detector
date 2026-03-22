/**
 * API Error interface for standardized error responses
 */
export interface ApiError {
  error: string;
  status: number;
}

/**
 * Request/Response interfaces for API endpoints
 */

export interface ScanRequest {
  directory: string;
}

export interface ScanResponse {
  scan_id: string;
  image_count: number;
}

/**
 * DuplicateGroupFull documents the full structure returned by GET /api/duplicates/{scan_id}
 *
 * - original: absolute file path of the original image
 * - hash: perceptual hash string
 * - copies: array of absolute file paths of duplicate images
 * - details: optional object mapping file path to details (may be missing or missing keys)
 *   - details[path]: {
 *       resolution: [width, height] (optional)
 *       is_blurred: boolean (optional)
 *       blur_score: number (optional)
 *       thumbnail: data URI string (optional)
 *       hamming_distance: number (optional)
 *       reason: string (optional, e.g. 'Perceptual hash match')
 *     }
 * - original_thumbnail: data URI string for original (optional)
 * - original_resolution: [width, height] (optional)
 * - original_is_blurred: boolean (optional)
 * - blurred: array of file paths of blurred copies (optional)
 */
export interface DuplicateImageInfo {
  path: string;
  preview_url?: string;
  quality_score?: number;
  reason?: string;
}

export interface DuplicateGroupFull {
  hash: string;
  // The API now returns structured image objects for original and copies
  original: DuplicateImageInfo;
  copies: DuplicateImageInfo[];
  // Backwards-compatible optional fields (may be present from older backends)
  details?: {
    [filePath: string]: {
      resolution?: [number, number];
      is_blurred?: boolean;
      blur_score?: number;
      thumbnail?: string;
      hamming_distance?: number;
      reason?: string;
    };
  };
  original_thumbnail?: string;
  original_resolution?: [number, number];
  original_is_blurred?: boolean;
  blurred?: string[];
}

export interface DuplicatesResponse {
  groups: DuplicateGroupFull[];
}

// Updated type for use throughout the frontend
export interface DuplicateGroup {
  hash: string;
  original: DuplicateImageInfo;
  copies: DuplicateImageInfo[];
}


export interface MoveOperation {
  original: string;
  target_copy: string;
  action: 'move' | 'delete';
}

export interface MoveOperationError {
  file: string;
  reason: string;
}

export interface MoveDuplicatesRequest {
  scan_id: string;
  destination: string;
  operations: MoveOperation[];
}

export interface MoveDuplicatesResponse {
  moved_count: number;
  failed_count: number;
  errors: MoveOperationError[];
}

export interface HealthCheckResponse {
  status: string;
  backend_version?: string;
}

/**
 * Type guard to check if a response is an ApiError
 */
function isApiError(response: unknown): response is ApiError {
  return (
    typeof response === 'object' &&
    response !== null &&
    'error' in response &&
    'status' in response
  );
}

/**
 * Creates a timeout promise that rejects after the specified milliseconds
 */
function createTimeoutPromise(ms: number): Promise<never> {
  return new Promise((_resolve, reject) => {
    setTimeout(() => {
      reject(new Error('Request timeout'));
    }, ms);
  });
}

/**
 * Validates that required fields are present in a response object
 */
function validateResponseFields(
  response: unknown,
  requiredFields: string[]
): void {
  if (typeof response !== 'object' || response === null) {
    throw new Error('Invalid response format');
  }

  for (const field of requiredFields) {
    if (!(field in response)) {
      throw new Error(`Missing required field: ${field}`);
    }
  }
}

/**
 * API Client Service
 * Handles all communication with the backend API with comprehensive error handling
 */
class ApiClient {
  private baseUrl: string;
  private timeout = 30000; // 30 seconds

  constructor(baseUrl?: string) {
    if (baseUrl) {
      this.baseUrl = baseUrl;
    } else {
      const apiBaseUrl = process.env.REACT_APP_API_BASE_URL;
      if (!apiBaseUrl) {
        throw new Error(
          'REACT_APP_API_BASE_URL environment variable is not set'
        );
      }
      this.baseUrl = apiBaseUrl;
    }
  }

  /**
   * Generic fetch wrapper with error handling and timeout
   */
  private async fetchWithTimeout(
    url: string,
    options: RequestInit = {}
  ): Promise<Response> {
    try {
      const response = await Promise.race([
        fetch(url, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
        }),
        createTimeoutPromise(this.timeout),
      ]);
      return response;
    } catch (error) {
      if (error instanceof Error && error.message === 'Request timeout') {
        throw { error: 'Request timeout', status: 0 };
      }
      // Network error or CORS error
      if (error instanceof TypeError) {
        throw {
          error: 'CORS error - backend not responding',
          status: 0,
        };
      }
      throw error;
    }
  }

  /**
   * Generic response handler
   */
  private async handleResponse<T>(response: Response): Promise<T | ApiError> {
    if (!response.ok) {
      const contentType = response.headers.get('content-type');
      let errorMessage = `HTTP ${response.status}`;

      try {
        if (contentType?.includes('application/json')) {
          const errorData = await response.json();
          if (
            typeof errorData === 'object' &&
            errorData !== null &&
            'error' in errorData
          ) {
            errorMessage = errorData.error;
          }
        }
      } catch {
        // If JSON parsing fails, just use the HTTP status message
        errorMessage = response.statusText || `HTTP ${response.status}`;
      }

      return {
        error: errorMessage,
        status: response.status,
      };
    }

    try {
      const contentType = response.headers.get('content-type');
      if (!contentType?.includes('application/json')) {
        return {
          error: 'Invalid response format',
          status: 0,
        };
      }
      return await response.json();
    } catch {
      return {
        error: 'Invalid response format',
        status: 0,
      };
    }
  }

  /**
   * Scans a directory for duplicate images
   * @param directory - Path to the directory to scan
   * @returns Scan ID and image count on success, or ApiError on failure
   */
  async scanDirectory(directory: string): Promise<ScanResponse | ApiError> {
    try {
      const request: ScanRequest = { directory };
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/api/scan`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      );

      const result = await this.handleResponse<ScanResponse>(response);

      if (isApiError(result)) {
        return result;
      }

      validateResponseFields(result, ['scan_id', 'image_count']);
      return result as ScanResponse;
    } catch (error) {
      if (isApiError(error)) {
        return error;
      }
      return {
        error: `Failed to scan directory: ${error instanceof Error ? error.message : 'Unknown error'}`,
        status: 0,
      };
    }
  }

  /**
   * Retrieves duplicate image groups for a scan
   * @param scanId - The scan ID to retrieve duplicates for
   * @returns Duplicate groups on success, or ApiError on failure
   */
  async getDuplicates(scanId: string): Promise<DuplicatesResponse | ApiError> {
    try {
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/api/duplicates/${encodeURIComponent(scanId)}`,
        {
          method: 'GET',
        }
      );

      const result = await this.handleResponse<DuplicatesResponse>(response);

      if (isApiError(result)) {
        return result;
      }

      validateResponseFields(result, ['groups']);
      return result as DuplicatesResponse;
    } catch (error) {
      if (isApiError(error)) {
        return error;
      }
      return {
        error: `Failed to get duplicates: ${error instanceof Error ? error.message : 'Unknown error'}`,
        status: 0,
      };
    }
  }

  /**
   * Moves duplicate files to a destination directory
   * @param scanId - The scan ID
   * @param operations - Array of move operations
   * @param destination - Destination directory path
   * @returns Count of moved and failed files on success, or ApiError on failure
   */
  async moveDuplicates(
    scanId: string,
    operations: MoveOperation[],
    destination: string
  ): Promise<MoveDuplicatesResponse | ApiError> {
    try {
      const request: MoveDuplicatesRequest = {
        scan_id: scanId,
        operations,
        destination,
      };

      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/api/move-duplicates`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      );

      const result = await this.handleResponse<MoveDuplicatesResponse>(
        response
      );

      if (isApiError(result)) {
        return result;
      }

      validateResponseFields(result, ['moved_count', 'failed_count']);
      return result as MoveDuplicatesResponse;
    } catch (error) {
      if (isApiError(error)) {
        return error;
      }
      return {
        error: `Failed to move duplicates: ${error instanceof Error ? error.message : 'Unknown error'}`,
        status: 0,
      };
    }
  }

  /**
   * Performs a health check on the backend API
   * @returns Health status on success, or ApiError on failure
   */
  async healthCheck(): Promise<HealthCheckResponse | ApiError> {
    try {
      const response = await this.fetchWithTimeout(
        `${this.baseUrl}/api/health`,
        {
          method: 'GET',
        }
      );

      const result = await this.handleResponse<HealthCheckResponse>(response);

      if (isApiError(result)) {
        return result;
      }

      validateResponseFields(result, ['status']);
      const typedResult = result as HealthCheckResponse;
      
      // Validate that status is "ok"
      if (typedResult.status !== 'ok') {
        return {
          error: `Unexpected health status: ${typedResult.status}`,
          status: 0,
        };
      }
      
      return typedResult;
    } catch (error) {
      if (isApiError(error)) {
        return error;
      }
      return {
        error: `Health check failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        status: 0,
      };
    }
  }
}

// Export a singleton instance
export const apiClient = new ApiClient();

export default ApiClient;
