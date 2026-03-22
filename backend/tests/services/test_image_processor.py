"""Tests for image_processor module.

Comprehensive test suite for image loading, hashing, comparison, and
batch processing functions.
"""

import os
import pytest
from pathlib import Path
from PIL import Image

from app.services.image_processor import (
    load_image,
    compute_hash,
    compare_hashes,
    batch_compute_hashes,
)
from app.exceptions import (
    InvalidImageError,
    DirectoryNotFoundError,
    PermissionDeniedError,
)


class TestLoadImage:
    """Tests for load_image function."""

    def test_load_image_valid_jpeg(self, sample_jpeg: str) -> None:
        """Test loading a valid JPEG image."""
        image = load_image(sample_jpeg)
        assert image is not None
        assert image.format == "JPEG"
        assert image.size == (100, 100)
        assert image.mode == "RGB"

    def test_load_image_not_found(self) -> None:
        """Test loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_image("/nonexistent/path/image.jpg")

    def test_load_image_empty_file(self, empty_file: str) -> None:
        """Test loading empty file raises InvalidImageError."""
        with pytest.raises(InvalidImageError):
            load_image(empty_file)

    def test_load_image_corrupted(self, corrupted_jpeg: str) -> None:
        """Test loading corrupted JPEG raises InvalidImageError."""
        with pytest.raises(InvalidImageError):
            load_image(corrupted_jpeg)

    def test_load_image_is_directory(self, temp_dir: str) -> None:
        """Test loading a directory path raises InvalidImageError."""
        with pytest.raises(InvalidImageError):
            load_image(temp_dir)

    def test_load_image_returns_pil_image(self, sample_jpeg: str) -> None:
        """Test that returned object is a PIL Image."""
        image = load_image(sample_jpeg)
        assert isinstance(image, Image.Image)


class TestComputeHash:
    """Tests for compute_hash function."""

    def test_compute_hash_phash(self, sample_jpeg: str) -> None:
        """Test computing perceptual hash with phash."""
        image = load_image(sample_jpeg)
        hash_value = compute_hash(image, algorithm="phash")
        assert isinstance(hash_value, str)
        assert len(hash_value) == 16  # 8x8 hash = 64 bits = 16 hex chars
        # Should be valid hex
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_hash_dhash(self, sample_jpeg: str) -> None:
        """Test computing hash with dhash."""
        image = load_image(sample_jpeg)
        hash_value = compute_hash(image, algorithm="dhash")
        assert isinstance(hash_value, str)
        assert len(hash_value) == 16
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_compute_hash_invalid_algorithm(self, sample_jpeg: str) -> None:
        """Test invalid algorithm raises ValueError."""
        image = load_image(sample_jpeg)
        with pytest.raises(ValueError, match="Unknown algorithm"):
            compute_hash(image, algorithm="invalid")

    def test_compute_hash_consistency(self, sample_jpeg: str) -> None:
        """Test same image produces same hash."""
        image = load_image(sample_jpeg)
        hash1 = compute_hash(image)
        hash2 = compute_hash(image)
        assert hash1 == hash2

    def test_compute_hash_returns_string(self, sample_jpeg: str) -> None:
        """Test that hash is returned as string."""
        image = load_image(sample_jpeg)
        hash_value = compute_hash(image)
        assert isinstance(hash_value, str)


class TestCompareHashes:
    """Tests for compare_hashes function."""

    def test_compare_hashes_identical(self, sample_jpeg: str) -> None:
        """Test comparing identical hashes."""
        image = load_image(sample_jpeg)
        hash_value = compute_hash(image)
        is_dup, distance = compare_hashes(hash_value, hash_value)
        assert is_dup is True
        assert distance == 0

    def test_compare_hashes_different_images(
        self, sample_jpeg: str, sample_jpeg_different: str
    ) -> None:
        """Test comparing two different images.
        
        Note: Since both test images are solid colors at the same resolution,
        they may produce similar hashes. We just verify the comparison works.
        """
        img1 = load_image(sample_jpeg)
        img2 = load_image(sample_jpeg_different)
        hash1 = compute_hash(img1)
        hash2 = compute_hash(img2)
        is_dup, distance = compare_hashes(hash1, hash2, similarity_threshold=5)
        # Just verify the comparison produces a valid result
        assert isinstance(is_dup, bool)
        assert isinstance(distance, int)
        assert distance >= 0 and distance <= 64

    def test_compare_hashes_same_content(
        self, sample_jpeg: str, sample_jpeg_copy: str
    ) -> None:
        """Test comparing identical content images."""
        img1 = load_image(sample_jpeg)
        img2 = load_image(sample_jpeg_copy)
        hash1 = compute_hash(img1)
        hash2 = compute_hash(img2)
        is_dup, distance = compare_hashes(hash1, hash2, similarity_threshold=5)
        assert is_dup is True
        assert distance <= 5

    def test_compare_hashes_invalid_hash_format(self) -> None:
        """Test invalid hash format raises ValueError."""
        with pytest.raises(ValueError):
            compare_hashes("invalid", "invalid")

    def test_compare_hashes_empty_hashes(self) -> None:
        """Test empty hashes raise ValueError."""
        with pytest.raises(ValueError):
            compare_hashes("", "")

    def test_compare_hashes_returns_tuple(self, sample_jpeg: str) -> None:
        """Test that result is a tuple."""
        image = load_image(sample_jpeg)
        hash_value = compute_hash(image)
        result = compare_hashes(hash_value, hash_value)
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_compare_hashes_invalid_threshold(self, sample_jpeg: str) -> None:
        """Test invalid threshold raises ValueError."""
        image = load_image(sample_jpeg)
        hash_value = compute_hash(image)
        with pytest.raises(ValueError, match="Similarity threshold"):
            compare_hashes(hash_value, hash_value, similarity_threshold=-1)
        with pytest.raises(ValueError, match="Similarity threshold"):
            compare_hashes(hash_value, hash_value, similarity_threshold=65)

    def test_compare_hashes_custom_threshold(self, sample_jpeg: str) -> None:
        """Test custom similarity threshold."""
        image = load_image(sample_jpeg)
        hash_value = compute_hash(image)
        # With very strict threshold (0), only exact match
        is_dup, distance = compare_hashes(
            hash_value, hash_value, similarity_threshold=0
        )
        assert is_dup is True
        assert distance == 0


class TestBatchComputeHashes:
    """Tests for batch_compute_hashes function."""

    def test_batch_compute_hashes_directory_not_found(self) -> None:
        """Test non-existent directory raises DirectoryNotFoundError."""
        with pytest.raises(DirectoryNotFoundError):
            batch_compute_hashes("/nonexistent/directory")

    def test_batch_compute_hashes_empty_directory(self, temp_dir: str) -> None:
        """Test empty directory returns empty dict."""
        hashes = batch_compute_hashes(temp_dir)
        assert hashes == {}

    def test_batch_compute_hashes_valid_directory(
        self, photo_directory_with_jpegs: str
    ) -> None:
        """Test computing hashes for directory with JPEGs."""
        hashes = batch_compute_hashes(photo_directory_with_jpegs)
        assert len(hashes) == 5
        # All hashes should be strings
        assert all(isinstance(h, str) for h in hashes.values())
        # All hashes should be valid hex
        assert all(
            all(c in "0123456789abcdef" for c in h) for h in hashes.values()
        )

    def test_batch_compute_hashes_returns_dict(
        self, photo_directory_with_jpegs: str
    ) -> None:
        """Test that result is a dictionary."""
        hashes = batch_compute_hashes(photo_directory_with_jpegs)
        assert isinstance(hashes, dict)

    def test_batch_compute_hashes_keys_are_paths(
        self, photo_directory_with_jpegs: str
    ) -> None:
        """Test that dictionary keys are file paths."""
        hashes = batch_compute_hashes(photo_directory_with_jpegs)
        for file_path in hashes.keys():
            assert isinstance(file_path, str)
            assert file_path.endswith(".jpg")

    def test_batch_compute_hashes_skip_corrupted(
        self, photo_directory_with_jpegs: str, corrupted_jpeg: str
    ) -> None:
        """Test that corrupted files are skipped with skip_errors=True."""
        # Copy corrupted file to photo directory
        import shutil
        dest = os.path.join(photo_directory_with_jpegs, "corrupted.jpg")
        shutil.copy(corrupted_jpeg, dest)

        # Should skip corrupted file and return other 5
        hashes = batch_compute_hashes(photo_directory_with_jpegs, skip_errors=True)
        assert len(hashes) == 5
        assert dest not in hashes

    def test_batch_compute_hashes_fail_on_corrupted(
        self, photo_directory_with_jpegs: str, corrupted_jpeg: str
    ) -> None:
        """Test that corrupted files raise error with skip_errors=False."""
        # Copy corrupted file to photo directory
        import shutil
        dest = os.path.join(photo_directory_with_jpegs, "corrupted.jpg")
        shutil.copy(corrupted_jpeg, dest)

        # Should raise error
        with pytest.raises(InvalidImageError):
            batch_compute_hashes(photo_directory_with_jpegs, skip_errors=False)

    def test_batch_compute_hashes_recursive(self, temp_dir: str) -> None:
        """Test recursive directory scanning."""
        # Create nested directories with images
        subdir = os.path.join(temp_dir, "subdir")
        os.makedirs(subdir)

        # Create images at root and in subdirectory
        img1 = Image.new("RGB", (100, 100), color="red")
        img1.save(os.path.join(temp_dir, "img1.jpg"))

        img2 = Image.new("RGB", (100, 100), color="blue")
        img2.save(os.path.join(subdir, "img2.jpg"))

        # Non-recursive should find only 1
        hashes_non_recursive = batch_compute_hashes(temp_dir, recursive=False)
        assert len(hashes_non_recursive) == 1

        # Recursive should find both
        hashes_recursive = batch_compute_hashes(temp_dir, recursive=True)
        assert len(hashes_recursive) == 2

    def test_batch_compute_hashes_case_insensitive(self, temp_dir: str) -> None:
        """Test that .jpg and .jpeg extensions are found."""
        # Create .jpg and .jpeg files
        img1 = Image.new("RGB", (100, 100), color="red")
        img1.save(os.path.join(temp_dir, "img1.jpg"))
        img1.save(os.path.join(temp_dir, "img2.jpeg"))

        hashes = batch_compute_hashes(temp_dir)
        assert len(hashes) == 2

    def test_batch_compute_hashes_path_is_directory(self, temp_dir: str) -> None:
        """Test error when path is not a directory."""
        # Create a file instead of directory
        file_path = os.path.join(temp_dir, "file.txt")
        with open(file_path, "w") as f:
            f.write("test")

        with pytest.raises(DirectoryNotFoundError):
            batch_compute_hashes(file_path)


class TestImageProcessorIntegration:
    """Integration tests for image processor."""

    def test_full_workflow_single_image(self, sample_jpeg: str) -> None:
        """Test complete workflow: load -> hash -> compare."""
        img = load_image(sample_jpeg)
        hash1 = compute_hash(img)
        hash2 = compute_hash(img)
        is_dup, distance = compare_hashes(hash1, hash2)
        assert is_dup is True
        assert distance == 0

    def test_batch_and_individual_hashes_match(
        self, photo_directory_with_jpegs: str
    ) -> None:
        """Test that batch hashing matches individual hashing."""
        batch_hashes = batch_compute_hashes(photo_directory_with_jpegs)

        # Compute individual hashes
        individual_hashes = {}
        for file_path, batch_hash in batch_hashes.items():
            img = load_image(file_path)
            individual_hashes[file_path] = compute_hash(img)

        # Should match
        assert batch_hashes == individual_hashes

    def test_identical_images_same_hash(
        self, sample_jpeg: str, sample_jpeg_copy: str
    ) -> None:
        """Test that identical images produce same hash."""
        img1 = load_image(sample_jpeg)
        img2 = load_image(sample_jpeg_copy)
        hash1 = compute_hash(img1)
        hash2 = compute_hash(img2)
        assert hash1 == hash2

# --- Additional tests for blur, thumbnail, metadata, edge cases ---
import io
import base64
import pytest
from PIL import Image, ImageFilter
from app.services import image_processor

def create_sharp_image(size=(100, 100), color=(255, 255, 255)):
    img = Image.new("RGB", size, color)
    for x in range(10, 90):
        for y in range(10, 90):
            img.putpixel((x, y), (0, 0, 0))
    return img

def create_blurred_image(size=(100, 100)):
    img = create_sharp_image(size)
    return img.filter(ImageFilter.GaussianBlur(radius=8))

def test_compute_blur_score_and_is_blurred():
    sharp = create_sharp_image()
    blurred = create_blurred_image()
    sharp_score = image_processor.compute_blur_score(sharp)
    blurred_score = image_processor.compute_blur_score(blurred)
    assert sharp_score > blurred_score
    # Default threshold
    is_blur_sharp, score_sharp = image_processor.is_blurred(sharp)
    is_blur_blur, score_blur = image_processor.is_blurred(blurred)
    assert not is_blur_sharp
    assert is_blur_blur
    # Custom threshold (force all to blurred)
    is_blur_custom, _ = image_processor.is_blurred(sharp, threshold=1e6)
    assert is_blur_custom

def test_generate_thumbnail_base64_valid_jpeg():
    img = create_sharp_image()
    data_uri = image_processor.generate_thumbnail_base64(img, size=(50, 50))
    assert data_uri.startswith('data:image/jpeg;base64,')
    b64 = data_uri.split(',', 1)[1]
    jpeg_bytes = base64.b64decode(b64)
    # Should be decodable by PIL
    thumb = Image.open(io.BytesIO(jpeg_bytes))
    assert thumb.format == 'JPEG'
    assert thumb.size[0] <= 50 and thumb.size[1] <= 50

def test_get_image_metadata_fields(tmp_path):
    img = create_sharp_image((80, 60))
    file_path = tmp_path / "sharp.jpg"
    img.save(file_path, format="JPEG")
    meta = image_processor.get_image_metadata(str(file_path))
    assert meta["resolution"] == (80, 60)
    assert meta["file_size_bytes"] > 0
    assert isinstance(meta["is_blurred"], bool)
    assert isinstance(meta["blur_score"], float)
    assert meta["thumbnail"].startswith('data:image/jpeg;base64,')
    assert meta["format"] == 'JPEG'

def test_get_image_metadata_config_override(tmp_path):
    img = create_sharp_image((120, 80))
    file_path = tmp_path / "sharp2.jpg"
    img.save(file_path, format="JPEG")
    config = {"THUMBNAIL_SIZE": (32, 32), "BLUR_THRESHOLD": 0.1}
    meta = image_processor.get_image_metadata(str(file_path), app_config=config)
    assert meta["thumbnail"].startswith('data:image/jpeg;base64,')
    assert meta["is_blurred"] is False  # Should not be blurred at very low threshold
    # Thumbnail should be small
    b64 = meta["thumbnail"].split(',', 1)[1]
    thumb = Image.open(io.BytesIO(base64.b64decode(b64)))
    assert thumb.size[0] <= 32 and thumb.size[1] <= 32

def test_get_image_metadata_corrupt_file(tmp_path):
    file_path = tmp_path / "corrupt.jpg"
    with open(file_path, "wb") as f:
        f.write(b"not an image")
    meta = image_processor.get_image_metadata(str(file_path))
    assert meta["thumbnail"] == ""
    assert meta["resolution"] is None
    assert meta["is_blurred"] is False
    assert meta["blur_score"] is None
