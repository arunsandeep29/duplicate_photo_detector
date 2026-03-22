/**
 * API Client Service Tests
 * Tests all 4 API endpoints and comprehensive error handling
 */

import {
  apiClient,
  ApiError,
  ScanResponse,
  DuplicatesResponse,
  MoveDuplicatesResponse,
  HealthCheckResponse,
  MoveOperation,
} from './api';

// Mock fetch globally
global.fetch = jest.fn();

/**
 * Helper to create a mock fetch response
 */
function mockFetchResponse(
  status: number,
  body: unknown,
  contentType = 'application/json'
): Response {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: `${status}`,
    headers: new Headers({ 'content-type': contentType }),
    json: jest.fn().mockResolvedValue(body),
    text: jest.fn().mockResolvedValue(JSON.stringify(body)),
  } as unknown as Response;
}

describe('API Client - scanDirectory endpoint', () => {
  it('should successfully scan a directory', async () => {
    const mockResponse: ScanResponse = {
      scan_id: 'scan-123',
      image_count: 42,
    };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(200, mockResponse)
    );

    const result = await apiClient.scanDirectory('/test/path');

    expect(result).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/scan'),
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('should handle HTTP 400 error', async () => {
    const errorResponse = { error: 'Invalid directory path' };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(400, errorResponse)
    );

    const result = (await apiClient.scanDirectory('/invalid')) as ApiError;

    expect(result.status).toBe(400);
    expect(result.error).toBe('Invalid directory path');
  });

  it('should handle HTTP 404 error', async () => {
    const errorResponse = { error: 'Endpoint not found' };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(404, errorResponse)
    );

    const result = (await apiClient.scanDirectory('/test')) as ApiError;

    expect(result.status).toBe(404);
  });

  it('should handle HTTP 500 error', async () => {
    const errorResponse = { error: 'Server error' };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(500, errorResponse)
    );

    const result = (await apiClient.scanDirectory('/test')) as ApiError;

    expect(result.status).toBe(500);
  });

  it('should handle network error', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(
      new TypeError('Network error')
    );

    const result = (await apiClient.scanDirectory('/test')) as ApiError;

    expect(result.status).toBe(0);
    expect(result.error).toContain('CORS error');
  });

  it('should handle timeout', async () => {
    jest.useFakeTimers();
    jest.setTimeout(10000);

    const mockFetch = jest.fn(() =>
      new Promise((resolve) => {
        setTimeout(() => resolve(mockFetchResponse(200, {})), 31000);
      })
    );
    (global.fetch as jest.Mock) = mockFetch;

    const promise = apiClient.scanDirectory('/test');

    // Advance timers to trigger the timeout
    jest.advanceTimersByTime(31000);

    const result = (await promise) as ApiError;

    jest.useRealTimers();

    expect(result.status).toBe(0);
    expect(result.error).toContain('timeout');
  });

  it('should handle invalid JSON response', async () => {
    const response = {
      ok: true,
      status: 200,
      statusText: '200',
      headers: new Headers({ 'content-type': 'application/json' }),
      json: jest.fn().mockRejectedValue(new Error('Invalid JSON')),
    } as unknown as Response;

    (global.fetch as jest.Mock).mockResolvedValue(response);

    const result = (await apiClient.scanDirectory('/test')) as ApiError;

    expect(result.error).toContain('Invalid response format');
  });

  it('should validate required response fields', async () => {
    const incompleteResponse = { scan_id: 'scan-123' }; // missing image_count
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(200, incompleteResponse)
    );

    const result = (await apiClient.scanDirectory('/test')) as ApiError;

    expect(result.error).toContain('Missing required field');
  });
});

describe('API Client - getDuplicates endpoint', () => {
  it('should successfully retrieve duplicates', async () => {
    const mockResponse: DuplicatesResponse = {
      groups: [
        {
          original: '/path/original1.jpg',
          copies: ['/path/image1.jpg', '/path/image2.jpg'],
          hash: 'abc123def456',
        },
      ],
    };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(200, mockResponse)
    );

    const result = await apiClient.getDuplicates('scan-123');

    expect(result).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/duplicates'),
      expect.objectContaining({
        method: 'GET',
      })
    );
  });

  it('should handle HTTP 400 error for getDuplicates', async () => {
    const errorResponse = { error: 'Invalid scan ID' };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(400, errorResponse)
    );

    const result = (await apiClient.getDuplicates('invalid-id')) as ApiError;

    expect(result.status).toBe(400);
  });

  it('should handle HTTP 404 error for getDuplicates', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(404, { error: 'Scan not found' })
    );

    const result = (await apiClient.getDuplicates('nonexistent')) as ApiError;

    expect(result.status).toBe(404);
  });

  it('should handle HTTP 500 error for getDuplicates', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(500, { error: 'Server error' })
    );

    const result = (await apiClient.getDuplicates('scan-123')) as ApiError;

    expect(result.status).toBe(500);
  });

  it('should handle timeout for getDuplicates', async () => {
    jest.useFakeTimers();
    jest.setTimeout(10000);

    const mockFetch = jest.fn(() =>
      new Promise((resolve) => {
        setTimeout(() => resolve(mockFetchResponse(200, {})), 31000);
      })
    );
    (global.fetch as jest.Mock) = mockFetch;

    const promise = apiClient.getDuplicates('scan-123');

    // Advance timers to trigger the timeout
    jest.advanceTimersByTime(31000);

    const result = (await promise) as ApiError;

    jest.useRealTimers();

    expect(result.status).toBe(0);
    expect(result.error).toContain('timeout');
  });

  it('should validate required response fields for getDuplicates', async () => {
    const incompleteResponse = {}; // missing groups
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(200, incompleteResponse)
    );

    const result = (await apiClient.getDuplicates('scan-123')) as ApiError;

    expect(result.error).toContain('Missing required field');
  });
});

