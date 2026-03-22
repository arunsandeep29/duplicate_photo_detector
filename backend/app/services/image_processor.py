"""Image processing module for computing perceptual hashes of JPEG images.

This module provides functions to load images, compute perceptual hashes
(content-based fingerprints), compare hashes for similarity, and batch
process directories of images.

The perceptual hash algorithm is designed to be robust to minor changes
like compression, resizing, or metadata alterations while still reliably
detecting duplicate or near-duplicate images.
"""

import logging
from pathlib import Path
from typing import Dict, Tuple
import mimetypes

import imagehash
from PIL import Image

from app.exceptions import (
    InvalidImageError,
    DirectoryNotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)


def load_image(file_path: str) -> Image.Image:
    """Load and validate a JPEG image from file.

    This function opens a JPEG image file, validates it, and returns
    a PIL Image object. It performs comprehensive validation including:
    - File existence
    - MIME type verification (image/jpeg)
    - File readability
    - Image integrity (can be opened and has valid format)

    Args:
        file_path: Absolute path to JPEG file to load.

    Returns:
        PIL.Image.Image: Opened image object ready for processing.

    Raises:
        FileNotFoundError: If file does not exist at the given path.
        InvalidImageError: If file is not a valid JPEG, is corrupted,
                          or cannot be read as an image.
        PermissionDeniedError: If file exists but is not readable
                              due to permission restrictions.

    Example:
        >>> image = load_image("/path/to/photo.jpg")
        >>> image.format
        'JPEG'
        >>> image.size
        (1920, 1080)
    """
    path = Path(file_path)

    # Check file existence
    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check readability
    if not path.is_file():
        logger.warning(f"Path is not a file: {file_path}")
        raise InvalidImageError(
            path.name,
            reason="Path is not a file",
        )

    try:
        # Check file is readable
        if not path.stat().st_size:
            logger.warning(f"File is empty: {file_path}")
            raise InvalidImageError(path.name, reason="File is empty")
    except PermissionError as e:
        logger.warning(f"Permission denied reading file: {file_path}")
        raise PermissionDeniedError(file_path, operation="read") from e

    # Validate MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type not in ("image/jpeg", None):  # None in case of unknown
        # Still try to load, but log warning
        logger.warning(f"Unexpected MIME type {mime_type} for {file_path}")

    # Load and validate image
    try:
        image = Image.open(file_path)
        # Verify it's actually a valid image by accessing basic properties
        _ = image.size
        _ = image.mode
        # For JPEG, verify format (will raise if corrupted)
        if image.format and image.format.upper() != "JPEG":
            logger.warning(f"File is {image.format}, not JPEG: {file_path}")
            raise InvalidImageError(
                path.name,
                reason=f"File is {image.format}, not JPEG",
            )
        # Force load of image data to detect corrupted images
        image.load()
        logger.debug(f"Successfully loaded image: {file_path}")
        return image

    except FileNotFoundError as e:
        logger.warning(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}") from e
    except PermissionError as e:
        logger.warning(f"Permission denied: {file_path}")
        raise PermissionDeniedError(file_path, operation="read") from e
    except (Image.UnidentifiedImageError, IOError, OSError) as e:
        logger.warning(f"Invalid or corrupted image: {file_path}: {str(e)}")
        raise InvalidImageError(
            path.name,
            reason="File is corrupted or not a valid image",
            details=str(e),
        ) from e


