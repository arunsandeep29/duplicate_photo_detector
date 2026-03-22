import React, { useState, useEffect } from 'react';
import './styles/App.css';
import DirectoryPicker from './components/DirectoryPicker';
import DuplicatesList from './components/DuplicatesList';
import ActionsPanel from './components/ActionsPanel';
import { apiClient, DuplicateGroup, MoveOperation, ApiError } from './services/api';

/**
 * App Component - Phase 4
 * Complete workflow orchestration for duplicate photos finder
 * 
 * Workflow:
 * 1. DirectoryPicker - User selects directory and initiates scan
 * 2. DuplicatesList - Display found duplicates and user selects which to delete/move
 * 3. ActionsPanel - User chooses action (move/delete) and executes
 */

interface AppState {
  currentScan: {
    scanId: string | null;
    imageCount: number | null;
  };
  duplicateGroups: DuplicateGroup[];
  selectedFiles: string[];
  isLoading: boolean;
  error: string | null;
  operationInProgress: boolean;
}

const App: React.FC = () => {
  const [isHealthy, setIsHealthy] = useState<boolean>(false);
  const [appState, setAppState] = useState<AppState>({
    currentScan: {
      scanId: null,
      imageCount: null,
    },
    duplicateGroups: [],
    selectedFiles: [],
    isLoading: false,
    error: null,
    operationInProgress: false,
  });

  // Check backend health on app load
  useEffect(() => {
    const checkHealth = async () => {
      const result = await apiClient.healthCheck();
      if ('status' in result && result.status === 'ok') {
        setIsHealthy(true);
      }
    };

    checkHealth();
  }, []);

  /**
   * Handle scan completion from DirectoryPicker
   */
  const handleScanComplete = async (scanId: string, imageCount: number) => {
    setAppState((prev) => ({
      ...prev,
      currentScan: { scanId, imageCount },
      isLoading: true,
      error: null,
    }));

    // Fetch duplicates
    const result = await apiClient.getDuplicates(scanId);

    if ('error' in result) {
      const apiError = result as ApiError;
      setAppState((prev) => ({
        ...prev,
        isLoading: false,
        error: apiError.error,
        duplicateGroups: [],
      }));
      return;
    }

    const groups = result.groups;
    setAppState((prev) => ({
      ...prev,
      duplicateGroups: groups,
      selectedFiles: [],
      isLoading: false,
      error: null,
    }));
  };

  /**
   * Handle selection change from DuplicatesList
   */
  const handleSelectionChange = (selectedFiles: string[]) => {
    setAppState((prev) => ({
      ...prev,
      selectedFiles,
    }));
  };

  /**
   * Handle execute action from ActionsPanel
   */
  const handleExecuteAction = async (
    operations: MoveOperation[],
    destination: string | undefined,
    action: 'move' | 'delete'
  ) => {
    if (!appState.currentScan.scanId) {
      setAppState((prev) => ({
        ...prev,
        error: 'No scan ID available',
      }));
      return;
    }

    setAppState((prev) => ({
      ...prev,
      operationInProgress: true,
      error: null,
    }));

    const result = await apiClient.moveDuplicates(
      appState.currentScan.scanId,
      operations,
      destination || ''
    );

    if ('error' in result) {
      const apiError = result as ApiError;
      setAppState((prev) => ({
        ...prev,
        operationInProgress: false,
        error: apiError.error,
      }));
      return;
    }

    // Success
    setAppState((prev) => ({
      ...prev,
      operationInProgress: false,
      selectedFiles: [],
      error: null,
    }));

    // Show success message
    const message =
      action === 'move'
        ? `Successfully moved ${result.moved_count} file${result.moved_count !== 1 ? 's' : ''}`
        : `Successfully deleted ${result.moved_count} file${result.moved_count !== 1 ? 's' : ''}`;

    if (result.failed_count > 0) {
      setAppState((prev) => ({
        ...prev,
        error: `${message}, but ${result.failed_count} file${result.failed_count !== 1 ? 's' : ''} failed`,
      }));
    }
  };

  /**
   * Reset to initial state
   */
  const handleStartOver = () => {
    setAppState({
      currentScan: {
        scanId: null,
        imageCount: null,
      },
      duplicateGroups: [],
      selectedFiles: [],
      isLoading: false,
      error: null,
      operationInProgress: false,
    });
  };

  return (
    <div className="App">
      <header className="header">
        <h1>Duplicate Photos Finder</h1>
        <p className="header-status">
          Backend Status:{' '}
          <span className={isHealthy ? 'status-healthy' : 'status-unhealthy'}>
            {isHealthy ? '✓ Connected' : '⚠ Disconnected'}
          </span>
        </p>
      </header>

      <main className="main-content">
        <div className="container">
          {/* Step 1: Directory Selection */}
          <section className="workflow-section">
            <div className="section-badge">Step 1</div>
            <h2>Select Directory</h2>
            <div className="component-container">
              <DirectoryPicker onScanComplete={handleScanComplete} />
            </div>
          </section>

          {/* Step 2: Duplicates Review */}
          {appState.currentScan.scanId && (
            <section className="workflow-section">
              <div className="section-badge">Step 2</div>
              <h2>Review Duplicates</h2>
              {appState.error && (
                <div className="app-error-message" role="alert">
                  <span className="error-icon">✗</span>
                  <span>{appState.error}</span>
                </div>
              )}
              <div className="component-container">
                <DuplicatesList
                  groups={appState.duplicateGroups}
                  isLoading={appState.isLoading}
                  onSelectionChange={handleSelectionChange}
                />
              </div>
            </section>
          )}

          {/* Step 3: Execute Actions */}
          {appState.duplicateGroups.length > 0 && (
            <section className="workflow-section">
              <div className="section-badge">Step 3</div>
              <h2>Execute Actions</h2>
              <div className="component-container">
                <ActionsPanel
                  selectedCount={appState.selectedFiles.length}
                  selections={appState.selectedFiles}
                  isExecuting={appState.operationInProgress}
                  onExecute={handleExecuteAction}
                  onClearSelection={() =>
                    setAppState((prev) => ({
                      ...prev,
                      selectedFiles: [],
                    }))
                  }
                />
              </div>
            </section>
          )}

          {/* Start Over Button */}
          {appState.currentScan.scanId && (
            <section className="workflow-section start-over-section">
              <button
                onClick={handleStartOver}
                className="start-over-button"
                aria-label="Start a new scan"
              >
                ← Start Over
              </button>
            </section>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>Duplicate Photos Finder - Phase 4 | Version 0.1.0</p>
      </footer>
    </div>
  );
};

export default App;
