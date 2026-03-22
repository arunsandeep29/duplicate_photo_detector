import React, { useState } from 'react';
import { apiClient, ApiError, ScanResponse } from '../services/api';
import './DirectoryPicker.css';

interface DirectoryPickerProps {
  onScanComplete?: (scanId: string, imageCount: number) => void;
}

interface ScanState {
  isLoading: boolean;
  error: string | null;
  successMessage: string | null;
  imageCount: number | null;
}

/**
 * DirectoryPicker Component
 * Allows users to select a directory and initiate a scan for duplicate images.
 * 
 * Features:
 * - Input field for directory path
 * - Validation feedback
 * - Loading state with spinner
 * - Success message with image count
 * - Error message display
 * - Keyboard navigation support
 * - Accessibility labels and ARIA attributes
 */
const DirectoryPicker: React.FC<DirectoryPickerProps> = ({ onScanComplete }) => {
  const [directory, setDirectory] = useState<string>('');
  const [scanState, setScanState] = useState<ScanState>({
    isLoading: false,
    error: null,
    successMessage: null,
    imageCount: null,
  });

  const handleDirectoryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDirectory(e.target.value);
    // Clear error when user starts typing
    if (scanState.error) {
      setScanState((prev) => ({ ...prev, error: null }));
    }
  };

  const handleScan = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    // Validation
    if (!directory.trim()) {
      setScanState({
        isLoading: false,
        error: 'Please enter a directory path',
        successMessage: null,
        imageCount: null,
      });
      return;
    }

    // Start scan
    setScanState({
      isLoading: true,
      error: null,
      successMessage: null,
      imageCount: null,
    });

    const result = await apiClient.scanDirectory(directory);

    // Handle response
    if ('error' in result) {
      const apiError = result as ApiError;
      let errorMessage = apiError.error;

      // Map common error codes to user-friendly messages
      if (errorMessage.includes('DIRECTORY_NOT_FOUND')) {
        errorMessage = 'Directory not found. Please check the path and try again.';
      } else if (errorMessage.includes('PERMISSION_DENIED')) {
        errorMessage = 'Permission denied. Make sure you have read access to this directory.';
      } else if (errorMessage.includes('NOT_A_DIRECTORY')) {
        errorMessage = 'The provided path is not a directory.';
      } else if (errorMessage.includes('CORS error')) {
        errorMessage = 'Unable to connect to the server. Please ensure the backend is running.';
      } else if (errorMessage.includes('timeout')) {
        errorMessage = 'Request timed out. The scan took too long. Please try again.';
      }

      setScanState({
        isLoading: false,
        error: errorMessage,
        successMessage: null,
        imageCount: null,
      });
      return;
    }

    // Success
    const scanResponse = result as ScanResponse;
    const successMsg = `Scan complete! Found ${scanResponse.image_count} image${scanResponse.image_count !== 1 ? 's' : ''}`;
    setScanState({
      isLoading: false,
      error: null,
      successMessage: successMsg,
      imageCount: scanResponse.image_count,
    });

    // Call callback if provided
    if (onScanComplete) {
      onScanComplete(scanResponse.scan_id, scanResponse.image_count);
    }
  };

  return (
    <div className="directory-picker">
      <form onSubmit={handleScan} className="directory-picker-form">
        <div className="form-group">
          <label htmlFor="directory-input" className="form-label">
            Directory Path
          </label>
          <input
            id="directory-input"
            type="text"
            className="directory-input"
            placeholder="Enter the directory path (e.g., /home/user/Photos)"
            value={directory}
            onChange={handleDirectoryChange}
            disabled={scanState.isLoading}
            aria-describedby={
              scanState.error
                ? 'directory-error'
                : scanState.successMessage
                  ? 'directory-success'
                  : undefined
            }
            aria-invalid={!!scanState.error}
          />
        </div>

        <button
          type="submit"
          className="scan-button"
          disabled={scanState.isLoading || !directory.trim()}
          aria-busy={scanState.isLoading}
          aria-label={scanState.isLoading ? 'Scanning in progress' : 'Start scan'}
        >
          {scanState.isLoading ? (
            <>
              <span className="spinner" aria-hidden="true" />
              Scanning...
            </>
          ) : (
            'Scan'
          )}
        </button>
      </form>

      {scanState.error && (
        <div className="error-message" id="directory-error" role="alert">
          <span className="error-icon" aria-hidden="true">
            ✗
          </span>
          {scanState.error}
        </div>
      )}

      {scanState.successMessage && (
        <div className="success-message" id="directory-success" role="status" aria-live="polite">
          <span className="success-icon" aria-hidden="true">
            ✓
          </span>
          {scanState.successMessage}
        </div>
      )}
    </div>
  );
};

export default DirectoryPicker;
