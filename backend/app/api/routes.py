"""API routes for duplicate photos finder."""

import logging
from typing import Dict, Any
from uuid import uuid4

from flask import Blueprint, request, jsonify

from app.utils.validators import validate_directory_path, validate_scan_id
from app.services.image_processor import batch_compute_hashes
from app.services.duplicate_finder import find_duplicates, validate_groups
from app.services.file_manager import validate_destination, execute_move_operations
from app.exceptions import (
    DuplicatePhotosError,
    DirectoryNotFoundError,
    PermissionDeniedError,
)

# Create blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")

# Set up logging
logger = logging.getLogger(__name__)

# In-memory storage for scans
_scans_store: Dict[str, Dict[str, Any]] = {}


@api_bp.route("/health", methods=["GET"])
def health_check() -> tuple:
    """Check API health status.

    Returns:
        tuple: JSON response with status and HTTP status code.

    Example:
        GET /api/health
        Response: {"status": "ok"} (200)
    """
    logger.debug("Health check endpoint called")
    return jsonify({"status": "ok"}), 200


@api_bp.route("/scan", methods=["POST"])
def start_scan() -> tuple:
    """Start a new directory scan for duplicate images.

    Request JSON:
        {
            "directory": string - Path to directory to scan
        }

    Returns:
        tuple: JSON response with scan_id and image_count, HTTP status code.

    Raises:
        DirectoryNotFoundError: If directory doesn't exist or isn't readable.

    Example:
        POST /api/scan
        Request: {"directory": "/path/to/photos"}
        Response: {"scan_id": "scan-123", "image_count": 42} (200)
        Error: {"error": "...", "code": "DIRECTORY_NOT_FOUND"} (400)
    """
    try:
        # Validate request JSON
        try:
            data = request.get_json()
        except Exception:
            logger.warning("POST /scan: Invalid JSON in request body")
            return (
                jsonify(
                    {
                        "error": "Request body must be valid JSON",
                        "code": "INVALID_REQUEST",
                    }
                ),
                400,
            )

        if not data:
            logger.warning("POST /scan: Missing JSON body")
            return (
                jsonify(
                    {
                        "error": "Request body must be valid JSON",
                        "code": "INVALID_REQUEST",
                    }
                ),
                400,
            )

        # Get and validate directory parameter
        directory = data.get("directory")
        if not directory:
            logger.warning("POST /scan: Missing directory parameter")
            return (
                jsonify(
                    {
                        "error": "Missing required field: directory",
                        "code": "MISSING_FIELD",
                    }
                ),
                400,
            )

        validate_directory_path(directory)

        # Compute hashes for all images in directory
        logger.info(f"Starting scan for directory: {directory}")
        hashes = batch_compute_hashes(directory, recursive=False)

        # Find duplicate groups
        groups = find_duplicates(hashes)

        # Validate groups
        if not validate_groups(groups):
            logger.error("Invalid groups produced by duplicate finder")
            return (
                jsonify(
                    {
                        "error": "Internal server error: Invalid duplicate groups",
                        "code": "INTERNAL_ERROR",
                    }
                ),
                500,
            )

        # Generate scan ID
        scan_id = f"scan-{uuid4().hex[:12]}"

        # Store scan results
        scan_data = {
            "scan_id": scan_id,
            "directory": directory,
            "image_count": len(hashes),
            "groups": groups,
        }

        _scans_store[scan_id] = scan_data
        logger.info(
            f"Scan complete: {scan_id} - {len(hashes)} images, " f"{len(groups)} duplicate groups"
        )

        return (
            jsonify({"scan_id": scan_id, "image_count": len(hashes)}),
            200,
        )

    except DirectoryNotFoundError as e:
        logger.warning(f"POST /scan: Directory not found: {str(e)}")
        return (
            jsonify(e.to_dict()),
            404,
        )
    except PermissionDeniedError as e:
        logger.warning(f"POST /scan: Permission denied: {str(e)}")
        return (
            jsonify(e.to_dict()),
            403,
        )
    except ValueError as e:
        logger.warning(f"POST /scan: Validation error: {str(e)}")
        return (
            jsonify({"error": str(e), "code": "INVALID_REQUEST"}),
            400,
        )
    except DuplicatePhotosError as e:
        logger.warning(f"POST /scan: Application error: {str(e)}")
        return (
            jsonify(e.to_dict()),
            400,
        )
    except Exception as e:
        logger.error(f"POST /scan: Unexpected error: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "details": str(e),
                }
            ),
            500,
        )


