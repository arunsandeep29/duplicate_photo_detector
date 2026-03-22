"""Tests for API endpoints."""

import json

import pytest


class TestHealthEndpoint:
    """Tests for GET /api/health endpoint."""

    def test_health_check_returns_200(self, client):
        """Test that health check endpoint returns 200 status code."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_check_returns_ok_status(self, client):
        """Test that health check returns correct response format."""
        response = client.get("/api/health")
        data = json.loads(response.data)
        assert data["status"] == "ok"

    def test_health_check_response_is_json(self, client):
        """Test that health check response is JSON."""
        response = client.get("/api/health")
        assert response.content_type == "application/json"


class TestScanEndpoint:
    """Tests for POST /api/scan endpoint."""

    def test_scan_with_valid_directory_returns_200(self, client, sample_directory):
        """Test scan with valid directory returns 200."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_scan_with_valid_directory_returns_scan_id(self, client, sample_directory):
        """Test scan response contains scan_id."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert "scan_id" in data
        assert data["scan_id"].startswith("scan-")

    def test_scan_with_valid_directory_returns_image_count(self, client, sample_directory):
        """Test scan response contains image_count."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert "image_count" in data
        assert isinstance(data["image_count"], int)
        assert data["image_count"] >= 0

    def test_scan_with_invalid_directory_returns_400(self, client):
        """Test scan with invalid directory returns 400."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": "/nonexistent/path"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_with_invalid_directory_error_format(self, client):
        """Test error response format for invalid directory."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": "/nonexistent/path"}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert "error" in data
        assert "code" in data
        assert data["code"] == "INVALID_REQUEST"

    def test_scan_with_missing_directory_field_returns_400(self, client):
        """Test scan with missing directory field returns 400."""
        response = client.post(
            "/api/scan",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_with_missing_directory_field_error_message(self, client):
        """Test error message for missing directory field."""
        response = client.post(
            "/api/scan",
            data=json.dumps({}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        # Empty object is treated as missing JSON body
        assert "error" in data and data["code"] == "INVALID_REQUEST"

    def test_scan_with_null_directory_returns_400(self, client):
        """Test scan with null directory returns 400."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": None}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_with_empty_body_returns_400(self, client):
        """Test scan with empty body returns 400."""
        response = client.post(
            "/api/scan",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_scan_response_is_json(self, client, sample_directory):
        """Test scan response is JSON."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        assert response.content_type == "application/json"


class TestDuplicatesEndpoint:
    """Tests for GET /api/duplicates/<scan_id> endpoint."""

    def test_duplicates_with_valid_scan_id_returns_200(self, client, sample_directory):
        """Test get duplicates with valid scan_id returns 200."""
        # First, create a scan
        scan_response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        scan_data = json.loads(scan_response.data)
        scan_id = scan_data["scan_id"]

        # Then get duplicates
        response = client.get(f"/api/duplicates/{scan_id}")
        assert response.status_code == 200

    def test_duplicates_with_valid_scan_id_returns_groups(self, client, sample_directory):
        """Test duplicates response contains groups."""
        # First, create a scan
        scan_response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        scan_data = json.loads(scan_response.data)
        scan_id = scan_data["scan_id"]

        # Then get duplicates
        response = client.get(f"/api/duplicates/{scan_id}")
        data = json.loads(response.data)
        assert "groups" in data
        assert isinstance(data["groups"], list)

    def test_duplicates_with_invalid_scan_id_returns_404(self, client):
        """Test get duplicates with invalid scan_id returns 404."""
        response = client.get("/api/duplicates/invalid-scan-id")
        assert response.status_code == 404

    def test_duplicates_with_invalid_scan_id_error_code(self, client):
        """Test error code for invalid scan_id."""
        response = client.get("/api/duplicates/invalid-scan-id")
        data = json.loads(response.data)
        assert data["code"] == "SCAN_NOT_FOUND"

    def test_duplicates_response_is_json(self, client, sample_directory):
        """Test duplicates response is JSON."""
        # First, create a scan
        scan_response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        scan_data = json.loads(scan_response.data)
        scan_id = scan_data["scan_id"]

        # Then get duplicates
        response = client.get(f"/api/duplicates/{scan_id}")
        assert response.content_type == "application/json"

    def test_duplicates_groups_have_expected_fields(self, client, sample_directory):
        """Test that group objects have expected fields."""
        # First, create a scan
        scan_response = client.post(
            "/api/scan",
            data=json.dumps({"directory": sample_directory}),
            content_type="application/json",
        )
        scan_data = json.loads(scan_response.data)
        scan_id = scan_data["scan_id"]

        # Then get duplicates
        response = client.get(f"/api/duplicates/{scan_id}")
        data = json.loads(response.data)

        if data["groups"]:
            group = data["groups"][0]
            assert "hash" in group
            assert "original" in group
            assert "copies" in group


class TestMoveDuplicatesEndpoint:
    """Tests for POST /api/move-duplicates endpoint."""

    def test_move_duplicates_with_valid_data_returns_200(self, client, temp_dir):
        """Test move duplicates with valid data returns 200."""
        import os

        archive_dir = os.path.join(temp_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        payload = {
            "scan_id": "scan-123",
            "destination": archive_dir,
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
        assert response.status_code == 200

    def test_move_duplicates_response_format(self, client, temp_dir):
        """Test move duplicates response has correct format."""
        import os

        archive_dir = os.path.join(temp_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        payload = {
            "scan_id": "scan-123",
            "destination": archive_dir,
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
        data = json.loads(response.data)
        assert "moved_count" in data
        assert "failed_count" in data
        assert "errors" in data

    def test_move_duplicates_missing_scan_id_returns_400(self, client):
        """Test move duplicates without scan_id returns 400."""
        payload = {
            "destination": "/archive",
            "operations": [],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_move_duplicates_missing_destination_returns_400(self, client):
        """Test move duplicates without destination returns 400."""
        payload = {
            "scan_id": "scan-123",
            "operations": [],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_move_duplicates_missing_operations_returns_400(self, client):
        """Test move duplicates without operations returns 400."""
        payload = {
            "scan_id": "scan-123",
            "destination": "/archive",
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_move_duplicates_invalid_operations_format_returns_400(self, client):
        """Test move duplicates with non-list operations returns 400."""
        payload = {
            "scan_id": "scan-123",
            "destination": "/archive",
            "operations": "not a list",
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_move_duplicates_operation_missing_fields_returns_400(self, client):
        """Test operation without required fields returns 400."""
        payload = {
            "scan_id": "scan-123",
            "destination": "/archive",
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

    def test_move_duplicates_invalid_action_returns_400(self, client):
        """Test operation with invalid action returns 400."""
        payload = {
            "scan_id": "scan-123",
            "destination": "/archive",
            "operations": [
                {
                    "original": "photo1.jpg",
                    "target_copy": "photo1_copy.jpg",
                    "action": "invalid_action",
                }
            ],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_move_duplicates_response_is_json(self, client):
        """Test move duplicates response is JSON."""
        payload = {
            "scan_id": "scan-123",
            "destination": "/archive",
            "operations": [],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        # Even if it fails validation, response should be JSON
        assert response.content_type == "application/json"

    def test_move_duplicates_empty_body_returns_400(self, client):
        """Test move duplicates with empty body returns 400."""
        response = client.post(
            "/api/move-duplicates",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_move_duplicates_multiple_operations(self, client, temp_dir):
        """Test move duplicates with multiple operations."""
        import os

        archive_dir = os.path.join(temp_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        # Create actual source files to move/delete
        source_file1 = os.path.join(temp_dir, "photo1_copy.jpg")
        source_file2 = os.path.join(temp_dir, "photo2_dup.jpg")
        with open(source_file1, "w") as f:
            f.write("test")
        with open(source_file2, "w") as f:
            f.write("test")

        payload = {
            "scan_id": "scan-123",
            "destination": archive_dir,
            "operations": [
                {
                    "original": "photo1.jpg",
                    "target_copy": source_file1,
                    "action": "move",
                },
                {
                    "original": "photo2.jpg",
                    "target_copy": source_file2,
                    "action": "delete",
                },
            ],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["moved_count"] == 1

    def test_move_duplicates_counts_correct_actions(self, client, temp_dir):
        """Test that move and delete operations are counted correctly."""
        import os

        archive_dir = os.path.join(temp_dir, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        # Create actual source files to move/delete
        source_file1 = os.path.join(temp_dir, "photo1_copy.jpg")
        source_file2 = os.path.join(temp_dir, "photo2_dup.jpg")
        source_file3 = os.path.join(temp_dir, "photo3_dup.jpg")
        with open(source_file1, "w") as f:
            f.write("test")
        with open(source_file2, "w") as f:
            f.write("test")
        with open(source_file3, "w") as f:
            f.write("test")

        payload = {
            "scan_id": "scan-123",
            "destination": archive_dir,
            "operations": [
                {
                    "original": "photo1.jpg",
                    "target_copy": source_file1,
                    "action": "move",
                },
                {
                    "original": "photo2.jpg",
                    "target_copy": source_file2,
                    "action": "move",
                },
                {
                    "original": "photo3.jpg",
                    "target_copy": source_file3,
                    "action": "delete",
                },
            ],
        }
        response = client.post(
            "/api/move-duplicates",
            data=json.dumps(payload),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert data["moved_count"] == 2


class TestErrorResponseFormat:
    """Tests for error response format consistency."""

    def test_error_response_has_error_field(self, client):
        """Test that error responses have error field."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": "/nonexistent"}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert "error" in data

    def test_error_response_has_code_field(self, client):
        """Test that error responses have code field."""
        response = client.post(
            "/api/scan",
            data=json.dumps({"directory": "/nonexistent"}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert "code" in data

    def test_error_code_is_string(self, client):
        """Test that error code is a string."""
        response = client.post(
            "/api/scan",
            data=json.dumps({}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert isinstance(data["code"], str)

    def test_not_found_endpoint_returns_404(self, client):
        """Test that non-existent endpoints return 404."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_method_not_allowed_returns_405(self, client, sample_directory):
        """Test that wrong HTTP method returns 405 or appropriate error."""
        response = client.post("/api/health")
        assert response.status_code != 200


class TestValidators:
    """Tests for validator functions."""

    def test_validate_directory_path_with_valid_path(self, sample_directory):
        """Test validate_directory_path with valid path."""
        from app.utils.validators import validate_directory_path

        assert validate_directory_path(sample_directory) is True

    def test_validate_directory_path_with_nonexistent_path(self):
        """Test validate_directory_path with nonexistent path."""
        from app.utils.validators import validate_directory_path

        with pytest.raises(ValueError):
            validate_directory_path("/nonexistent/path")

    def test_validate_directory_path_with_empty_string(self):
        """Test validate_directory_path with empty string."""
        from app.utils.validators import validate_directory_path

        with pytest.raises(ValueError):
            validate_directory_path("")

    def test_validate_scan_id_with_valid_format(self):
        """Test validate_scan_id with valid format."""
        from app.utils.validators import validate_scan_id

        assert validate_scan_id("scan-123abc") is True

    def test_validate_scan_id_with_hyphens(self):
        """Test validate_scan_id with hyphens."""
        from app.utils.validators import validate_scan_id

        assert validate_scan_id("scan-123-abc") is True

    def test_validate_scan_id_with_invalid_characters(self):
        """Test validate_scan_id with invalid characters."""
        from app.utils.validators import validate_scan_id

        with pytest.raises(ValueError):
            validate_scan_id("scan_123")

    def test_validate_image_format_with_jpg(self):
        """Test validate_image_format with jpg file."""
        from app.utils.validators import validate_image_format

        assert validate_image_format("photo.jpg") is True

    def test_validate_image_format_with_png(self):
        """Test validate_image_format with png file."""
        from app.utils.validators import validate_image_format

        assert validate_image_format("photo.png") is True

    def test_validate_image_format_with_invalid_extension(self):
        """Test validate_image_format with invalid extension."""
        from app.utils.validators import validate_image_format

        with pytest.raises(ValueError):
            validate_image_format("photo.txt")

    def test_validate_image_format_with_no_extension(self):
        """Test validate_image_format with no extension."""
        from app.utils.validators import validate_image_format

        with pytest.raises(ValueError):
            validate_image_format("photo")

    def test_validate_image_format_with_mime_type(self):
        """Test validate_image_format with mime type."""
        from app.utils.validators import validate_image_format

        assert validate_image_format("photo.jpg", "image/jpeg") is True

    def test_validate_image_format_with_invalid_mime_type(self):
        """Test validate_image_format with invalid mime type."""
        from app.utils.validators import validate_image_format

        with pytest.raises(ValueError):
            validate_image_format("photo.jpg", "text/plain")


class TestExceptions:
    """Tests for custom exception classes."""

    def test_duplicate_photos_error_to_dict(self):
        """Test DuplicatePhotosError to_dict method."""
        from app.exceptions import DuplicatePhotosError

        error = DuplicatePhotosError("Test error", "TEST_CODE", "Test details")
        result = error.to_dict()
        assert result["error"] == "Test error"
        assert result["code"] == "TEST_CODE"
        assert result["details"] == "Test details"

    def test_duplicate_photos_error_to_dict_no_details(self):
        """Test DuplicatePhotosError to_dict without details."""
        from app.exceptions import DuplicatePhotosError

        error = DuplicatePhotosError("Test error", "TEST_CODE")
        result = error.to_dict()
        assert "details" not in result

    def test_directory_not_found_error(self):
        """Test DirectoryNotFoundError."""
        from app.exceptions import DirectoryNotFoundError

        error = DirectoryNotFoundError("/path/to/dir")
        assert error.code == "DIRECTORY_NOT_FOUND"
        assert "/path/to/dir" in error.message

    def test_invalid_image_error(self):
        """Test InvalidImageError."""
        from app.exceptions import InvalidImageError

        error = InvalidImageError("photo.txt", "unsupported format")
        assert error.code == "INVALID_IMAGE"
        assert "photo.txt" in error.message

    def test_permission_denied_error(self):
        """Test PermissionDeniedError."""
        from app.exceptions import PermissionDeniedError

        error = PermissionDeniedError("/path", "read")
        assert error.code == "PERMISSION_DENIED"
        assert "/path" in error.message

    def test_scan_not_found_error(self):
        """Test ScanNotFoundError."""
        from app.exceptions import ScanNotFoundError

        error = ScanNotFoundError("scan-123")
        assert error.code == "SCAN_NOT_FOUND"
        assert "scan-123" in error.message

    def test_invalid_operation_error(self):
        """Test InvalidOperationError."""
        from app.exceptions import InvalidOperationError

        error = InvalidOperationError("delete", "file locked")
        assert error.code == "INVALID_OPERATION"
        assert "delete" in error.message
