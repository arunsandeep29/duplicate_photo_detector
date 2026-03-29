"""Duplicate image detection service using semantic embeddings.

This module finds groups of duplicate or near-duplicate images by analyzing
their semantic embeddings (CLIP). It uses cosine similarity and clustering
to group visually similar images together.
"""

import logging
from typing import Dict, List, Set, Tuple, Any
import numpy as np

logger = logging.getLogger(__name__)


def find_duplicates(
    embeddings: Dict[str, np.ndarray],
    similarity_threshold: float = 0.95,
) -> List[Dict[str, Any]]:
    """Find groups of duplicate images using semantic embeddings and cosine similarity.

    This function analyzes a dictionary of file paths and their CLIP embeddings
    to identify groups of duplicate or near-duplicate images. It uses cosine
    similarity to measure visual relatedness.

    The algorithm:
    1. Compares all pairs of embeddings using cosine similarity.
    2. Groups images with similarity >= threshold (default 0.95).
    3. Uses union-find to track connected components (transitive groups).
    4. Ranks images within each group by quality (resolution, sharpness, etc.).
    5. Returns groups with 2+ files (ignores unique images).

    Args:
        embeddings: Dictionary mapping file paths to numpy embedding vectors.
                   Format: {"/path/to/image.jpg": np.array([...])}
        similarity_threshold: Minimum cosine similarity (0.0 to 1.0) to consider
                             images as duplicates. Default 0.95.

    Returns:
        List of duplicate group dictionaries with rich metadata and legacy fields.
    """
    if not embeddings:
        logger.warning("Empty embeddings dictionary provided")
        raise ValueError("Embeddings dictionary cannot be empty")

    if not (0.0 <= similarity_threshold <= 1.0):
        raise ValueError("Similarity threshold must be between 0.0 and 1.0")

    file_list = list(embeddings.keys())
    file_list_len = len(file_list)
    logger.info(f"Finding duplicates in {file_list_len} images using cosine similarity")

    # Step 1: Use union-find for clustering similar embeddings
    file_to_group = {i: i for i in range(file_list_len)}

    def find_parent(idx: int) -> int:
        if file_to_group[idx] != idx:
            file_to_group[idx] = find_parent(file_to_group[idx])
        return file_to_group[idx]

    def union(idx1: int, idx2: int) -> None:
        parent1 = find_parent(idx1)
        parent2 = find_parent(idx2)
        if parent1 != parent2:
            file_to_group[parent1] = parent2

    # Pre-normalize embeddings for faster cosine similarity (dot product)
    normalized_embeddings = {}
    for path, vec in embeddings.items():
        norm = np.linalg.norm(vec)
        normalized_embeddings[path] = vec / norm if norm > 0 else vec

    # Compare all pairs (O(n^2) approach, suitable for local directories)
    for i in range(file_list_len):
        for j in range(i + 1, file_list_len):
            path_i = file_list[i]
            path_j = file_list[j]
            
            # Cosine similarity of normalized vectors is just the dot product
            similarity = np.dot(normalized_embeddings[path_i], normalized_embeddings[path_j])
            
            if similarity >= similarity_threshold:
                union(i, j)
                logger.debug(f"Grouped {path_i} and {path_j} (similarity={similarity:.4f})")

    # Step 2: Collect merged groups
    merged_groups: Dict[int, List[str]] = {}
    for file_idx, file_path in enumerate(file_list):
        parent = find_parent(file_idx)
        if parent not in merged_groups:
            merged_groups[parent] = []
        merged_groups[parent].append(file_path)

    # Step 3: Format output and enrich with metadata
    result = []
    from app.services.image_processor import (
        get_image_metadata,
        compute_quality_score,
        compute_sharpness,
        load_image
    )
    from flask import current_app
    from urllib.parse import quote_plus

    for group_files in merged_groups.values():
        if len(group_files) < 2:
            continue

        # Gather metadata and scores for each file in the group
        file_metas = {}
        for f in group_files:
            try:
                app_config = getattr(current_app, "config", None)
            except Exception:
                app_config = None
            
            meta = get_image_metadata(f, app_config=app_config)
            
            # Compute sharpness separately for better accuracy
            sharp = None
            try:
                img_obj = load_image(f)
                sharp = compute_sharpness(img_obj)
            except Exception:
                sharp = 0.0
            
            meta["sharpness"] = sharp
            score = compute_quality_score(
                resolution=meta.get("resolution"),
                file_size_bytes=meta.get("file_size_bytes"),
                sharpness=meta.get("sharpness"),
                has_exif=meta.get("has_exif", False),
                file_format=meta.get("format", "JPEG")
            )
            meta["quality_score"] = score
            file_metas[f] = meta

        # Rank files: highest quality score first
        sorted_files = sorted(
            group_files,
            key=lambda p: (-file_metas[p]["quality_score"], p),
        )
        
        # Domain heuristic: prefer non-blurred images as the 'original'
        original = sorted_files[0]
        non_blurred = [p for p in sorted_files if not file_metas[p].get("is_blurred")]
        if non_blurred:
            original = non_blurred[0]

        copies = [p for p in group_files if p != original]
        
        # Build detailed information for each file in the group
        details = {}
        legacy_details = {}
        for p in group_files:
            meta = file_metas[p]
            
            # Calculate similarity to original for the reason string
            sim_to_orig = np.dot(normalized_embeddings[original], normalized_embeddings[p])
            
            reason = "highest quality" if p == original else f"similarity={sim_to_orig:.4f}"
            res = meta.get("resolution")
            size = meta.get("file_size_bytes")
            sharp = meta.get("sharpness")
            reason_text = f"{reason}; res={res}; size={size}; sharp={round(sharp, 2) if sharp else 'N/A'}"

            details[p] = {
                "path": p,
                "preview_url": f"/api/preview?path={quote_plus(p)}",
                "quality_score": meta["quality_score"],
                "reason": reason_text,
            }
            
            # Maintain legacy details for backward compatibility
            legacy_details[p] = {
                "resolution": res,
                "is_blurred": bool(meta.get("is_blurred")),
                "blur_score": meta.get("blur_score"),
                "thumbnail": meta.get("thumbnail", ""),
                "similarity": float(sim_to_orig),
                "reason": reason_text,
            }

        group_entry = {
            "original": original,
            "hash": "semantic-v1",  # Placeholder for legacy 'hash' field
            "copies": copies,
            "original_info": details[original],
            "copies_info": [details[c] for c in copies],
            "details": legacy_details,
            "original_thumbnail": file_metas[original].get("thumbnail", ""),
            "original_resolution": file_metas[original].get("resolution"),
            "original_is_blurred": bool(file_metas[original].get("is_blurred")),
            "blurred": [p for p in group_files if p != original],
        }
        result.append(group_entry)

    logger.info(f"Found {len(result)} duplicate groups")
    return result


