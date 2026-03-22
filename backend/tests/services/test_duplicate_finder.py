"""Tests for duplicate_finder module.

Comprehensive test suite for duplicate detection, group merging, and validation.
"""

import pytest
from typing import Dict, List

from app.services.duplicate_finder import (
    find_duplicates,
    merge_similar_groups,
    validate_groups,
)


class TestFindDuplicates:
    """Tests for find_duplicates function."""

    def test_find_duplicates_empty_raises_error(self) -> None:
        """Test empty hashes dict raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            find_duplicates({})

    def test_find_duplicates_no_duplicates(self) -> None:
        """Test when no duplicates exist."""
        hashes = {
            "photo1.jpg": "ffffffffffffffff",  # All 1s
            "photo2.jpg": "0000000000000000",  # All 0s
            "photo3.jpg": "1010101010101010",  # Alternating
        }
        groups = find_duplicates(hashes)
        assert groups == []

    def test_find_duplicates_exact_match(self) -> None:
        """Test finding exact hash matches."""
        hashes = {
            "photo1.jpg": "a1b2c3d4e5f6a1b2",
            "photo1_copy.jpg": "a1b2c3d4e5f6a1b2",  # Identical
            "photo2.jpg": "0000000000000000",
        }
        groups = find_duplicates(hashes)
        assert len(groups) == 1
        assert groups[0]["original"] == "photo1.jpg"
        assert "photo1_copy.jpg" in groups[0]["copies"]
        assert groups[0]["hash"] == "a1b2c3d4e5f6a1b2"

    def test_find_duplicates_similar_within_threshold(self) -> None:
        """Test finding similar hashes within threshold."""
        hashes = {
            "photo1.jpg": "a1b2c3d4e5f6a1b2",
            "photo1_slightly_different.jpg": "a1b2c3d4e5f6a1b3",  # 1 bit diff
            "photo2.jpg": "0000000000000000",
        }
        groups = find_duplicates(hashes, similarity_threshold=5)
        assert len(groups) == 1
        assert groups[0]["original"] == "photo1.jpg"
        assert "photo1_slightly_different.jpg" in groups[0]["copies"]

    def test_find_duplicates_similar_outside_threshold(self) -> None:
        """Test hashes outside threshold are not grouped."""
        hashes = {
            "photo1.jpg": "a1b2c3d4e5f6a1b2",
            "photo2.jpg": "00000000000000f0",  # Very different
        }
        groups = find_duplicates(hashes, similarity_threshold=5)
        assert groups == []

    def test_find_duplicates_multiple_groups(self) -> None:
        """Test finding multiple duplicate groups."""
        hashes = {
            "photo1.jpg": "a1b2c3d4e5f6a1b2",
            "photo1_copy.jpg": "a1b2c3d4e5f6a1b2",
            "photo2.jpg": "f6e5d4c3b2a10000",
            "photo2_copy.jpg": "f6e5d4c3b2a10000",
            "photo3.jpg": "0000000000000000",
        }
        groups = find_duplicates(hashes)
        assert len(groups) == 2
        # Verify both groups have originals
        originals = {g["original"] for g in groups}
        assert "photo1.jpg" in originals
        assert "photo2.jpg" in originals

    def test_find_duplicates_invalid_threshold(self) -> None:
        """Test invalid threshold raises ValueError."""
        hashes = {"photo1.jpg": "a1b2c3d4e5f6a1b2"}
        with pytest.raises(ValueError):
            find_duplicates(hashes, similarity_threshold=-1)
        with pytest.raises(ValueError):
            find_duplicates(hashes, similarity_threshold=65)

    def test_find_duplicates_groups_have_copies(self) -> None:
        """Test that groups have at least one copy."""
        hashes = {
            "photo1.jpg": "a1b2c3d4e5f6a1b2",
            "photo1_copy.jpg": "a1b2c3d4e5f6a1b2",
            "photo1_copy2.jpg": "a1b2c3d4e5f6a1b2",
        }
        groups = find_duplicates(hashes)
        assert len(groups) == 1
        assert len(groups[0]["copies"]) >= 1

    def test_find_duplicates_returns_list(self) -> None:
        """Test that result is a list."""
        hashes = {"photo1.jpg": "a1b2c3d4e5f6a1b2"}
        groups = find_duplicates(hashes)
        assert isinstance(groups, list)

    def test_find_duplicates_original_is_first_file(self) -> None:
        """Test that original is the first file alphabetically."""
        hashes = {
            "zzz.jpg": "a1b2c3d4e5f6a1b2",
            "aaa.jpg": "a1b2c3d4e5f6a1b2",
            "mmm.jpg": "a1b2c3d4e5f6a1b2",
        }
        groups = find_duplicates(hashes)
        assert groups[0]["original"] == "aaa.jpg"

    def test_find_duplicates_clustering(self) -> None:
        """Test clustering of multiple similar images."""
        hashes = {
            "photo1.jpg": "a1b2c3d4e5f6a1b0",
            "photo2.jpg": "a1b2c3d4e5f6a1b1",  # 1 bit from photo1
            "photo3.jpg": "a1b2c3d4e5f6a1b2",  # 2 bits from photo1
            "photo4.jpg": "a1b2c3d4e5f6a1b3",  # 3 bits from photo1
        }
        groups = find_duplicates(hashes, similarity_threshold=3)
        # All should be in same group due to transitivity
        assert len(groups) == 1
        assert len(groups[0]["copies"]) == 3


class TestMergeSimilarGroups:
    """Tests for merge_similar_groups function."""

    def test_merge_similar_groups_empty_raises_error(self) -> None:
        """Test empty groups list raises ValueError."""
        with pytest.raises(ValueError):
            merge_similar_groups([])

    def test_merge_similar_groups_single_group(self) -> None:
        """Test single group returns unchanged."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            }
        ]
        result = merge_similar_groups(groups)
        assert result == groups

    def test_merge_similar_groups_no_merging_needed(self) -> None:
        """Test groups that shouldn't merge."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            },
            {
                "original": "photo2.jpg",
                "hash": "0000000000000000",
                "copies": ["photo2_copy.jpg"],
            },
        ]
        result = merge_similar_groups(groups)
        assert len(result) == 2

    def test_merge_similar_groups_merges_similar(self) -> None:
        """Test merging of similar groups."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b0",
                "copies": ["photo1_copy.jpg"],
            },
            {
                "original": "photo2.jpg",
                "hash": "a1b2c3d4e5f6a1b1",  # 1 bit different
                "copies": ["photo2_copy.jpg"],
            },
        ]
        result = merge_similar_groups(groups, similarity_threshold=5)
        # Should be merged into one group
        assert len(result) == 1
        # Original should keep first one
        assert result[0]["original"] == "photo1.jpg"
        # Both copies should be in result
        assert len(result[0]["copies"]) >= 2

    def test_merge_similar_groups_transitive(self) -> None:
        """Test transitive merging (A~B and B~C merge to A+B+C)."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b0",
                "copies": [],
            },
            {
                "original": "photo2.jpg",
                "hash": "a1b2c3d4e5f6a1b1",  # 1 bit from photo1
                "copies": [],
            },
            {
                "original": "photo3.jpg",
                "hash": "a1b2c3d4e5f6a1b2",  # 2 bits from photo1
                "copies": [],
            },
        ]
        result = merge_similar_groups(groups, similarity_threshold=3)
        # All three should merge transitively
        assert len(result) == 1

    def test_merge_similar_groups_returns_list(self) -> None:
        """Test that result is a list."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            }
        ]
        result = merge_similar_groups(groups)
        assert isinstance(result, list)

    def test_merge_similar_groups_preserves_structure(self) -> None:
        """Test that result groups have correct structure."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b0",
                "copies": ["photo1_copy.jpg"],
            },
            {
                "original": "photo2.jpg",
                "hash": "a1b2c3d4e5f6a1b1",
                "copies": ["photo2_copy.jpg"],
            },
        ]
        result = merge_similar_groups(groups, similarity_threshold=5)
        for group in result:
            assert "original" in group
            assert "hash" in group
            assert "copies" in group
            assert isinstance(group["copies"], list)


class TestValidateGroups:
    """Tests for validate_groups function."""

    def test_validate_groups_empty_list(self) -> None:
        """Test empty groups list is valid."""
        assert validate_groups([]) is True

    def test_validate_groups_valid_single(self) -> None:
        """Test valid single group."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            }
        ]
        assert validate_groups(groups) is True

    def test_validate_groups_valid_multiple(self) -> None:
        """Test valid multiple groups."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            },
            {
                "original": "photo2.jpg",
                "hash": "0000000000000000",
                "copies": ["photo2_copy.jpg"],
            },
        ]
        assert validate_groups(groups) is True

    def test_validate_groups_missing_original(self) -> None:
        """Test group missing 'original' field."""
        groups = [
            {
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            }
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_missing_hash(self) -> None:
        """Test group missing 'hash' field."""
        groups = [
            {
                "original": "photo1.jpg",
                "copies": ["photo1_copy.jpg"],
            }
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_missing_copies(self) -> None:
        """Test group missing 'copies' field."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
            }
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_not_a_dict(self) -> None:
        """Test non-dictionary group."""
        groups = ["not a dict"]
        assert validate_groups(groups) is False

    def test_validate_groups_original_not_string(self) -> None:
        """Test original that is not a string."""
        groups = [
            {
                "original": 123,  # Not a string
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            }
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_hash_not_string(self) -> None:
        """Test hash that is not a string."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": 123,  # Not a string
                "copies": ["photo1_copy.jpg"],
            }
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_copies_not_list(self) -> None:
        """Test copies that is not a list."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": "not a list",
            }
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_empty_copies(self) -> None:
        """Test group with no copies."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": [],
            }
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_overlapping_files(self) -> None:
        """Test that overlapping files across groups are detected."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            },
            {
                "original": "photo1_copy.jpg",  # Appears in both groups!
                "hash": "0000000000000000",
                "copies": ["photo2_copy.jpg"],
            },
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_copy_in_multiple_groups(self) -> None:
        """Test that copies appearing in multiple groups are detected."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["shared_copy.jpg"],
            },
            {
                "original": "photo2.jpg",
                "hash": "0000000000000000",
                "copies": ["shared_copy.jpg"],  # Appears twice!
            },
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_empty_file_path(self) -> None:
        """Test group with empty file path."""
        groups = [
            {
                "original": "",  # Empty
                "hash": "a1b2c3d4e5f6a1b2",
                "copies": ["photo1_copy.jpg"],
            }
        ]
        assert validate_groups(groups) is False

    def test_validate_groups_empty_hash(self) -> None:
        """Test group with empty hash."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "",  # Empty
                "copies": ["photo1_copy.jpg"],
            }
        ]
        assert validate_groups(groups) is False


