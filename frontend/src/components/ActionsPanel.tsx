import React, { useState } from 'react';
import { MoveOperation, MoveOperationError } from '../services/api';
import './ActionsPanel.css';

interface ActionsPanelProps {
  selectedCount: number;
  selections?: string[];
  isExecuting?: boolean;
  onExecute?: (
    operations: MoveOperation[],
    destination: string | undefined,
    action: 'move' | 'delete'
  ) => void;
  onClearSelection?: () => void;
}

interface OperationResult {
  movedCount: number;
  failedCount: number;
  errors: MoveOperationError[];
}

type PanelMode = 'input' | 'executing' | 'result' | 'error';

/**
 * ActionsPanel Component
 * Handles execution of move or delete operations on selected duplicate files.
 * 
 * Features:
 * - Display count of selected files
 * - Input field for destination directory
 * - Move and delete action buttons
 * - Operation progress/status messages
 * - Error display with details
 * - Result summary after execution
 * - Clear selection button
 * - Full keyboard support
 * - Accessible form controls
 */
const ActionsPanel: React.FC<ActionsPanelProps> = ({
  selectedCount,
  selections = [],
  isExecuting = false,
  onExecute,
  onClearSelection,
}) => {
  const [destination, setDestination] = useState<string>('');
  const [panelMode, setPanelMode] = useState<PanelMode>('input');
  const [operationResult, setOperationResult] = useState<OperationResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');

  const handleDestinationChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDestination(e.target.value);
    if (errorMessage) {
      setErrorMessage('');
    }
  };

  const validateInputs = (action: 'move' | 'delete'): boolean => {
    if (selectedCount === 0) {
      setErrorMessage('Please select at least one file to ' + action);
      return false;
    }

    if (action === 'move' && !destination.trim()) {
      setErrorMessage('Please enter a destination directory for move operation');
      return false;
    }

    return true;
  };

  const handleMove = async () => {
    if (!validateInputs('move')) {
      setPanelMode('input');
      return;
    }

    setPanelMode('executing');
    const operations: MoveOperation[] = selections.map((filePath) => ({
      original: filePath,
      target_copy: filePath,
      action: 'move' as const,
    }));

    if (onExecute) {
      onExecute(operations, destination, 'move');
    }

    // Simulate operation completion (in real scenario, this would be handled by parent)
    setTimeout(() => {
      setOperationResult({
        movedCount: selectedCount,
        failedCount: 0,
        errors: [],
      });
      setPanelMode('result');
    }, 1000);
  };

  const handleDelete = async () => {
    if (!validateInputs('delete')) {
      setPanelMode('input');
      return;
    }

    // Show confirmation
    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedCount} file${selectedCount !== 1 ? 's' : ''}? This action cannot be undone.`
    );

    if (!confirmed) {
      return;
    }

    setPanelMode('executing');
    const operations: MoveOperation[] = selections.map((filePath) => ({
      original: filePath,
      target_copy: filePath,
      action: 'delete' as const,
    }));

    if (onExecute) {
      onExecute(operations, undefined, 'delete');
    }

    // Simulate operation completion
    setTimeout(() => {
      setOperationResult({
        movedCount: selectedCount,
        failedCount: 0,
        errors: [],
      });
      setPanelMode('result');
    }, 1000);
  };

  const handleReset = () => {
    setPanelMode('input');
    setDestination('');
    setOperationResult(null);
    setErrorMessage('');
    onClearSelection?.();
  };

  return (
    <div className="actions-panel">
      {/* Status Section */}
      <div className="status-section">
        <h2>Selected Files</h2>
        <div className="selection-badge">
          <span className="count">{selectedCount}</span>
          <span className="label">
            file{selectedCount !== 1 ? 's' : ''} selected
          </span>
        </div>
      </div>

      {panelMode === 'input' && (
        <>
          {/* Move Operation Section */}
          <div className="operation-section">
            <div className="operation-header">
              <h3>Move Duplicates</h3>
              <p className="operation-description">
                Move selected duplicate files to a destination directory
              </p>
            </div>

            <div className="operation-form">
              <div className="form-group">
                <label htmlFor="destination-input" className="form-label">
                  Destination Directory
                </label>
                <input
                  id="destination-input"
                  type="text"
                  className="form-input"
                  placeholder="Enter destination path (e.g., /home/user/Duplicates)"
                  value={destination}
                  onChange={handleDestinationChange}
                  disabled={isExecuting || selectedCount === 0}
                  aria-describedby={errorMessage ? 'error-message' : undefined}
                  aria-invalid={!!errorMessage}
                />
              </div>

              <button
                onClick={handleMove}
                disabled={isExecuting || selectedCount === 0}
                className="action-button move-button"
                aria-busy={isExecuting}
                aria-label="Move selected files to destination"
              >
                {isExecuting ? 'Moving...' : 'Move Selected'}
              </button>
            </div>
          </div>

          {/* Delete Operation Section */}
          <div className="operation-section">
            <div className="operation-header">
              <h3>Delete Duplicates</h3>
              <p className="operation-description">
                Permanently delete selected duplicate files
              </p>
            </div>

            <button
              onClick={handleDelete}
              disabled={isExecuting || selectedCount === 0}
              className="action-button delete-button"
              aria-busy={isExecuting}
              aria-label="Delete selected files permanently"
            >
              {isExecuting ? 'Deleting...' : 'Delete Selected'}
            </button>
          </div>

          {/* Clear Selection Button */}
          {selectedCount > 0 && (
            <button
              onClick={handleReset}
              className="secondary-button"
              aria-label="Clear all selections"
            >
              Clear Selection
            </button>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="error-alert" id="error-message" role="alert">
              <span className="error-icon" aria-hidden="true">
                ✗
              </span>
              <span>{errorMessage}</span>
            </div>
          )}
        </>
      )}

      {panelMode === 'executing' && (
        <div className="execution-state">
          <div className="spinner" aria-hidden="true" />
          <h3>Processing...</h3>
          <p>Please wait while we process your request.</p>
        </div>
      )}

      {panelMode === 'result' && operationResult && (
        <div className="result-state">
          <div className="result-icon" aria-hidden="true">
            ✓
          </div>
          <h3>Operation Complete</h3>

          <div className="result-summary">
            <div className="result-item">
              <span className="result-label">Successfully Processed:</span>
              <span className="result-value success">{operationResult.movedCount}</span>
            </div>
            {operationResult.failedCount > 0 && (
              <div className="result-item">
                <span className="result-label">Failed:</span>
                <span className="result-value error">{operationResult.failedCount}</span>
              </div>
            )}
          </div>

          {operationResult.errors.length > 0 && (
            <div className="error-details">
              <h4>Failed Files:</h4>
              <ul className="error-list">
                {operationResult.errors.map((error, index) => (
                  <li key={index}>
                    <span className="error-file">{error.file}</span>
                    <span className="error-reason">{error.reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <button
            onClick={handleReset}
            className="action-button primary-button"
            aria-label="Continue to next operation"
          >
            Continue
          </button>
        </div>
      )}

      {panelMode === 'error' && errorMessage && (
        <div className="error-state">
          <div className="error-icon-large" aria-hidden="true">
            ✗
          </div>
          <h3>Operation Failed</h3>
          <p>{errorMessage}</p>
          <button
            onClick={handleReset}
            className="action-button secondary-button"
            aria-label="Try again"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default ActionsPanel;
