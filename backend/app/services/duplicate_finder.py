"""Duplicate image detection service.

This module finds groups of duplicate or near-duplicate images by analyzing
their perceptual hashes. It uses clustering and union-find algorithms to
efficiently group similar images together.
"""

import logging
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


def find_duplicates(
    hashes: Dict[str, str],
    similarity_threshold: int = 5,
) -> List[Dict[str, object]]:
    """Find groups of duplicate images from perceptual hashes.

    This function analyzes a dictionary of file paths and their perceptual
    hashes to identify groups of duplicate or near-duplicate images. It uses
    an efficient clustering algorithm to group similar hashes together.

    The algorithm:
    1. Groups files with identical hashes (exact matches)
    2. Uses graph-based clustering to merge groups with similar hashes
    3. Uses union-find to track connected components
    4. Returns groups with 2+ files (ignores unique images)

    Time complexity: O(n²) worst-case for hash comparison, where n is number
    of unique hashes. In practice much better due to early pruning.

    Args:
        hashes: Dictionary mapping file paths to hash strings.
                Format: {"/path/to/image.jpg": "a1b2c3d4e5f6a1b2"}
        similarity_threshold: Maximum Hamming distance to consider images
                             similar. Default 5. Must be 0-64.

    Returns:
        List of duplicate group dictionaries. Each group has:
            {
                "original": "/path/to/original.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["/path/to/copy1.jpg", "/path/to/copy2.jpg"]
            }

        Returns empty list if:
        - Input hashes dict is empty
        - No duplicates found (all images unique)
        - Only single instance of each image

    Raises:
        ValueError: If hashes dict is empty.
        ValueError: If similarity_threshold is outside valid range (0-64).

    Example:
        >>> hashes = {
        ...     "photo1.jpg": "a1b2c3d4e5f6a1b2",
        ...     "photo1_copy.jpg": "a1b2c3d4e5f6a1b2",  # Identical
        ...     "photo2.jpg": "f6e5d4c3b2a10000",
        ...     "photo2_dup.jpg": "f6e5d4c3b2a10001",   # 1 bit different
        ... }
        >>> groups = find_duplicates(hashes)
        >>> len(groups)
        2
        >>> groups[0]["original"]
        'photo1.jpg'
        >>> len(groups[0]["copies"])
        1
    """
    if not hashes:
        logger.warning("Empty hashes dictionary provided")
        raise ValueError("Hashes dictionary cannot be empty")

    if similarity_threshold < 0 or similarity_threshold > 64:
        raise ValueError("Similarity threshold must be between 0 and 64")

    # Import here to avoid circular imports
    from app.services.image_processor import compare_hashes

    logger.info(f"Finding duplicates in {len(hashes)} images")

    # Step 1: Group by exact hash matches
    exact_groups: Dict[str, List[str]] = {}
    for file_path, hash_value in hashes.items():
        if hash_value not in exact_groups:
            exact_groups[hash_value] = []
        exact_groups[hash_value].append(file_path)

    # Step 2: Use union-find for clustering similar hashes
    file_to_group = {}  # Maps file to its group ID
    groups_list = []  # List of groups, each is a set of file indices

    # Create initial groups from exact matches
    file_list = list(hashes.keys())
    for file_idx, file_path in enumerate(file_list):
        file_to_group[file_idx] = file_idx
        groups_list.append({file_idx})

    # Union-find helper functions
    def find_parent(idx: int) -> int:
        """Find the root parent of a group."""
        if file_to_group[idx] != idx:
            file_to_group[idx] = find_parent(file_to_group[idx])
        return file_to_group[idx]

    def union(idx1: int, idx2: int) -> None:
        """Union two groups."""
        parent1 = find_parent(idx1)
        parent2 = find_parent(idx2)
        if parent1 != parent2:
            file_to_group[parent1] = parent2

    # Compare all pairs of hashes and union similar ones
    file_list_len = len(file_list)
    for i in range(file_list_len):
        for j in range(i + 1, file_list_len):
            hash_i = hashes[file_list[i]]
            hash_j = hashes[file_list[j]]

            try:
                is_similar, distance = compare_hashes(
                    hash_i, hash_j, similarity_threshold=similarity_threshold
                )
                if is_similar:
                    union(i, j)
                    logger.debug(f"Grouped {file_list[i]} and {file_list[j]} (distance={distance})")
            except ValueError:
                logger.warning(f"Failed to compare hashes: {hash_i} and {hash_j}")

    # Step 3: Collect merged groups
    merged_groups: Dict[int, List[str]] = {}
    for file_idx, file_path in enumerate(file_list):
        parent = find_parent(file_idx)
        if parent not in merged_groups:
            merged_groups[parent] = []
        merged_groups[parent].append(file_path)

    # Step 4: Format output
    result = []
    for group_files in merged_groups.values():
        if len(group_files) >= 2:
            # Use quality scoring to pick the original. Compute metadata for each file.
            from app.services.image_processor import (
                get_image_metadata,
                compute_quality_score,
                compute_sharpness,
            )
            from flask import current_app
            from urllib.parse import quote_plus

            # Gather metadata for files in this group (cache, only once per file)
            file_metas = {}
            for f in group_files:
                if f not in file_metas:
                    try:
                        app_config = getattr(current_app, "config", None)
                    except Exception:
                        app_config = None
                    try:
                        meta = get_image_metadata(f, app_config=app_config)
                    except Exception:
                        meta = {"resolution": None, "is_blurred": False, "blur_score": None, "thumbnail": "", "file_size_bytes": None}
                    # Compute sharpness separately (more accurate when cv2 available)
                    try:
                        from app.services.image_processor import load_image

                        img_obj = None
                        try:
                            img_obj = load_image(f)
                        except Exception:
                            img_obj = None
                        sharp = None
                        if img_obj is not None:
                            try:
                                sharp = compute_sharpness(img_obj)
                            except Exception:
                                sharp = None
                    except Exception:
                        sharp = None

                    meta["sharpness"] = sharp
                    # Compute quality score using available metrics
                    score = compute_quality_score(
                        image=None,
                        resolution=meta.get("resolution"),
                        file_size_bytes=meta.get("file_size_bytes"),
                        sharpness=meta.get("sharpness"),
                    )
                    meta["quality_score"] = score
                    file_metas[f] = meta

            # Choose original = file with highest quality_score. Tie-break lexicographically
            sorted_files = sorted(
                group_files,
                key=lambda p: (file_metas.get(p, {}).get("quality_score", 0.0), p),
                reverse=True,
            )
            original = sorted_files[0]
            copies = [p for p in group_files if p != original]

            # Build output objects with preview_url and reason strings
            details = {}
            blurred_list = []
            for p in group_files:
                meta = file_metas.get(p, {})
                if meta.get("is_blurred"):
                    blurred_list.append(p)

                # compute hamming distance for additional reason
                try:
                    from app.services.image_processor import compare_hashes
                    _, distance = compare_hashes(hashes[original], hashes[p])
                except Exception:
                    distance = None

                # Build reason string: include hamming_distance and individual metric breakdown
                reason_parts = []
                if p == original:
                    reason_parts.append("chosen as highest quality")
                else:
                    reason_parts.append("duplicate of original")

                if distance is not None:
                    reason_parts.append(f"hamming_distance={distance}")

                res = meta.get("resolution")
                size_b = meta.get("file_size_bytes")
                sharp = meta.get("sharpness")
                reason_parts.append(
                    f"resolution={res}; size={size_b}; sharpness={round(sharp,2) if sharp is not None else 'N/A'}"
                )

                reason_text = "; ".join(reason_parts)

                details[p] = {
                    "path": p,
                    "preview_url": f"/api/preview?path={quote_plus(p)}",
                    "quality_score": meta.get("quality_score"),
                    "reason": reason_text,
                }

            # Build group with legacy fields plus new structured info.
            group_original_info = details[original]
            group_copies_info = [details[c] for c in copies]

            # Legacy fields (keep backward compatibility)
            legacy_original = original
            legacy_copies = copies
            legacy_hash = hashes.get(original)

            result.append({
                "original": legacy_original,  # legacy: string path
                "hash": legacy_hash,
                "copies": legacy_copies,
                # New structured additions
                "original_info": group_original_info,
                "copies_info": group_copies_info,
            })

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