def compute_hash(image: Image.Image, algorithm: str = "phash") -> str:
    """Compute perceptual hash of an image.

    Computes a content-based hash of the image that is robust to minor
    changes like compression, resizing, or metadata alterations. This is
    useful for identifying duplicate or near-duplicate images.

    The perceptual hash algorithm works by:
    1. Resizing the image to a small size (8x8 for phash)
    2. Converting to grayscale
    3. Computing frequency information (DCT or gradient-based)
    4. Comparing pixel values to derive a hash

    Supported algorithms:
    - phash (default): Perceptual hash using DCT (discrete cosine transform)
                      Robust to compression and small changes. Recommended.
    - dhash: Difference hash using pixel gradients. Faster but less robust.

    Args:
        image: PIL Image object to hash.
        algorithm: Hash algorithm to use. Either "phash" (default) or "dhash".

    Returns:
        str: Hexadecimal string representation of the hash.
             For an 8x8 hash: 16 character hex string.
             For a 16x16 hash: 32 character hex string.

    Raises:
        InvalidImageError: If image is invalid or cannot be hashed.
        ValueError: If algorithm is not recognized.

    Example:
        >>> image = load_image("photo.jpg")
        >>> hash_value = compute_hash(image)
        >>> hash_value
        'a1b2c3d4e5f6a1b2'
        >>> hash2 = compute_hash(image)  # Same image
        >>> hash_value == hash2
        True
    """
    if algorithm not in ("phash", "dhash"):
        raise ValueError(f"Unknown algorithm: {algorithm}. Use 'phash' or 'dhash'.")

    try:
        if algorithm == "phash":
            hash_obj = imagehash.phash(image)
        else:  # dhash
            hash_obj = imagehash.dhash(image)

        hash_string = str(hash_obj)
        logger.debug(f"Computed {algorithm} hash: {hash_string}")
        return hash_string

    except Exception as e:
        logger.error(f"Failed to compute hash: {str(e)}")
        raise InvalidImageError(
            "unknown",
            reason="Failed to compute hash",
            details=str(e),
        ) from e


def compare_hashes(
    hash1: str,
    hash2: str,
    algorithm: str = "phash",
    similarity_threshold: int = 5,
) -> Tuple[bool, int]:
    """Compare two perceptual hashes and determine if images are duplicates.

    Computes the Hamming distance between two hashes (number of differing bits).
    Images are considered duplicates if the distance is within the threshold.

    Distance interpretation:
    - 0: Identical hashes (same or extremely similar images)
    - 1-3: Very similar (likely same image with minor compression differences)
    - 4-5: Similar (same image with rotation, slight resize, or filter applied)
    - 6-10: Somewhat similar (related images, possible duplicates)
    - 11+: Different images

    Default threshold of 5 allows detection of:
    - Images with different JPEG compression levels
    - Small crops or rotations
    - Minor filter applications
    - Slight metadata changes

    Args:
        hash1: First hash as hexadecimal string (from compute_hash).
        hash2: Second hash as hexadecimal string (from compute_hash).
        algorithm: Hash algorithm used ("phash" or "dhash"). Used for validation.
        similarity_threshold: Maximum Hamming distance to consider a duplicate.
                             Default 5 (empirically tuned for JPEG images).
                             Range: 0-64 (for 8x8 hash) or 0-256 (for 16x16).

    Returns:
        Tuple[bool, int]: A tuple containing:
            - is_duplicate (bool): True if Hamming distance <= threshold
            - hamming_distance (int): Exact Hamming distance (0 = identical)

    Raises:
        ValueError: If hashes are invalid format or similarity_threshold
                   is outside valid range.

    Example:
        >>> hash1 = "a1b2c3d4e5f6a1b2"
        >>> hash2 = "a1b2c3d4e5f6a1b3"  # 1 bit different
        >>> is_dup, distance = compare_hashes(hash1, hash2)
        >>> is_dup
        True
        >>> distance
        1
        >>> is_dup, distance = compare_hashes(hash1, "0000000000000000")
        >>> distance
        64  # All bits different
    """
    if not isinstance(hash1, str) or not isinstance(hash2, str):
        raise ValueError("Hashes must be strings")

    if not hash1 or not hash2:
        raise ValueError("Hashes cannot be empty")

    if similarity_threshold < 0 or similarity_threshold > 64:
        raise ValueError("Similarity threshold must be between 0 and 64")

    try:
        # Convert hex strings to integers and compute Hamming distance
        hash_int1 = int(hash1, 16)
        hash_int2 = int(hash2, 16)

        # XOR to find differing bits, then count them
        xor_result = hash_int1 ^ hash_int2
        hamming_distance = bin(xor_result).count("1")

        is_duplicate = hamming_distance <= similarity_threshold

        logger.debug(
            f"Compared hashes: distance={hamming_distance}, "
            f"is_duplicate={is_duplicate}"
        )

        return is_duplicate, hamming_distance

    except (ValueError, TypeError) as e:
        logger.error(f"Invalid hash format: {str(e)}")
        raise ValueError(f"Invalid hash format: {str(e)}") from e