@api_bp.route("/duplicates/<scan_id>", methods=["GET"])
def get_duplicates(scan_id: str) -> tuple:
    """Get duplicate image groups for a scan.

    Args:
        scan_id: ID of the scan to retrieve results for.

    Returns:
        tuple: JSON response with groups and HTTP status code.

    Raises:
        ScanNotFoundError: If scan_id doesn't exist.

    Example:
        GET /api/duplicates/scan-123
        Response: {
            "groups": [
                {
                    "hash": "abc123",
                    "original": "photo1.jpg",
                    "copies": ["photo1_copy.jpg"]
                }
            ]
        } (200)
        Error: {"error": "...", "code": "SCAN_NOT_FOUND"} (404)
    """
    try:
        validate_scan_id(scan_id)

        if scan_id not in _scans_store:
            logger.warning(f"GET /duplicates: Scan not found: {scan_id}")
            return (
                jsonify(
                    {
                        "error": f"Scan not found: {scan_id}",
                        "code": "SCAN_NOT_FOUND",
                    }
                ),
                404,
            )

        scan_data = _scans_store[scan_id]
        logger.info(f"Retrieved duplicates for scan: {scan_id}")

        return jsonify({"groups": scan_data["groups"]}), 200

    except ValueError as e:
        logger.warning(f"GET /duplicates: Validation error: {str(e)}")
        return (
            jsonify({"error": str(e), "code": "INVALID_REQUEST"}),
            400,
        )
    except Exception as e:
        logger.error(f"GET /duplicates: Unexpected error: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "details": str(e),
                }
            ),
            500,
        )



@api_bp.route("/preview", methods=["GET"])
def preview_image() -> tuple:
    """Return a resized thumbnail preview for an image.

    Query params:
        path: URL-encoded absolute path or path relative to a previously scanned directory

    Security:
        - Absolute paths are allowed only if they are under one of the scan
          directories previously registered by /api/scan (stored in _scans_store).
        - Relative paths are resolved against scan directories when possible.
        - Otherwise returns 403 Forbidden.

    Returns:
        Raw JPEG bytes with Content-Type: image/jpeg on success.
    """
    try:
        from urllib.parse import unquote_plus
        from pathlib import Path
        from flask import Response
        from app.services.image_processor import generate_thumbnail

        raw_path = request.args.get("path")
        if not raw_path:
            return (jsonify({"error": "Missing required query parameter: path", "code": "MISSING_FIELD"}), 400)

        decoded = unquote_plus(raw_path)
        candidate = Path(decoded)

        # Determine allowed scan directories
        allowed_dirs = [d["directory"] for d in _scans_store.values() if d.get("directory")]

        resolved_path = None
        if candidate.is_absolute():
            # Absolute paths: only allow if under any scan directory
            for d in allowed_dirs:
                try:
                    if Path(decoded).resolve().is_relative_to(Path(d).resolve()):
                        resolved_path = Path(decoded).resolve()
                        break
                except Exception:
                    # Fallback for python <3.9 without is_relative_to
                    try:
                        resolved_path = Path(decoded).resolve()
                        if str(resolved_path).startswith(str(Path(d).resolve())):
                            break
                        resolved_path = None
                    except Exception:
                        resolved_path = None
            if resolved_path is None:
                return (jsonify({"error": "Path not allowed", "code": "FORBIDDEN"}), 403)
        else:
            # Relative path: try to find under any allowed_dir
            found = False
            for d in allowed_dirs:
                cand = Path(d) / decoded
                if cand.exists():
                    resolved_path = cand.resolve()
                    found = True
                    break
            if not found:
                return (jsonify({"error": "Path not allowed or not found", "code": "FORBIDDEN"}), 403)

        # Generate thumbnail bytes
        thumb_bytes = generate_thumbnail(str(resolved_path), max_width=300)
        return Response(thumb_bytes, mimetype="image/jpeg")

    except FileNotFoundError:
        return (jsonify({"error": "File not found", "code": "NOT_FOUND"}), 404)
    except PermissionDeniedError as e:
        return (jsonify(e.to_dict()), 403)
    except Exception as e:
        logger.exception("/api/preview: Unexpected error")
        return (jsonify({"error": "Internal server error", "code": "INTERNAL_ERROR", "details": str(e)}), 500)