def merge_similar_groups(
    groups: List[Dict[str, object]],
    similarity_threshold: int = 5,
) -> List[Dict[str, object]]:
    """Merge groups of similar hashes into single duplicate groups.

    This function handles the case where similar images create multiple
    separate groups due to transitivity. For example:
    - Image A matches B (distance 3)
    - Image B matches C (distance 4)
    - But C doesn't match A (distance 8)

    Without merging: Groups would be [A, B] and [C]
    With merging: Should be [A, B, C]

    This function ensures all related images end up in the same group.

    Args:
        groups: List of duplicate group dictionaries from find_duplicates.
        similarity_threshold: Maximum Hamming distance to merge groups.

    Returns:
        List of merged group dictionaries in same format as input.
        May have fewer groups if similar groups were merged.

    Raises:
        ValueError: If groups list is empty.
    """
    if not groups:
        logger.warning("Empty groups list provided")
        raise ValueError("Groups list cannot be empty")

    from app.services.image_processor import compare_hashes

    logger.info(f"Merging {len(groups)} groups with similar hashes")

    # If only one group, nothing to merge
    if len(groups) <= 1:
        return groups

    # Use union-find to merge groups that should be together
    group_to_parent = {i: i for i in range(len(groups))}

    def find_parent(idx: int) -> int:
        """Find the root parent of a group."""
        if group_to_parent[idx] != idx:
            group_to_parent[idx] = find_parent(group_to_parent[idx])
        return group_to_parent[idx]

    def union(idx1: int, idx2: int) -> None:
        """Union two groups."""
        parent1 = find_parent(idx1)
        parent2 = find_parent(idx2)
        if parent1 != parent2:
            group_to_parent[parent1] = parent2

    # Compare all pairs of groups (by their original hash)
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            hash_i = groups[i]["hash"]
            hash_j = groups[j]["hash"]

            try:
                is_similar, distance = compare_hashes(
                    hash_i, hash_j, similarity_threshold=similarity_threshold
                )
                if is_similar:
                    union(i, j)
                    logger.debug(f"Merged group {i} and group {j} (distance={distance})")
            except ValueError:
                logger.warning(f"Failed to compare group hashes: {hash_i} and {hash_j}")

    # Collect merged groups
    merged_groups: Dict[int, Dict[str, object]] = {}
    for group_idx, group in enumerate(groups):
        parent = find_parent(group_idx)

        if parent not in merged_groups:
            # Create new merged group with first group's original
            merged_groups[parent] = {
                "original": group["original"],
                "hash": group["hash"],
                "copies": list(group["copies"]),
            }
        else:
            # Merge copies into existing group
            merged_groups[parent]["copies"].extend(group["copies"])

    # Sort copies in each group for consistency
    for group in merged_groups.values():
        group["copies"].sort()

    result = list(merged_groups.values())
    logger.info(f"After merging: {len(result)} groups")
    return result


