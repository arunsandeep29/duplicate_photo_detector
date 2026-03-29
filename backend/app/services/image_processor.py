"""Image processing module for semantic embeddings and perceptual hashes of images.

This module provides functions to load images, compute semantic embeddings using CLIP,
and compute perceptual hashes. It leverages local AI models and hardware acceleration
(CUDA) when available for high-performance duplicate detection.

The semantic embedding approach (CLIP) is 100% local and privacy-focused,
allowing for the detection of near-duplicate images based on visual content.
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import mimetypes

import imagehash
import torch
import numpy as np
from PIL import Image, ExifTags
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# Define supported extensions (excluding RAW formats like .cr2, .cr3)
SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
RAW_EXTENSIONS = {'.cr2', '.cr3', '.nef', '.arw', '.dng'}

from app.exceptions import (
    InvalidImageError,
    DirectoryNotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

# Hardware Acceleration: Explicitly check for CUDA to utilize the RTX 5050 GPU.
# torch.device('cuda') is used to offload embedding generation to the GPU, 
# providing significant speedups over CPU-based processing.
if torch.cuda.is_available():
    device = torch.device('cuda')
    logger.info("RTX 5050 GPU detected. Utilizing CUDA for hardware acceleration.")
else:
    device = torch.device('cpu')
    logger.warning("CUDA not available. Falling back to CPU for embedding generation.")

# Core Technology: Initialize CLIP model for semantic image embeddings.
# clip-ViT-B-32 provides a 100% local, privacy-focused way to generate 
# visual fingerprints (embeddings) without sending data to external APIs.
model = SentenceTransformer('clip-ViT-B-32', device=device)


def load_image(file_path: str) -> Image.Image:
    """Load and validate a supported image from file.

    This function opens an image file (JPEG, PNG, WebP), validates it,
    and returns a PIL Image object. It performs comprehensive validation.
    RAW files (.cr2, .cr3) are explicitly ignored during scan.

    Args:
        file_path: Absolute path to image file to load.

    Returns:
        PIL.Image.Image: Opened image object ready for processing.

    Raises:
        FileNotFoundError: If file does not exist.
        InvalidImageError: If file is not a supported/valid image.
    """
    path = Path(file_path)

    # Security: Reject RAW early even at load level
    if path.suffix.lower() in RAW_EXTENSIONS:
        raise InvalidImageError(path.name, reason="RAW files not supported for direct processing")

    if not path.exists():
        logger.warning(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        if not path.stat().st_size:
            raise InvalidImageError(path.name, reason="File is empty")
    except PermissionError as e:
        raise PermissionDeniedError(file_path, operation="read") from e

    # Load and validate image
    try:
        image = Image.open(file_path)
        # Verify it's actually a valid image
        _ = image.size
        _ = image.mode
        
        # Verify it's a supported format
        if image.format and image.format.upper() not in {"JPEG", "PNG", "WEBP", "MPO"}:
            logger.warning(f"Unsupported image format {image.format}: {file_path}")
            raise InvalidImageError(path.name, reason=f"Unsupported format: {image.format}")

        image.load()
        logger.debug(f"Successfully loaded {image.format} image: {file_path}")
        return image

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


def compute_embedding(image: Image.Image) -> np.ndarray:
    """Compute semantic image embedding using CLIP.

    Generates a high-dimensional vector representing the visual content
    of the image. This embedding is robust to significant changes like
    lighting, perspective, and composition, making it ideal for finding
    near-duplicates that perceptual hashes might miss.

    Process:
    1. Preprocess image (resize, normalize) via CLIP's internal processor
    2. Pass through the vision transformer (clip-ViT-B-32)
    3. Return the resulting 512-dimensional vector as a numpy array

    Args:
        image: PIL Image object to embed.

    Returns:
        np.ndarray: 512-dimensional semantic embedding vector.

    Raises:
        InvalidImageError: If embedding generation fails.
    """
    try:
        # model.encode handles image preprocessing internally
        # We ensure it returns a numpy array for easier storage/comparison
        with torch.no_grad():
            embedding = model.encode(image, convert_to_numpy=True)
        return embedding
    except Exception as e:
        logger.error(f"Failed to compute semantic embedding: {str(e)}")
        raise InvalidImageError(
            "unknown",
            reason="Failed to compute semantic embedding",
            details=str(e),
        ) from e


def batch_compute_embeddings(
    directory: str,
    recursive: bool = False,
    skip_errors: bool = True,
) -> Dict[str, np.ndarray]:
    """Compute semantic embeddings for all supported images in a directory.

    Scans a directory for JPEG, PNG, and WebP images and computes a CLIP
    embedding for each. This process is hardware-accelerated (CUDA) if available.
    RAW files (.cr2, .cr3) are explicitly ignored.

    A progress bar is displayed in the terminal via tqdm to provide
    feedback during long-running batch operations.

    Args:
        directory: Path to directory to scan.
        recursive: If True, scan subdirectories recursively.
        skip_errors: If True, skip corrupted files with warning.

    Returns:
        Dict[str, np.ndarray]: Mapping of file paths to embedding vectors.

    Raises:
        DirectoryNotFoundError: If directory doesn't exist.
        PermissionDeniedError: If directory is not readable.
    """
    dir_path = Path(directory)

    # Validate directory existence
    if not dir_path.exists() or not dir_path.is_dir():
        logger.warning(f"Invalid directory: {directory}")
        raise DirectoryNotFoundError(directory)

    # Find supported image files
    all_files = []
    if recursive:
        all_files = [f for f in dir_path.rglob("*") if f.is_file()]
    else:
        all_files = [f for f in dir_path.glob("*") if f.is_file()]
    
    # Filter for supported extensions and explicitly exclude RAW
    image_files = [
        f for f in all_files 
        if f.suffix.lower() in SUPPORTED_EXTENSIONS 
        and f.suffix.lower() not in RAW_EXTENSIONS
    ]

    logger.info(f"Found {len(image_files)} supported images for embedding in {directory}")

    if not image_files:
        return {}

    embeddings: Dict[str, np.ndarray] = {}

    # Process each file with a progress bar
    for file_path in tqdm(image_files, desc="Generating embeddings", unit="image"):
        try:
            image = load_image(str(file_path))
            embedding = compute_embedding(image)
            embeddings[str(file_path)] = embedding
            logger.debug(f"Embedded: {file_path}")

        except (InvalidImageError, PermissionDeniedError, FileNotFoundError) as e:
            if skip_errors:
                logger.warning(f"Skipping file {file_path.name}: {str(e)}")
            else:
                raise
        except Exception as e:
            if skip_errors:
                logger.warning(f"Unexpected error on {file_path}: {str(e)}")
            else:
                raise

    logger.info(f"Successfully embedded {len(embeddings)} images from {directory}")
    return embeddings


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
    """Collect metadata for an image file, including EXIF and format info.

    Args:
        file_path: Path to image file.
        thumb_size: Thumbnail size (width, height). If None, uses config or (200,200).
        blur_threshold: Blur threshold. If None, uses config or 2000.0.
        app_config: Optional Flask app.config dict for config values.

    Returns:
        dict: Metadata including resolution, file_size_bytes, is_blurred, blur_score, thumbnail, format, and has_exif.
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
        "has_exif": False,
    }

    try:
        path = Path(file_path)
        
        # Security: Skip RAW files explicitly to avoid processing heavy formats
        if path.suffix.lower() in RAW_EXTENSIONS:
            logger.debug(f"Skipping RAW metadata extraction for: {file_path}")
            return meta

        image = load_image(file_path)

        meta["format"] = image.format
        meta["resolution"] = image.size
        
        # Check for EXIF metadata presence (high signal for original images)
        try:
            exif = image.getexif()
            meta["has_exif"] = bool(exif)
        except Exception:
            meta["has_exif"] = False

        try:
            meta["file_size_bytes"] = path.stat().st_size
        except Exception:
            meta["file_size_bytes"] = None

        is_blur, blur_score = is_blurred(image, threshold=blur_threshold)
        meta["is_blurred"] = is_blur
        meta["blur_score"] = blur_score
        meta["thumbnail"] = generate_thumbnail_base64(image, size=thumb_size)
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
    has_exif: bool = False,
    file_format: str = "JPEG"
) -> float:
    """Advanced Quality Scoring to identify the 'Source' image.

    This improved formula rewards:
    1.  Data Integrity (EXIF presence: +2.0)
    2.  Visual Fidelity (Resolution 40%, Sharpness 30%)
    3.  Format Efficiency (PNG/WebP priority)
    4.  Raw Data (File size 10%)

    Args:
        image: Optional PIL Image (currently unused for direct score)
        resolution: (width, height)
        file_size_bytes: Size in bytes
        sharpness: Precomputed sharpness score
        has_exif: Boolean indicating if metadata exists
        file_format: The image format (e.g., 'PNG', 'JPEG')

    Returns:
        float: Combined quality score.
    """
    import math

    # Calculate base metrics
    res_w = res_h = 0
    if resolution:
        try:
            res_w, res_h = int(resolution[0]), int(resolution[1])
        except Exception:
            res_w = res_h = 0
    
    area = res_w * res_h
    size_val = file_size_bytes or 0
    sharp = sharpness or 0.0

    # 1. Fidelity Scores (Log-normalized to reduce outliers)
    # Resolution remains a strong signal for original quality
    res_score = math.log10(area + 1) * 0.4
    # Sharpness indicates lack of blur or heavy compression artifacts
    sharp_score = math.log10(sharp + 1) * 0.3
    # File size acts as a proxy for bitrate/detail in lossy formats
    size_score = math.log10(size_val + 1) * 0.1

    # 2. Metadata Bonus (Extremely high signal for non-forwarded originals)
    exif_bonus = 2.0 if has_exif else 0.0

    # 3. Format Multiplier (Reward more efficient or lossless formats)
    format_map = {
        'PNG': 1.2,   # Lossless
        'WEBP': 1.1,  # Efficient
        'JPEG': 1.0,  # Baseline
        'MPO': 1.0
    }
    format_mult = format_map.get(str(file_format).upper(), 1.0)

    # 4. Final Aggregation
    # We add the signals and multiply by format efficiency
    final_score = (res_score + sharp_score + size_score + exif_bonus) * format_mult
    
    return round(float(final_score), 3)


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