@api_bp.route("/move-duplicates", methods=["POST"])
def move_duplicates() -> tuple:
    """Execute move/delete operations on duplicate files.

    Request JSON:
        {
            "scan_id": string,
            "destination": string,
            "operations": [
                {
                    "original": string,
                    "target_copy": string,
                    "action": "move" | "delete"
                }
            ]
        }

    Returns:
        tuple: JSON response with operation results, HTTP status code.

    Example:
        POST /api/move-duplicates
        Request: {
            "scan_id": "scan-123",
            "destination": "/archive",
            "operations": [
                {"original": "photo1.jpg", "target_copy": "photo1_copy.jpg",
                 "action": "move"}
            ]
        }
        Response: {
            "moved_count": 1,
            "deleted_count": 0,
            "failed_count": 0,
            "errors": []
        } (200)
    """
    try:
        try:
            data = request.get_json()
        except Exception:
            logger.warning("POST /move-duplicates: Invalid JSON in request body")
            return (
                jsonify(
                    {
                        "error": "Request body must be valid JSON",
                        "code": "INVALID_REQUEST",
                    }
                ),
                400,
            )

        if not data:
            logger.warning("POST /move-duplicates: Missing JSON body")
            return (
                jsonify(
                    {
                        "error": "Request body must be valid JSON",
                        "code": "INVALID_REQUEST",
                    }
                ),
                400,
            )

        # Validate required fields
        scan_id = data.get("scan_id")
        destination = data.get("destination")
        operations = data.get("operations")

        if not scan_id:
            return (
                jsonify(
                    {
                        "error": "Missing required field: scan_id",
                        "code": "MISSING_FIELD",
                    }
                ),
                400,
            )

        if not destination:
            return (
                jsonify(
                    {
                        "error": "Missing required field: destination",
                        "code": "MISSING_FIELD",
                    }
                ),
                400,
            )

        if not operations or not isinstance(operations, list):
            return (
                jsonify(
                    {
                        "error": "Missing required field: operations (must be list)",
                        "code": "MISSING_FIELD",
                    }
                ),
                400,
            )

        validate_scan_id(scan_id)

        # Validate operations format
        for op in operations:
            if not isinstance(op, dict):
                return (
                    jsonify(
                        {
                            "error": "Each operation must be an object",
                            "code": "INVALID_REQUEST",
                        }
                    ),
                    400,
                )

            required_fields = {"original", "target_copy", "action"}
            if not all(field in op for field in required_fields):
                return (
                    jsonify(
                        {
                            "error": ("Each operation must have: " "original, target_copy, action"),
                            "code": "INVALID_REQUEST",
                        }
                    ),
                    400,
                )

            if op["action"] not in {"move", "delete"}:
                return (
                    jsonify(
                        {
                            "error": 'Action must be "move" or "delete"',
                            "code": "INVALID_REQUEST",
                        }
                    ),
                    400,
                )

        # Validate destination before executing operations
        is_valid, reason = validate_destination(destination)
        if not is_valid:
            logger.warning(f"POST /move-duplicates: Invalid destination: {reason}")
            return (
                jsonify(
                    {
                        "error": f"Invalid destination: {reason}",
                        "code": "INVALID_REQUEST",
                    }
                ),
                400,
            )

        # Execute operations
        logger.info(f"Processing {len(operations)} file operations for scan {scan_id}")
        result = execute_move_operations(operations, destination)

        return jsonify(result), 200

    except ValueError as e:
        logger.warning(f"POST /move-duplicates: Validation error: {str(e)}")
        return (
            jsonify({"error": str(e), "code": "INVALID_REQUEST"}),
            400,
        )
    except Exception as e:
        logger.error(f"POST /move-duplicates: Unexpected error: {str(e)}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "details": str(e),
                }
            ),
            500,
        )