class TestDuplicateFinderIntegration:
    """Integration tests for duplicate finder."""

    def test_find_and_validate(self) -> None:
        """Test find_duplicates output passes validation."""
        hashes = {
            "photo1.jpg": "a1b2c3d4e5f6a1b2",
            "photo1_copy.jpg": "a1b2c3d4e5f6a1b2",
        }
        groups = find_duplicates(hashes)
        assert validate_groups(groups) is True

    def test_merge_and_validate(self) -> None:
        """Test merge_similar_groups output passes validation."""
        groups = [
            {
                "original": "photo1.jpg",
                "hash": "a1b2c3d4e5f6a1b0",
                "copies": ["photo1_copy.jpg"],
            },
            {
                "original": "photo2.jpg",
                "hash": "a1b2c3d4e5f6a1b1",
                "copies": ["photo2_copy.jpg"],
            },
        ]
        result = merge_similar_groups(groups, similarity_threshold=5)
        assert validate_groups(result) is True

# --- Additional tests for resolution, details, blur, edge cases, caching ---
import tempfile
import shutil
import os
from PIL import Image, ImageFilter
from app.services import duplicate_finder, image_processor
from unittest import mock

def create_image(path, size=(100, 100), color=(255, 255, 255), blur=False):
    img = Image.new("RGB", size, color)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=8))
    img.save(path, format="JPEG")
    return path