def batch_compute_hashes(
    directory: str,
    recursive: bool = False,
    skip_errors: bool = True,
) -> Dict[str, str]:
    """Compute perceptual hashes for all JPEG images in a directory.

    Scans a directory for JPEG images and computes a perceptual hash for
    each. By default, corrupted or unreadable images are skipped with a
    warning (instead of crashing the entire scan).

    File discovery:
    - Finds files with extensions: .jpg, .jpeg (case-insensitive)
    - By default, only scans top-level directory
    - If recursive=True, scans all subdirectories recursively

    Error handling:
    - If skip_errors=True (default): Logs warning and continues
    - If skip_errors=False: Raises exception on first error

    Args:
        directory: Path to directory to scan (must exist and be readable).
        recursive: If True, scan subdirectories recursively.
                  Default False (only top-level).
        skip_errors: If True, skip corrupted files with warning.
                    If False, raise exception on first error.
                    Default True (recommended for robust scanning).

    Returns:
        Dict[str, str]: Mapping of file paths to hash strings.
                       Format: {"/path/to/image.jpg": "a1b2c3d4e5f6a1b2"}
                       Returns empty dict if directory contains no JPEG files.

    Raises:
        DirectoryNotFoundError: If directory doesn't exist.
        PermissionDeniedError: If directory is not readable.
        InvalidImageError: Only if skip_errors=False and corrupted file found.

    Example:
        >>> hashes = batch_compute_hashes("/path/to/photos")
        >>> len(hashes)
        42
        >>> list(hashes.items())[0]
        ('/path/to/photos/photo1.jpg', 'a1b2c3d4e5f6a1b2')

        >>> # Skip corrupted files
        >>> hashes = batch_compute_hashes("/path/to/photos", skip_errors=True)
        # WARNING: Skipping corrupted file: photo_bad.jpg

        >>> # Scan recursively
        >>> hashes = batch_compute_hashes("/path/to/photos", recursive=True)
        # Finds images in subdirectories too
    """
    dir_path = Path(directory)

    # Validate directory existence
    if not dir_path.exists():
        logger.warning(f"Directory not found: {directory}")
        raise DirectoryNotFoundError(directory)

    if not dir_path.is_dir():
        logger.warning(f"Path is not a directory: {directory}")
        raise DirectoryNotFoundError(directory)

    # Check readability
    try:
        dir_path.stat()
    except PermissionError as e:
        logger.warning(f"Permission denied reading directory: {directory}")
        raise PermissionDeniedError(directory, operation="read") from e

    hashes: Dict[str, str] = {}

    # Find JPEG files
    if recursive:
        glob_pattern = "**/*.jpg"
    else:
        glob_pattern = "*.jpg"

    jpeg_files = list(dir_path.glob(glob_pattern))
    # Also find .jpeg extensions
    if recursive:
        jpeg_files.extend(dir_path.glob("**/*.jpeg"))
    else:
        jpeg_files.extend(dir_path.glob("*.jpeg"))

    # Remove duplicates (same file found via .jpg and .jpeg)
    jpeg_files = list(set(jpeg_files))

    logger.info(f"Found {len(jpeg_files)} JPEG files in {directory}")

    if not jpeg_files:
        logger.debug(f"No JPEG files found in {directory}")
        return {}

    # Process each file
    for file_path in jpeg_files:
        try:
            image = load_image(str(file_path))
            hash_value = compute_hash(image)
            hashes[str(file_path)] = hash_value
            logger.debug(f"Processed: {file_path} -> {hash_value}")

        except (InvalidImageError, PermissionDeniedError) as e:
            if skip_errors:
                logger.warning(f"Skipping corrupted file: {file_path.name}: {str(e)}")
            else:
                logger.error(f"Error processing {file_path}: {str(e)}")
                raise

        except Exception as e:
            if skip_errors:
                logger.warning(f"Unexpected error processing {file_path}: {str(e)}")
            else:
                logger.error(f"Unexpected error processing {file_path}: {str(e)}")
                raise

    logger.info(f"Successfully hashed {len(hashes)} images from {directory}")
    return hashes


# --- Additional metadata helpers ---
import base64
from io import BytesIO
from typing import Any, Dict, Tuple
from PIL import ImageFilter


def compute_blur_score(image: Image.Image) -> float:
    """Compute a simple blur/sharpness score for an image.

    Uses an edge-detection filter (FIND_EDGES) on the grayscale image and
    returns the variance of the edge response. Lower variance indicates
    fewer edges => more likely blurred. This is a lightweight heuristic
    that avoids adding extra dependencies.
    """
    try:
        gray = image.convert("L")
        edges = gray.filter(ImageFilter.FIND_EDGES)
        pixels = list(edges.getdata())
        if not pixels:
            return 0.0
        n = len(pixels)
        mean = sum(pixels) / n
        var = sum((p - mean) ** 2 for p in pixels) / n
        return float(var)
    except Exception:
        return 0.0


