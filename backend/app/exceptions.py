"""Custom exception classes for the application."""


class DuplicatePhotosError(Exception):
    """Base exception class for all custom exceptions."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: str = None,
    ):
        """Initialize the exception.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code.
            details: Optional additional details about the error.
        """
        self.message = message
        self.code = code
        self.details = details
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response.

        Returns:
            dict: Dictionary representation of the exception.
        """
        result = {"error": self.message, "code": self.code}
        if self.details:
            result["details"] = self.details
        return result


class DirectoryNotFoundError(DuplicatePhotosError):
    """Raised when a specified directory does not exist."""

    def __init__(self, directory: str, details: str = None):
        """Initialize the exception.

        Args:
            directory: Path to the missing directory.
            details: Optional additional details.
        """
        message = f"Directory not found: {directory}"
        super().__init__(message, "DIRECTORY_NOT_FOUND", details)


class InvalidImageError(DuplicatePhotosError):
    """Raised when an image file is invalid or unsupported."""

    def __init__(self, filename: str, reason: str = None, details: str = None):
        """Initialize the exception.

        Args:
            filename: Name of the invalid image file.
            reason: Reason why the image is invalid.
            details: Optional additional details.
        """
        message = f"Invalid image: {filename}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "INVALID_IMAGE", details)


class PermissionDeniedError(DuplicatePhotosError):
    """Raised when permission is denied for a file operation."""

    def __init__(self, path: str, operation: str = None, details: str = None):
        """Initialize the exception.

        Args:
            path: Path to the resource.
            operation: Type of operation that was denied.
            details: Optional additional details.
        """
        message = f"Permission denied: {path}"
        if operation:
            message += f" ({operation})"
        super().__init__(message, "PERMISSION_DENIED", details)


class ScanNotFoundError(DuplicatePhotosError):
    """Raised when a scan with the specified ID is not found."""

    def __init__(self, scan_id: str, details: str = None):
        """Initialize the exception.

        Args:
            scan_id: ID of the missing scan.
            details: Optional additional details.
        """
        message = f"Scan not found: {scan_id}"
        super().__init__(message, "SCAN_NOT_FOUND", details)


class InvalidOperationError(DuplicatePhotosError):
    """Raised when an operation is invalid or cannot be performed."""

    def __init__(self, operation: str, reason: str = None, details: str = None):
        """Initialize the exception.

        Args:
            operation: Name of the operation.
            reason: Reason why the operation is invalid.
            details: Optional additional details.
        """
        message = f"Invalid operation: {operation}"
        if reason:
            message += f" ({reason})"
        super().__init__(message, "INVALID_OPERATION", details)
