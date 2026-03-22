import os
import json
from urllib.parse import quote_plus

import pytest
from PIL import Image


def test_preview_endpoint_returns_image(client, temp_dir):
    # Create a sample directory with one image and register scan
    sample_dir = os.path.join(temp_dir, "preview_photos")
    os.makedirs(sample_dir, exist_ok=True)
    img = Image.new("RGB", (640, 480), color="green")
    img_path = os.path.join(sample_dir, "test.jpg")
    img.save(img_path, format="JPEG")

    # Start a scan to register the directory
    resp = client.post("/api/scan", json={"directory": sample_dir})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "scan_id" in data

    # Request preview for relative path
    preview_resp = client.get(f"/api/preview?path={quote_plus('test.jpg')}")
    assert preview_resp.status_code == 200
    assert preview_resp.mimetype == "image/jpeg"
    # Body should be non-empty bytes
    assert preview_resp.data and len(preview_resp.data) > 0