def is_blurred(image: Image.Image, threshold: float = 2000.0) -> Tuple[bool, float]:
    """Return (is_blurred, score). Lower score -> more blurred.

    Default threshold=2000.0 chosen to work with the edge-variance heuristic used
    in compute_blur_score. Callers may tune this value via app_config when
    collecting metadata.
    """
    score = compute_blur_score(image)
    return (score < threshold, score)


def generate_thumbnail_base64(image: Image.Image, size: Tuple[int, int] = (200, 200)) -> str:
    """Create a JPEG thumbnail and return it as a data URI (base64).

    Returns a string like: 'data:image/jpeg;base64,...'
    """
    try:
        thumb = image.copy()
        thumb.thumbnail(size)
        buf = BytesIO()
        thumb.save(buf, format="JPEG", quality=75)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"
    except Exception:
        return ""


def get_image_metadata(
    file_path: str,
    thumb_size: Tuple[int, int] = None,
    blur_threshold: float = None,
    app_config: dict = None,
) -> Dict[str, Any]:
    """Collect metadata for an image file, using config if provided.

    Args:
        file_path: Path to image file.
        thumb_size: Thumbnail size (width, height). If None, uses config or (200,200).
        blur_threshold: Blur threshold. If None, uses config or 100.0.
        app_config: Optional Flask app.config dict for config values.

    Returns:
        dict: Metadata including resolution, file_size_bytes, is_blurred, blur_score, thumbnail, format.
    """
    # Use config values if provided
    if app_config is not None:
        if thumb_size is None:
            thumb_size = tuple(app_config.get("THUMBNAIL_SIZE", (200, 200)))
        if blur_threshold is None:
            blur_threshold = float(app_config.get("BLUR_THRESHOLD", 2000.0))
    if thumb_size is None:
        thumb_size = (200, 200)
    if blur_threshold is None:
        blur_threshold = 2000.0

    meta: Dict[str, Any] = {
        "resolution": None,
        "file_size_bytes": None,
        "is_blurred": False,
        "blur_score": None,
        "thumbnail": "",
        "format": None,
    }

    try:
        path = Path(file_path)
        image = load_image(file_path)

        w, h = image.size
        meta["resolution"] = (w, h)
        try:
            meta["file_size_bytes"] = path.stat().st_size
        except Exception:
            meta["file_size_bytes"] = None

        is_blur, blur_score = is_blurred(image, threshold=blur_threshold)
        meta["is_blurred"] = is_blur
        meta["blur_score"] = blur_score
        meta["thumbnail"] = generate_thumbnail_base64(image, size=thumb_size)
        meta["format"] = image.format
    except Exception as e:
        logger.warning(f"Failed to get metadata for {file_path}: {str(e)}")

    return meta


# --- New quality scoring and thumbnail helpers ---
import hashlib
import os
from typing import Optional


def compute_sharpness(image: Image.Image) -> float:
    """Compute sharpness using OpenCV if available, otherwise fallback.

    Strategy:
    - If cv2 is available, convert image to grayscale numpy array and compute
      the variance of the Laplacian (standard sharpness metric).
    - If cv2 not available, fallback to using PIL edge detection (FIND_EDGES)
      and compute variance of the result (already implemented in
      compute_blur_score). We normalize outputs to be comparable.

    Returns:
        float: sharpness score (higher -> sharper). Non-negative.
    """
    try:
        import cv2
        import numpy as np

        # Convert PIL Image to grayscale numpy array
        gray = image.convert("L")
        arr = np.array(gray)
        # Compute Laplacian and return variance
        lap = cv2.Laplacian(arr, cv2.CV_64F)
        var = float(lap.var())
        return var
    except Exception:
        # Fallback to compute_blur_score which returns variance of edges
        try:
            # compute_blur_score: higher variance -> more edges -> sharper
            return compute_blur_score(image)
        except Exception:
            return 0.0


