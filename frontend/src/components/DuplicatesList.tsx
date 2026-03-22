import React, { useCallback, useState } from 'react';
import { DuplicateGroup } from '../services/api';
import './DuplicatesList.css';

interface DuplicatesListProps {
  groups: DuplicateGroup[];
  isLoading?: boolean;
  onSelectionChange?: (selectedFiles: string[]) => void;
}

/**
 * DuplicatesList Component
 * Renders a list of duplicate groups and allows selecting copies.
 */
const DuplicatesList: React.FC<DuplicatesListProps> = ({
  groups,
  isLoading = false,
  onSelectionChange,
}) => {
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());

  const truncatePath = (path: string): string => {
    const maxLength = 60;
    if (path.length > maxLength) {
      const start = path.substring(0, 20);
      const end = path.substring(path.length - 30);
      return `${start}...${end}`;
    }
    return path;
  };

  const getFileName = (path: string): string => {
    return path.split('/').pop() || path;
  };

  const allCopies = groups.flatMap((g) => g.copies);

  const handleFileSelect = useCallback(
    (filePath: string) => {
      const newSelected = new Set(selectedFiles);
      if (newSelected.has(filePath)) {
        newSelected.delete(filePath);
      } else {
        newSelected.add(filePath);
      }
      setSelectedFiles(newSelected);
      onSelectionChange?.(Array.from(newSelected));
    },
    [selectedFiles, onSelectionChange]
  );

  const handleSelectAll = useCallback(() => {
    if (selectedFiles.size === allCopies.length) {
      setSelectedFiles(new Set());
      onSelectionChange?.([]);
    } else {
      const newSelected = new Set(allCopies);
      setSelectedFiles(newSelected);
      onSelectionChange?.(Array.from(newSelected));
    }
  }, [allCopies, selectedFiles, onSelectionChange]);

  const handleGroupToggle = useCallback(
    (groupCopies: string[]) => {
      const newSelected = new Set(selectedFiles);

      // If all group copies are selected, remove them; otherwise add them
      const allSelected = groupCopies.every((c) => newSelected.has(c));
      if (allSelected) {
        for (const c of groupCopies) newSelected.delete(c);
      } else {
        for (const c of groupCopies) newSelected.add(c);
      }

      setSelectedFiles(newSelected);
      onSelectionChange?.(Array.from(newSelected));
    },
    [selectedFiles, onSelectionChange]
  );

  if (isLoading) {
    return (
      <div className="duplicates-list loading">
        <div className="loading-spinner" aria-hidden="true" />
        <p>Loading duplicates...</p>
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="duplicates-list empty" role="status">
        <p className="empty-message">No duplicates found.</p>
        <p className="empty-hint">Scan a directory to find duplicate images.</p>
      </div>
    );
  }

  const isAllSelected = selectedFiles.size === allCopies.length && allCopies.length > 0;
  const isPartiallySelected = selectedFiles.size > 0 && selectedFiles.size < allCopies.length;

  return (
    <div className="duplicates-list">
      <div className="list-header">
        <div className="selection-info">
          <h2>Duplicate Groups</h2>
          <p className="selection-counter" role="status" aria-live="polite">
            {selectedFiles.size} file{selectedFiles.size !== 1 ? 's' : ''} selected
          </p>
        </div>

        {groups.length > 0 && (
          <div className="select-all-wrapper">
            <label htmlFor="select-all-checkbox" className="select-all-label">
              <input
                id="select-all-checkbox"
                type="checkbox"
                checked={isAllSelected}
                ref={(el) => {
                  if (el) {
                    el.indeterminate = isPartiallySelected;
                  }
                }}
                onChange={handleSelectAll}
                aria-label="Select all duplicate copies"
              />
              Select All
            </label>
          </div>
        )}
      </div>

      <div className="groups-container">
        {groups.map((group, groupIndex) => {
          const groupCopies = group.copies;
          const groupSelectedCount = groupCopies.filter((c) => selectedFiles.has(c)).length;
          const groupAllSelected = groupSelectedCount === groupCopies.length && groupCopies.length > 0;
          const groupPartially = groupSelectedCount > 0 && groupSelectedCount < groupCopies.length;

          return (
            <div key={`${group.hash}-${groupIndex}`} className="duplicate-group-card">
              <div className="group-header">
                <div className="group-title">
                  <h3>Duplicate Group {groupIndex + 1}</h3>
                  <span className="group-hash" title={group.hash}>
                    {group.hash.substring(0, 12)}...
                  </span>
                </div>

                <div className="copies-count">
                  <label className="group-select-label">
                    <input
                      type="checkbox"
                      checked={groupAllSelected}
                      ref={(el) => {
                        if (el) el.indeterminate = groupPartially;
                      }}
                      onChange={() => handleGroupToggle(groupCopies)}
                      aria-label={`Select copies for group ${groupIndex + 1}`}
                    />
                    {group.copies.length} duplicate{group.copies.length !== 1 ? 's' : ''}
                  </label>
                </div>
              </div>

              <div className="group-content">
                <div className="original-file-section">
                  <h4 className="section-title">Original File</h4>
                  <div className="file-path" title={group.original}>
                    <span className="file-icon" aria-hidden="true">📄</span>
                    <span className="path-text">{truncatePath(group.original)}</span>
                  </div>
                  <p className="file-name">{getFileName(group.original)}</p>
                </div>

                <div className="copies-section">
                  <h4 className="section-title">Duplicate Copies</h4>
                  <ul className="copies-list" role="list">
                    {group.copies.map((copy, copyIndex) => (
                      <li key={`${copy}-${copyIndex}`} className="copy-item">
                        <label className="copy-label">
                          <input
                            type="checkbox"
                            checked={selectedFiles.has(copy)}
                            onChange={() => handleFileSelect(copy)}
                            aria-label={`Select ${getFileName(copy)}`}
                          />
                          <span className="checkbox-visual" />
                          <span className="copy-info">
                            <span className="file-icon" aria-hidden="true">📄</span>
                            <span className="path-text" title={copy}>{truncatePath(copy)}</span>
                          </span>
                        </label>
                        <p className="file-name">{getFileName(copy)}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DuplicatesList;