def test_resolution_based_original_selection(tmp_path):
    # Create three identical images at different resolutions
    img1 = tmp_path / "img1.jpg"
    img2 = tmp_path / "img2.jpg"
    img3 = tmp_path / "img3.jpg"
    create_image(img1, (100, 100))
    create_image(img2, (200, 200))
    create_image(img3, (150, 150))
    # All have same content, so same hash
    hash_val = image_processor.compute_hash(image_processor.load_image(str(img1)))
    hashes = {str(img1): hash_val, str(img2): hash_val, str(img3): hash_val}
    groups = duplicate_finder.find_duplicates(hashes)
    # The original should be the highest resolution (200x200)
    originals = [g['original'] for g in groups]
    assert any(str(img2) == o for o in originals)

def test_original_tiebreak_by_file_size_and_path(tmp_path):
    # Two images, same resolution, different file size
    img1 = tmp_path / "a.jpg"
    img2 = tmp_path / "b.jpg"
    create_image(img1, (100, 100), color=(255, 0, 0))
    create_image(img2, (100, 100), color=(255, 0, 0))
    # Make img2 larger by appending bytes
    with open(img2, "ab") as f:
        f.write(b"extra")
    hash_val = image_processor.compute_hash(image_processor.load_image(str(img1)))
    hashes = {str(img1): hash_val, str(img2): hash_val}
    groups = duplicate_finder.find_duplicates(hashes)
    # img2 should be original (larger file size)
    assert groups[0]['original'] == str(img2)
    # Now make file sizes equal, should pick lex smallest path
    with open(img1, "ab") as f:
        f.write(b"extra")
    groups2 = duplicate_finder.find_duplicates(hashes)
    assert groups2[0]['original'] == min(str(img1), str(img2))

