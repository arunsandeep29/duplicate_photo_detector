"""Comprehensive integration tests for API endpoints."""

import json
import os
from unittest.mock import MagicMock


class TestScanEndpointIntegration:
    """Integration tests for POST /api/scan endpoint."""

    def test_scan_with_permission_denied(self, client, monkeypatch):
        """Test scan with permission denied error."""

        def mock_validate(*args, **kwargs):
            from app.exceptions import PermissionDeniedError

            raise PermissionDeniedError("/restricted", "read")

        monkeypatch.setattr("app.api.routes.validate_directory_path", mock_validate)

        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": "/restricted"}),
            content_type="application/json",
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["code"] == "PERMISSION_DENIED"

    def test_scan_with_unexpected_error(self, client, monkeypatch):
        """Test scan with unexpected error during processing."""

        def mock_hash_error(*args, **kwargs):
            raise RuntimeError("Unexpected processing error")

        monkeypatch.setattr("app.api.routes.batch_compute_hashes", mock_hash_error)

        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": "/tmp"}),
            content_type="application/json",
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["code"] == "INTERNAL_ERROR"

    def test_scan_with_invalid_groups(self, client, monkeypatch, sample_directory):
        """Test scan when duplicate finder returns invalid groups."""
        # Mock validate_groups to return False
        mock_validate = MagicMock(return_value=False)
        monkeypatch.setattr("app.api.routes.validate_groups", mock_validate)

        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data["code"] == "INTERNAL_ERROR"
        assert "Invalid duplicate groups" in data["error"]


class TestDuplicatesEndpointIntegration:
    """Integration tests for GET /api/duplicates/{scan_id} endpoint."""

    def test_duplicates_with_nonexistent_scan(self, client):
        """Test retrieving duplicates for non-existent scan."""
        response = client.get("/api/duplicates/scan-nonexistent")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["code"] == "SCAN_NOT_FOUND"

    def test_duplicates_endpoint_with_valid_scan_stores_and_retrieves(
        self, client, sample_directory
    ):
        """Test that scan stores data that can be retrieved."""
        # First, do a scan
        scan_response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        assert scan_response.status_code == 200
        scan_data = json.loads(scan_response.data)
        scan_id = scan_data["scan_id"]

        # Then retrieve the duplicates
        dup_response = client.get(f"/api/duplicates/{scan_id}")
        assert dup_response.status_code == 200
        dup_data = json.loads(dup_response.data)
        assert "groups" in dup_data
        assert isinstance(dup_data["groups"], list)