def validate_groups(groups: List[Dict[str, object]]) -> bool:
    """Validate that duplicate groups are properly formatted and valid.

    Performs comprehensive validation including:
    - All required fields present (original, hash, copies)
    - No file appears in multiple groups
    - Each group has at least 2 files (original + 1+ copies)
    - All file paths are strings
    - Hash is non-empty string
    - Groups list is not empty (unless input was empty)

    Args:
        groups: List of group dictionaries to validate.

    Returns:
        bool: True if all groups are valid, False otherwise.
              Returns True for empty list (edge case).

    Example:
        >>> groups = [
        ...     {
        ...         "original": "photo1.jpg",
        ...         "hash": "a1b2c3d4",
        ...         "copies": ["photo1_copy.jpg"]
        ...     }
        ... ]
        >>> validate_groups(groups)
        True

        >>> bad_groups = [
        ...     {
        ...         "original": "photo1.jpg",
        ...         # Missing hash and copies
        ...     }
        ... ]
        >>> validate_groups(bad_groups)
        False
    """
    if not groups:
        logger.debug("Empty groups list is valid (no duplicates found)")
        return True

    seen_files: Set[str] = set()

    for group_idx, group in enumerate(groups):
        # Check required fields
        if not isinstance(group, dict):
            logger.error(f"Group {group_idx} is not a dictionary")
            return False

        required_fields = {"original", "hash", "copies"}
        if not all(field in group for field in required_fields):
            logger.error(f"Group {group_idx} missing required fields: {required_fields}")
            return False

        original = group["original"]
        hash_val = group["hash"]
        copies = group["copies"]

        # Validate field types
        if not isinstance(original, str) or not original:
            logger.error(f"Group {group_idx}: original must be non-empty string")
            return False

        if not isinstance(hash_val, str) or not hash_val:
            logger.error(f"Group {group_idx}: hash must be non-empty string")
            return False

        if not isinstance(copies, list):
            logger.error(f"Group {group_idx}: copies must be list")
            return False

        # Validate copies
        for copy_idx, copy_file in enumerate(copies):
            if not isinstance(copy_file, str) or not copy_file:
                logger.error(f"Group {group_idx}, copy {copy_idx}: must be non-empty string")
                return False

        # Check for overlapping files
        if original in seen_files:
            logger.error(f"Group {group_idx}: original '{original}' appears in multiple groups")
            return False
        seen_files.add(original)

        for copy_file in copies:
            if copy_file in seen_files:
                logger.error(f"Group {group_idx}: file '{copy_file}' appears in multiple groups")
                return False
            seen_files.add(copy_file)

        # Each group must have original + at least 1 copy
        if len(copies) < 1:
            logger.error(f"Group {group_idx}: must have at least 1 copy")
            return False

    logger.debug(f"Validated {len(groups)} groups: all valid")
    return True
