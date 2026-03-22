import os
from pathlib import Path
import pytest
from PIL import Image

from app.services.image_processor import (
    compute_quality_score,
    compute_sharpness,
)


def test_quality_score_prefers_resolution(tmp_path):
    # Create two images with different resolutions
    img_small = Image.new("RGB", (100, 100), color="white")
    img_large = Image.new("RGB", (400, 300), color="white")

    small_path = tmp_path / "small.jpg"
    large_path = tmp_path / "large.jpg"
    img_small.save(small_path, format="JPEG")
    img_large.save(large_path, format="JPEG")

    # File sizes
    size_small = small_path.stat().st_size
    size_large = large_path.stat().st_size

    # Sharpness (should be similar)
    sharp_small = compute_sharpness(img_small)
    sharp_large = compute_sharpness(img_large)

    score_small = compute_quality_score(
        image=None, resolution=(100, 100), file_size_bytes=size_small, sharpness=sharp_small
    )
    score_large = compute_quality_score(
        image=None, resolution=(400, 300), file_size_bytes=size_large, sharpness=sharp_large
    )

    assert isinstance(score_small, float)
    assert isinstance(score_large, float)
    assert score_large > score_small


def test_quality_score_handles_corrupted_file():
    # Corrupted/missing metrics should still produce a numeric score (fallback)
    score = compute_quality_score(image=None, resolution=None, file_size_bytes=None, sharpness=None)
    assert isinstance(score, float)
    assert score >= 0.0