def test_group_details_and_blurred(tmp_path):
    # Create sharp and blurred images
    sharp = tmp_path / "sharp.jpg"
    blur = tmp_path / "blur.jpg"
    create_image(sharp, (100, 100))
    create_image(blur, (100, 100), blur=True)
    hash_val = image_processor.compute_hash(image_processor.load_image(str(sharp)))
    hashes = {str(sharp): hash_val, str(blur): hash_val}
    groups = duplicate_finder.find_duplicates(hashes)
    group = groups[0]
    # Details should include both
    assert 'details' in group
    assert str(blur) in group['details']
    assert 'hamming_distance' in group['details'][str(blur)]
    assert 'reason' in group['details'][str(blur)]
    # Blurred list should include blur.jpg
    assert str(blur) in group['blurred']
    # Thumbnails should be non-empty
    assert group['details'][str(blur)]['thumbnail'].startswith('data:image/jpeg;base64,')
    assert group['original_thumbnail'].startswith('data:image/jpeg;base64,')
    # Original_is_blurred should be False for sharp
    assert group['original_is_blurred'] is False

def test_find_duplicates_handles_corrupt_and_missing_metadata(tmp_path):
    # Create one good, one corrupt
    good = tmp_path / "good.jpg"
    corrupt = tmp_path / "corrupt.jpg"
    create_image(good, (100, 100))
    with open(corrupt, "wb") as f:
        f.write(b"")
    hash_val = image_processor.compute_hash(image_processor.load_image(str(good)))
    hashes = {str(good): hash_val, str(corrupt): hash_val}
    # Should not crash, should set thumbnail to "" for corrupt
    groups = duplicate_finder.find_duplicates(hashes)
    group = groups[0]
    assert group['details'][str(corrupt)]['thumbnail'] == ""
    assert group['details'][str(corrupt)]['resolution'] is None

def test_metadata_caching(tmp_path):
    # Create two images, same hash
    img1 = tmp_path / "img1.jpg"
    img2 = tmp_path / "img2.jpg"
    create_image(img1, (100, 100))
    create_image(img2, (100, 100))
    hash_val = image_processor.compute_hash(image_processor.load_image(str(img1)))
    hashes = {str(img1): hash_val, str(img2): hash_val}
    # Patch get_image_metadata to count calls
    call_count = {}
    orig_get_image_metadata = image_processor.get_image_metadata
    def counting_get_image_metadata(path, *a, **kw):
        call_count[path] = call_count.get(path, 0) + 1
        return orig_get_image_metadata(path, *a, **kw)
    with mock.patch('app.services.image_processor.get_image_metadata', side_effect=counting_get_image_metadata):
        duplicate_finder.find_duplicates(hashes)
    # Each file should be called only once
    assert call_count[str(img1)] == 1
    assert call_count[str(img2)] == 1