describe('API Client - moveDuplicates endpoint', () => {
  it('should successfully move duplicates', async () => {
    const mockResponse: MoveDuplicatesResponse = {
      moved_count: 10,
      failed_count: 0,
      errors: [],
    };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(200, mockResponse)
    );

    const operations: MoveOperation[] = [
      { original: '/path/original.jpg', target_copy: '/path/dup1.jpg', action: 'move' },
    ];
    const result = await apiClient.moveDuplicates(
      'scan-123',
      operations,
      '/dest'
    );

    expect(result).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/move-duplicates'),
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  it('should handle HTTP 400 error for moveDuplicates', async () => {
    const errorResponse = { error: 'Invalid request' };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(400, errorResponse)
    );

    const result = (await apiClient.moveDuplicates(
      'scan-123',
      [],
      '/dest'
    )) as ApiError;

    expect(result.status).toBe(400);
  });

  it('should handle HTTP 404 error for moveDuplicates', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(404, { error: 'Scan not found' })
    );

    const result = (await apiClient.moveDuplicates(
      'nonexistent',
      [],
      '/dest'
    )) as ApiError;

    expect(result.status).toBe(404);
  });

  it('should handle HTTP 500 error for moveDuplicates', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(500, { error: 'Server error' })
    );

    const result = (await apiClient.moveDuplicates(
      'scan-123',
      [],
      '/dest'
    )) as ApiError;

    expect(result.status).toBe(500);
  });

  it('should handle network error for moveDuplicates', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(
      new TypeError('Network error')
    );

    const result = (await apiClient.moveDuplicates(
      'scan-123',
      [],
      '/dest'
    )) as ApiError;

    expect(result.status).toBe(0);
    expect(result.error).toContain('CORS error');
  });

  it('should validate required response fields for moveDuplicates', async () => {
    const incompleteResponse = { moved_count: 5 }; // missing failed_count
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(200, incompleteResponse)
    );

    const result = (await apiClient.moveDuplicates(
      'scan-123',
      [],
      '/dest'
    )) as ApiError;

    expect(result.error).toContain('Missing required field');
  });
});

describe('API Client - healthCheck endpoint', () => {
  it('should successfully perform health check', async () => {
    const mockResponse: HealthCheckResponse = {
      status: 'ok',
      backend_version: '0.1.0',
    };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(200, mockResponse)
    );

    const result = await apiClient.healthCheck();

    expect(result).toEqual(mockResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/health'),
      expect.objectContaining({
        method: 'GET',
      })
    );
  });

  it('should handle HTTP 400 error for healthCheck', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(400, { error: 'Bad request' })
    );

    const result = (await apiClient.healthCheck()) as ApiError;

    expect(result.status).toBe(400);
  });

  it('should handle HTTP 404 error for healthCheck', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(404, { error: 'Not found' })
    );

    const result = (await apiClient.healthCheck()) as ApiError;

    expect(result.status).toBe(404);
  });

  it('should handle HTTP 500 error for healthCheck', async () => {
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(500, { error: 'Server error' })
    );

    const result = (await apiClient.healthCheck()) as ApiError;

    expect(result.status).toBe(500);
  });

  it('should handle timeout for healthCheck', async () => {
    jest.useFakeTimers();
    jest.setTimeout(10000);

    const mockFetch = jest.fn(() =>
      new Promise((resolve) => {
        setTimeout(() => resolve(mockFetchResponse(200, {})), 31000);
      })
    );
    (global.fetch as jest.Mock) = mockFetch;

    const promise = apiClient.healthCheck();

    // Advance timers to trigger the timeout
    jest.advanceTimersByTime(31000);

    const result = (await promise) as ApiError;

    jest.useRealTimers();

    expect(result.status).toBe(0);
    expect(result.error).toContain('timeout');
  });

  it('should validate required response fields for healthCheck', async () => {
    const incompleteResponse = { backend_version: '0.1.0' }; // missing status
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(200, incompleteResponse)
    );

    const result = (await apiClient.healthCheck()) as ApiError;

    expect(result.error).toContain('Missing required field');
  });
});

describe('API Client - Error Handling', () => {
  it('should handle CORS errors', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(
      new TypeError('Failed to fetch')
    );

    const result = (await apiClient.scanDirectory('/test')) as ApiError;

    expect(result.status).toBe(0);
    expect(result.error).toContain('CORS');
  });

  it('should handle missing Content-Type header', async () => {
    const response = {
      ok: true,
      status: 200,
      statusText: '200',
      headers: new Headers({}),
      json: jest.fn().mockResolvedValue({ data: 'test' }),
    } as unknown as Response;

    (global.fetch as jest.Mock).mockResolvedValue(response);

    const result = (await apiClient.scanDirectory('/test')) as ApiError;

    expect(result.error).toContain('Invalid response format');
  });

  it('should extract error message from error response body', async () => {
    const errorResponse = { error: 'Detailed error message' };
    (global.fetch as jest.Mock).mockResolvedValue(
      mockFetchResponse(400, errorResponse)
    );

    const result = (await apiClient.scanDirectory('/test')) as ApiError;

    expect(result.error).toBe('Detailed error message');
  });
});