def compute_quality_score(
    image: Optional[Image.Image] = None,
    resolution: Optional[tuple] = None,
    file_size_bytes: Optional[int] = None,
    sharpness: Optional[float] = None,
) -> float:
    """Combine resolution, file size, and sharpness into a single quality score.

    Formula (weighted, normalized):

    - resolution_score = log10(width * height + 1)
    - size_score = log10(file_size_bytes + 1)
    - sharpness_score = log10(sharpness + 1)

    Combined quality_score =  (w_res * resolution_score) + (w_size * size_score) + (w_sharp * sharpness_score)

    Weights chosen: w_res=0.5, w_size=0.2, w_sharp=0.3. These reflect a bias
    toward image resolution as the primary quality signal, with file size and
    sharpness as secondary signals. The log10 normalization reduces dominance of
    very large values and keeps the score in a reasonable numeric range.

    If image is provided but resolution/sharpness/file_size are not, they will
    be computed. Missing values default to 0.

    Args:
        image: Optional PIL Image to compute missing metrics from.
        resolution: Optional (width, height)
        file_size_bytes: Optional file size in bytes
        sharpness: Optional sharpness score

    Returns:
        float: Combined quality score.
    """
    import math

    # Compute missing values if image provided
    res_w = res_h = None
    if resolution is not None:
        try:
            res_w, res_h = int(resolution[0]), int(resolution[1])
        except Exception:
            res_w = res_h = None
    if (res_w is None or res_h is None) and image is not None:
        try:
            res_w, res_h = image.size
        except Exception:
            res_w = res_h = None

    area = 0
    if res_w and res_h:
        area = int(res_w) * int(res_h)

    size_val = int(file_size_bytes or 0)

    sharp = sharpness if sharpness is not None else None
    if sharp is None and image is not None:
        try:
            sharp = compute_sharpness(image)
        except Exception:
            sharp = 0.0
    if sharp is None:
        sharp = 0.0

    # Normalize via log10 to reduce skew
    resolution_score = math.log10(area + 1)
    size_score = math.log10(size_val + 1)
    sharpness_score = math.log10(max(float(sharp), 0.0) + 1)

    # Weights
    w_res = 0.5
    w_size = 0.2
    w_sharp = 0.3

    quality_score = (w_res * resolution_score) + (w_size * size_score) + (w_sharp * sharpness_score)
    # Scale to a round number
    return float(quality_score)


def _thumbnail_cache_path(cache_dir: str, path: str, mtime: float) -> str:
    """Compute a deterministic cache filename for a thumbnail based on path+mtime."""
    key = f"{path}|{int(mtime)}"
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()
    fname = f"{h}.jpg"
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, fname)


def generate_thumbnail(
    file_path: str,
    max_width: int = 300,
    cache_dir: str = None,
) -> bytes:
    """Generate (and cache) a JPEG thumbnail for the given file path.

    - Validates file exists and is an image via load_image
    - Resizes maintaining aspect ratio to max_width
    - Caches result on disk under cache_dir (defaults to backend/tmp/thumbnails)
    - Returns raw JPEG bytes and raises exceptions for invalid paths

    Security note: Caller should validate file_path is under allowed directories.
    """
    from io import BytesIO

    path_obj = Path(file_path)
    if not path_obj.exists() or not path_obj.is_file():
        raise FileNotFoundError(file_path)

    # Default cache_dir
    if cache_dir is None:
        base = Path(__file__).parents[2] / "tmp" / "thumbnails"
        cache_dir = str(base)

    try:
        mtime = path_obj.stat().st_mtime
    except Exception:
        mtime = 0

    cache_path = _thumbnail_cache_path(cache_dir, str(path_obj), mtime)
    # If cached, return bytes
    try:
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                return f.read()
    except Exception:
        # If cache read fails, continue to regenerate
        pass

    # Generate thumbnail in-memory
    image = load_image(str(path_obj))
    w, h = image.size
    if w <= max_width:
        thumb = image.copy()
    else:
        ratio = max_width / float(w)
        new_h = int(h * ratio)
        thumb = image.copy()
        thumb = thumb.resize((max_width, new_h), Image.LANCZOS)

    buf = BytesIO()
    thumb.save(buf, format="JPEG", quality=80)
    jpg_bytes = buf.getvalue()

    # Try to write to cache (best-effort)
    try:
        with open(cache_path, "wb") as f:
            f.write(jpg_bytes)
    except Exception:
        logger.debug(f"Failed to write thumbnail cache: {cache_path}")

    return jpg_bytes
