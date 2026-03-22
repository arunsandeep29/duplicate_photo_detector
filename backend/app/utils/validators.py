"""Input validation utilities."""

import os
from typing import Optional


def validate_directory_path(directory: str) -> bool:
    """Validate that a directory exists and is readable.

    Args:
        directory: Path to the directory to validate.

    Returns:
        bool: True if directory exists and is readable.

    Raises:
        ValueError: If directory doesn't exist or is not readable.
    """
    if not directory or not isinstance(directory, str):
        raise ValueError("Directory path must be a non-empty string")

    if not os.path.exists(directory):
        raise ValueError(f"Directory does not exist: {directory}")

    if not os.path.isdir(directory):
        raise ValueError(f"Path is not a directory: {directory}")

    if not os.access(directory, os.R_OK):
        raise ValueError(f"Directory is not readable: {directory}")

    return True


def validate_scan_id(scan_id: str) -> bool:
    """Validate the format of a scan ID.

    Args:
        scan_id: Scan ID to validate.

    Returns:
        bool: True if scan ID is valid.

    Raises:
        ValueError: If scan ID format is invalid.
    """
    if not scan_id or not isinstance(scan_id, str):
        raise ValueError("Scan ID must be a non-empty string")

    # Scan ID should be alphanumeric and hyphens only
    if not all(c.isalnum() or c == "-" for c in scan_id):
        raise ValueError("Scan ID must contain only alphanumeric characters and hyphens")

    return True


def validate_image_format(filename: str, mime_type: Optional[str] = None) -> bool:
    """Validate that a file is a supported image format.

    Args:
        filename: Name of the image file.
        mime_type: Optional MIME type of the file.

    Returns:
        bool: True if image format is valid.

    Raises:
        ValueError: If image format is not supported.
    """
    if not filename or not isinstance(filename, str):
        raise ValueError("Filename must be a non-empty string")

    # Check by extension
    _, ext = os.path.splitext(filename.lower())
    ext = ext.lstrip(".")

    allowed_extensions = {"jpg", "jpeg", "png", "gif", "webp"}

    if not ext:
        raise ValueError("File has no extension")

    if ext not in allowed_extensions:
        raise ValueError(f"Unsupported image format: {ext}")

    # If MIME type is provided, validate it as well
    if mime_type:
        allowed_mimes = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
        }
        if mime_type not in allowed_mimes:
            raise ValueError(f"Unsupported MIME type: {mime_type}")

    return True
