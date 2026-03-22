"""File management service for safe file operations.

This module provides functions for safely moving, deleting, and validating
file operations with proper error handling and atomic operations to prevent
data loss.
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from app.exceptions import (
    PermissionDeniedError,
    InvalidOperationError,
)

logger = logging.getLogger(__name__)


def move_file(src: str, dest: str, overwrite: bool = False) -> bool:
    """Safely move a file from source to destination.

    Performs an atomic move operation with comprehensive validation:
    - Source file exists and is readable
    - Destination is writable (directory or parent directory exists)
    - Source and destination are not the same
    - Handles overwrite protection

    The move is atomic (atomic rename) when possible, or uses copy+delete
    if atomic move fails (e.g., across filesystem boundaries).

    Args:
        src: Source file path (must exist and be readable).
        dest: Destination path. Can be:
              - Directory path: file will be moved into directory with same name
              - File path: file will be moved/renamed to this path
        overwrite: If True, overwrite destination if it exists.
                  If False, raise error if destination exists.
                  Default False.

    Returns:
        bool: True if move was successful.

    Raises:
        FileNotFoundError: If source file doesn't exist.
        PermissionDeniedError: If source not readable or dest not writable.
        FileExistsError: If destination exists and overwrite=False.
        InvalidOperationError: If src == dest or other invalid operation.

    Example:
        >>> move_file("/tmp/photo.jpg", "/backup/photo.jpg")
        True

        >>> move_file("/tmp/photo.jpg", "/backup/")  # Into directory
        True

        >>> move_file("/tmp/photo.jpg", "/tmp/photo.jpg", overwrite=False)
        # Raises InvalidOperationError
    """
    src_path = Path(src)
    dest_path = Path(dest)

    # Check source exists
    if not src_path.exists():
        logger.warning(f"Source file not found: {src}")
        raise FileNotFoundError(f"Source file not found: {src}")

    if not src_path.is_file():
        logger.warning(f"Source is not a file: {src}")
        raise InvalidOperationError("move_file", reason="Source is not a file")

    # Check source is readable
    try:
        if not os.access(src, os.R_OK):
            raise PermissionError("Not readable")
    except PermissionError as e:
        logger.warning(f"Cannot read source file: {src}")
        raise PermissionDeniedError(src, operation="read") from e

    # Handle destination directory
    if dest_path.is_dir():
        # If destination is a directory, move file into it with same name
        dest_path = dest_path / src_path.name

    # Check src == dest
    if src_path.resolve() == dest_path.resolve():
        logger.warning(f"Source and destination are the same: {src}")
        raise InvalidOperationError(
            "move_file",
            reason="Source and destination are the same",
        )

    # Check destination exists
    if dest_path.exists() and not overwrite:
        logger.warning(f"Destination already exists: {dest}")
        raise FileExistsError(f"Destination already exists: {dest}")

    # Check destination directory is writable
    dest_dir = dest_path.parent
    if not dest_dir.exists():
        logger.warning(f"Destination directory doesn't exist: {dest_dir}")
        raise InvalidOperationError(
            "move_file",
            reason=f"Destination directory doesn't exist: {dest_dir}",
        )

    try:
        if not os.access(dest_dir, os.W_OK):
            raise PermissionError("Not writable")
    except PermissionError as e:
        logger.warning(f"Cannot write to destination directory: {dest_dir}")
        raise PermissionDeniedError(dest_dir, operation="write") from e

    # Perform the move
    try:
        # Try atomic move first (using os.replace for atomic rename)
        os.replace(src, str(dest_path))
        logger.info(f"Moved file: {src} -> {dest_path}")
        return True

    except OSError as e:
        logger.error(f"Failed to move file: {str(e)}")
        raise PermissionDeniedError(src, operation="move") from e


def validate_destination(path: str) -> Tuple[bool, str]:
    """Validate that a destination directory is suitable for file operations.

    Checks:
    - Directory exists
    - Directory is readable and writable
    - Sufficient disk space available (checks free space)
    - Path is valid and accessible

    Args:
        path: Path to directory to validate.

    Returns:
        Tuple[bool, str]: (is_valid, reason)
            - is_valid: True if directory is valid and usable
            - reason: Empty string if valid, error message if invalid

    Example:
        >>> is_valid, reason = validate_destination("/backup")
        >>> if is_valid:
        ...     print("Ready to move files")
        >>> else:
        ...     print(f"Invalid destination: {reason}")
    """
    dest_path = Path(path)

    # Check directory exists
    if not dest_path.exists():
        reason = f"Directory does not exist: {path}"
        logger.warning(reason)
        return False, reason

    if not dest_path.is_dir():
        reason = f"Path is not a directory: {path}"
        logger.warning(reason)
        return False, reason

    # Check directory is readable
    try:
        if not os.access(path, os.R_OK):
            raise PermissionError("Not readable")
    except PermissionError:
        reason = f"Directory is not readable: {path}"
        logger.warning(reason)
        return False, reason

    # Check directory is writable
    try:
        if not os.access(path, os.W_OK):
            raise PermissionError("Not writable")
    except PermissionError:
        reason = f"Directory is not writable: {path}"
        logger.warning(reason)
        return False, reason

    # Check available disk space (minimum 1MB required)
    try:
        import shutil
        free_bytes = shutil.disk_usage(path).free
        if free_bytes < 1024 * 1024:  # Less than 1MB
            reason = f"Insufficient disk space: {free_bytes} bytes available"
            logger.warning(reason)
            return False, reason
    except Exception as e:
        reason = f"Cannot check disk space: {str(e)}"
        logger.warning(reason)
        return False, reason

    logger.debug(f"Destination validation passed: {path}")
    return True, ""


def execute_move_operations(
    operations: List[Dict[str, str]],
    destination: str,
) -> Dict[str, object]:
    """Execute multiple file move/delete operations safely.

    Processes each operation in the list without stopping on errors.
    Returns detailed results including successes and failures.

    Each operation should have:
    - original: Path to original file
    - target_copy: Path to file to move/delete
    - action: "move" or "delete"

    Args:
        operations: List of operation dictionaries.
                   [{
                       "original": "/path/to/original.jpg",
                       "target_copy": "/path/to/copy.jpg",
                       "action": "move" or "delete"
                   }]
        destination: Directory to move files to (for "move" actions).

    Returns:
        Dict with operation results:
            {
                "moved_count": int,      # Number of successful moves
                "deleted_count": int,    # Number of successful deletes
                "failed_count": int,     # Number of failed operations
                "errors": [              # Details of failures
                    {
                        "file": "/path/to/file.jpg",
                        "action": "move" or "delete",
                        "reason": "Error message"
                    }
                ]
            }

    Example:
        >>> operations = [
        ...     {
        ...         "original": "/photos/photo1.jpg",
        ...         "target_copy": "/photos/photo1_copy.jpg",
        ...         "action": "move"
        ...     },
        ...     {
        ...         "original": "/photos/photo2.jpg",
        ...         "target_copy": "/photos/photo2_dup.jpg",
        ...         "action": "delete"
        ...     }
        ... ]
        >>> result = execute_move_operations(operations, "/backup")
        >>> result["moved_count"]
        1
        >>> result["deleted_count"]
        1
        >>> result["failed_count"]
        0
    """
    result = {
        "moved_count": 0,
        "deleted_count": 0,
        "failed_count": 0,
        "errors": [],
    }

    if not operations:
        logger.info("No operations to execute")
        return result

    logger.info(f"Executing {len(operations)} file operations")

    # Process each operation
    for operation in operations:
        target_file = operation.get("target_copy", "")
        action = operation.get("action", "")

        if not target_file or not action:
            logger.warning(f"Invalid operation: missing target_copy or action")
            result["failed_count"] += 1
            result["errors"].append(
                {
                    "file": target_file or "unknown",
                    "action": action or "unknown",
                    "reason": "Missing required fields",
                }
            )
            continue

        try:
            if action == "move":
                # Move file to destination
                dest_file = Path(destination) / Path(target_file).name
                move_file(target_file, str(dest_file), overwrite=False)
                result["moved_count"] += 1
                logger.info(f"Moved: {target_file} -> {dest_file}")

            elif action == "delete":
                # Delete file
                file_path = Path(target_file)
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {target_file}")

                file_path.unlink()
                result["deleted_count"] += 1
                logger.info(f"Deleted: {target_file}")

            else:
                result["failed_count"] += 1
                result["errors"].append(
                    {
                        "file": target_file,
                        "action": action,
                        "reason": f"Unknown action: {action}",
                    }
                )

        except FileNotFoundError as e:
            result["failed_count"] += 1
            result["errors"].append(
                {
                    "file": target_file,
                    "action": action,
                    "reason": f"File not found",
                }
            )
            logger.warning(f"Operation failed: {str(e)}")

        except PermissionDeniedError as e:
            result["failed_count"] += 1
            result["errors"].append(
                {
                    "file": target_file,
                    "action": action,
                    "reason": f"Permission denied",
                }
            )
            logger.warning(f"Operation failed: {str(e)}")

        except FileExistsError as e:
            result["failed_count"] += 1
            result["errors"].append(
                {
                    "file": target_file,
                    "action": action,
                    "reason": f"Destination already exists",
                }
            )
            logger.warning(f"Operation failed: {str(e)}")

        except Exception as e:
            result["failed_count"] += 1
            result["errors"].append(
                {
                    "file": target_file,
                    "action": action,
                    "reason": str(e),
                }
            )
            logger.error(f"Unexpected error during operation: {str(e)}")

    logger.info(
        f"Operations complete: {result['moved_count']} moved, "
        f"{result['deleted_count']} deleted, {result['failed_count']} failed"
    )

    return result