class TestMoveDuplicatesEndpointIntegration:
    """Integration tests for POST /api/move-duplicates endpoint."""

    def test_move_with_permission_denied(self, client, monkeypatch, temp_dir):
        """Test move with permission denied error."""
        archive_dir = os.path.join(temp_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        # Create a source file
        source_file = os.path.join(temp_dir, "test.jpg")
        with open(source_file, "w") as f:
            f.write("test")

        def mock_execute_move(*args, **kwargs):
            return {
                "moved_count": 0,
                "deleted_count": 0,
                "failed_count": 1,
                "errors": [{"file": "test.jpg", "reason": "Permission denied"}],
            }

        monkeypatch.setattr(
            "app.api.routes.execute_move_operations",
            mock_execute_move,
        )

        payload = {
            "scan_id": "scan-123",
            "destination": archive_dir,
            "operations": [
                {
                    "original": "photo1.jpg",
                    "target_copy": source_file,
                    "action": "move",
                }
            ],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["failed_count"] == 1

    def test_move_with_invalid_destination_directory(self, client, sample_directory):
        """Test move with invalid destination directory."""
        payload = {
            "scan_id": "scan-123",
            "destination": "/nonexistent/archive/path",
            "operations": [
                {
                    "original": "photo1.jpg",
                    "target_copy": "photo1_copy.jpg",
                    "action": "move",
                }
            ],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid destination" in data["error"]

    def test_move_with_all_failed_operations(self, client, temp_dir):
        """Test move operations where all operations fail."""
        archive_dir = os.path.join(temp_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        payload = {
            "scan_id": "scan-123",
            "destination": archive_dir,
            "operations": [
                {
                    "original": "photo1.jpg",
                    "target_copy": "/nonexistent/photo1_copy.jpg",
                    "action": "move",
                }
            ],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["failed_count"] == 1
        assert len(data["errors"]) == 1


class TestErrorHandlingIntegration:
    """Integration tests for error handling across endpoints."""

    def test_malformed_json_returns_400(self, client):
        """Test that malformed JSON returns 400."""
        response = client.post("/api/scan", data="{invalid json}", content_type="application/json")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["code"] == "INVALID_REQUEST"

    def test_post_without_content_type_handles_gracefully(self, client):
        """Test POST without Content-Type header handles gracefully."""
        response = client.post("/api/scan", data=json.dumps({"directory": "/tmp"}))
        # Should still work - Flask will parse JSON anyway
        assert response.status_code in [200, 400, 404]

    def test_get_request_to_post_endpoint_returns_405(self, client):
        """Test GET request to POST-only endpoint returns 405."""
        response = client.get("/api/scan")
        assert response.status_code == 405

    def test_post_request_to_get_endpoint_returns_405(self, client):
        """Test POST request to GET-only endpoint returns 405."""
        response = client.post("/api/health")
        assert response.status_code == 405


class TestDataValidationIntegration:
    """Integration tests for request data validation."""

    def test_scan_with_whitespace_only_directory(self, client):
        """Test scan with whitespace-only directory parameter."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": "   "}),
            content_type="application/json",
        )
        # Should fail validation
        assert response.status_code in [400, 404]

    def test_move_with_invalid_action_type(self, client, temp_dir):
        """Test move operations with invalid action type."""
        archive_dir = os.path.join(temp_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        payload = {
            "scan_id": "scan-123",
            "destination": archive_dir,
            "operations": [
                {
                    "original": "photo1.jpg",
                    "target_copy": "photo1_copy.jpg",
                    "action": "copy",  # Invalid: should be "move" or "delete"
                }
            ],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Action must be" in data["error"]

    def test_move_with_missing_required_operation_fields(self, client, temp_dir):
        """Test move with missing required fields in operation object."""
        archive_dir = os.path.join(temp_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        payload = {
            "scan_id": "scan-123",
            "destination": archive_dir,
            "operations": [
                {
                    "original": "photo1.jpg",
                    # Missing target_copy and action
                }
            ],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "operation must have" in data["error"]


class TestHealthEndpointIntegration:
    """Integration tests for health check endpoint."""

    def test_health_endpoint_always_available(self, client):
        """Test that health endpoint is always available."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.content_type == "application/json"

    def test_health_endpoint_response_structure(self, client):
        """Test health endpoint response structure."""
        response = client.get("/api/health")
        data = json.loads(response.data)
        assert "status" in data
        assert data["status"] == "ok"
        assert isinstance(data, dict)
        assert len(data) == 1  # Should only have status field


class TestScanStorageIntegration:
    """Integration tests for scan storage and retrieval."""

    def test_multiple_scans_stored_independently(self, client, sample_directory, temp_dir):
        """Test that multiple scans are stored independently."""
        from PIL import Image

        # Create two different directories
        dir2 = os.path.join(temp_dir, "dir2")
        os.makedirs(dir2, exist_ok=True)

        for i in range(3):
            img = Image.new("RGB", (100, 100), color=(i * 80, i * 80, i * 80))
            img.save(os.path.join(dir2, f"photo{i}.jpg"), "JPEG")

        # Scan first directory
        resp1 = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        scan_id1 = json.loads(resp1.data)["scan_id"]

        # Scan second directory
        resp2 = client.post(
            "/api/scan",
            data=json.dumps({"directory": dir2}),
            content_type="application/json",
        )
        scan_id2 = json.loads(resp2.data)["scan_id"]

        # Verify both scans can be retrieved independently
        dup1 = client.get(f"/api/duplicates/{scan_id1}")
        dup2 = client.get(f"/api/duplicates/{scan_id2}")

        assert dup1.status_code == 200
        assert dup2.status_code == 200

        # Scan IDs should be different
        assert scan_id1 != scan_id2

    def test_scan_id_format_is_consistent(self, client, sample_directory):
        """Test that scan IDs follow expected format."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        scan_id = data["scan_id"]

        # Should start with "scan-" and be alphanumeric
        assert scan_id.startswith("scan-")
        assert len(scan_id) > 5
        # Check format: scan-[hex]
        parts = scan_id.split("-")
        assert len(parts) == 2
        assert parts[0] == "scan"
