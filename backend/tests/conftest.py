"""Test configuration and fixtures."""

import os
import tempfile
from typing import Generator

import pytest
from PIL import Image

from app import create_app
from app.config import TestingConfig


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing.

    Yields:
        str: Path to temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def app(temp_dir):
    """Create Flask application for testing.

    Args:
        temp_dir: Temporary directory fixture.

    Yields:
        Flask: Configured test application.
    """
    # Create test config with temp directory
    config = TestingConfig()
    config.UPLOAD_DIR = temp_dir
    config.TEMP_DIR = temp_dir
    config.SCANS_DIR = temp_dir

    app = create_app(config)

    yield app


@pytest.fixture
def client(app):
    """Create test client for Flask application.

    Args:
        app: Flask application fixture.

    Returns:
        FlaskClient: Test client for making requests.
    """
    return app.test_client()


@pytest.fixture
def sample_directory(temp_dir) -> str:
    """Create a sample directory structure for testing.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        str: Path to sample directory.
    """
    # Create sample directory
    sample_dir = os.path.join(temp_dir, "sample_photos")
    os.makedirs(sample_dir, exist_ok=True)

    # Create 5 actual JPEG image files
    for i in range(5):
        image = Image.new("RGB", (100, 100), color=(i * 50, i * 50, i * 50))
        file_path = os.path.join(sample_dir, f"photo{i}.jpg")
        image.save(file_path, "JPEG")

    return sample_dir


@pytest.fixture
def sample_jpeg(temp_dir: str) -> str:
    """Create a sample JPEG image for testing.

    Creates a simple 100x100 RGB JPEG image.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        str: Path to created JPEG file.
    """
    image = Image.new("RGB", (100, 100), color="red")
    file_path = os.path.join(temp_dir, "sample.jpg")
    image.save(file_path, "JPEG")
    return file_path


@pytest.fixture
def sample_jpeg_copy(temp_dir: str, sample_jpeg: str) -> str:
    """Create a copy of a sample JPEG image.

    Creates an identical copy of the sample JPEG.

    Args:
        temp_dir: Temporary directory fixture.
        sample_jpeg: Path to source JPEG.

    Returns:
        str: Path to created JPEG copy.
    """
    image = Image.open(sample_jpeg)
    file_path = os.path.join(temp_dir, "sample_copy.jpg")
    image.save(file_path, "JPEG")
    return file_path


@pytest.fixture
def sample_jpeg_modified(temp_dir: str) -> str:
    """Create a slightly modified JPEG image.

    Creates an image with same content but different compression,
    which should produce a similar but not identical hash.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        str: Path to created JPEG file.
    """
    image = Image.new("RGB", (100, 100), color="red")
    file_path = os.path.join(temp_dir, "sample_modified.jpg")
    # Save with different quality to change hash slightly
    image.save(file_path, "JPEG", quality=50)
    return file_path


@pytest.fixture
def sample_jpeg_different(temp_dir: str) -> str:
    """Create a completely different JPEG image.

    Creates a different image that should produce a very different hash.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        str: Path to created JPEG file.
    """
    image = Image.new("RGB", (100, 100), color="blue")
    file_path = os.path.join(temp_dir, "sample_different.jpg")
    image.save(file_path, "JPEG")
    return file_path


@pytest.fixture
def corrupted_jpeg(temp_dir: str) -> str:
    """Create a corrupted JPEG file (invalid image data).

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        str: Path to corrupted JPEG file.
    """
    file_path = os.path.join(temp_dir, "corrupted.jpg")
    with open(file_path, "wb") as f:
        # Write JPEG header but corrupt data
        f.write(b"\xff\xd8\xff\xe0")
        f.write(b"\x00" * 100)
        f.write(b"\xff\xd9")  # JPEG end marker
    return file_path


@pytest.fixture
def empty_file(temp_dir: str) -> str:
    """Create an empty file.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        str: Path to empty file.
    """
    file_path = os.path.join(temp_dir, "empty.jpg")
    with open(file_path, "wb"):
        pass
    return file_path


@pytest.fixture
def photo_directory_with_jpegs(temp_dir: str) -> str:
    """Create a directory with multiple JPEG images.

    Creates 5 JPEG images with various similarities for testing
    batch operations and duplicate detection.

    Args:
        temp_dir: Temporary directory fixture.

    Returns:
        str: Path to directory containing JPEGs.
    """
    photo_dir = os.path.join(temp_dir, "photos")
    os.makedirs(photo_dir, exist_ok=True)

    # Create 5 images
    for i in range(5):
        image = Image.new("RGB", (100, 100), color=(i * 50, i * 50, i * 50))
        file_path = os.path.join(photo_dir, f"photo{i}.jpg")
        image.save(file_path, "JPEG")

    return photo_dir
