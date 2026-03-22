"""Tests for file_manager module.

Comprehensive test suite for file operations, validation, and safety.
"""

import os
import pytest
from pathlib import Path

from app.services.file_manager import (
    move_file,
    validate_destination,
    execute_move_operations,
)
from app.exceptions import PermissionDeniedError, InvalidOperationError


class TestMoveFile:
    """Tests for move_file function."""

    def test_move_file_success(self, temp_dir: str) -> None:
        """Test successful file move."""
        # Create source file
        src = os.path.join(temp_dir, "source.txt")
        with open(src, "w") as f:
            f.write("test content")

        # Move to destination
        dest = os.path.join(temp_dir, "destination.txt")
        result = move_file(src, dest)

        assert result is True
        assert os.path.exists(dest)
        assert not os.path.exists(src)  # Source should be gone
        with open(dest, "r") as f:
            assert f.read() == "test content"

    def test_move_file_to_directory(self, temp_dir: str) -> None:
        """Test moving file into a directory."""
        # Create source file
        src = os.path.join(temp_dir, "source.txt")
        with open(src, "w") as f:
            f.write("test")

        # Create destination directory
        dest_dir = os.path.join(temp_dir, "subdir")
        os.makedirs(dest_dir)

        # Move into directory
        result = move_file(src, dest_dir)

        assert result is True
        # File should be in directory with same name
        expected_dest = os.path.join(dest_dir, "source.txt")
        assert os.path.exists(expected_dest)
        assert not os.path.exists(src)

    def test_move_file_not_found(self, temp_dir: str) -> None:
        """Test moving non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            move_file("/nonexistent/file.txt", os.path.join(temp_dir, "dest.txt"))

    def test_move_file_destination_exists_no_overwrite(self, temp_dir: str) -> None:
        """Test moving to existing destination without overwrite raises error."""
        # Create files
        src = os.path.join(temp_dir, "source.txt")
        dest = os.path.join(temp_dir, "dest.txt")
        with open(src, "w") as f:
            f.write("source")
        with open(dest, "w") as f:
            f.write("existing")

        with pytest.raises(FileExistsError):
            move_file(src, dest, overwrite=False)

    def test_move_file_destination_exists_with_overwrite(self, temp_dir: str) -> None:
        """Test moving with overwrite=True replaces destination."""
        # Create files
        src = os.path.join(temp_dir, "source.txt")
        dest = os.path.join(temp_dir, "dest.txt")
        with open(src, "w") as f:
            f.write("source")
        with open(dest, "w") as f:
            f.write("existing")

        result = move_file(src, dest, overwrite=True)

        assert result is True
        assert os.path.exists(dest)
        with open(dest, "r") as f:
            assert f.read() == "source"
        assert not os.path.exists(src)

    def test_move_file_same_source_and_dest(self, temp_dir: str) -> None:
        """Test moving file to itself raises InvalidOperationError."""
        src = os.path.join(temp_dir, "file.txt")
        with open(src, "w") as f:
            f.write("test")

        with pytest.raises(InvalidOperationError):
            move_file(src, src)

    def test_move_file_is_directory(self, temp_dir: str) -> None:
        """Test moving a directory raises InvalidOperationError."""
        src_dir = os.path.join(temp_dir, "source_dir")
        os.makedirs(src_dir)

        with pytest.raises(InvalidOperationError):
            move_file(src_dir, os.path.join(temp_dir, "dest"))

    def test_move_file_dest_dir_not_exists(self, temp_dir: str) -> None:
        """Test moving to non-existent destination directory raises error."""
        src = os.path.join(temp_dir, "source.txt")
        with open(src, "w") as f:
            f.write("test")

        dest = os.path.join(temp_dir, "nonexistent", "file.txt")
        with pytest.raises(InvalidOperationError):
            move_file(src, dest)

    def test_move_file_returns_boolean(self, temp_dir: str) -> None:
        """Test that move_file returns boolean."""
        src = os.path.join(temp_dir, "source.txt")
        with open(src, "w") as f:
            f.write("test")

        dest = os.path.join(temp_dir, "dest.txt")
        result = move_file(src, dest)

        assert isinstance(result, bool)
        assert result is True


class TestValidateDestination:
    """Tests for validate_destination function."""

    def test_validate_destination_valid(self, temp_dir: str) -> None:
        """Test validating a valid destination directory."""
        is_valid, reason = validate_destination(temp_dir)
        assert is_valid is True
        assert reason == ""

    def test_validate_destination_not_exists(self, temp_dir: str) -> None:
        """Test validating non-existent directory."""
        path = os.path.join(temp_dir, "nonexistent")
        is_valid, reason = validate_destination(path)
        assert is_valid is False
        assert "does not exist" in reason

    def test_validate_destination_not_directory(self, temp_dir: str) -> None:
        """Test validating a file instead of directory."""
        file_path = os.path.join(temp_dir, "file.txt")
        with open(file_path, "w") as f:
            f.write("test")

        is_valid, reason = validate_destination(file_path)
        assert is_valid is False
        assert "not a directory" in reason

    def test_validate_destination_returns_tuple(self, temp_dir: str) -> None:
        """Test that result is a tuple of (bool, str)."""
        result = validate_destination(temp_dir)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)

    def test_validate_destination_low_disk_space(self, temp_dir: str) -> None:
        """Test validating directory with insufficient disk space.
        
        Note: This test is hard to replicate on real filesystems, so we skip it.
        """
        pytest.skip("Cannot easily simulate low disk space on test filesystem")


class TestExecuteMoveOperations:
    """Tests for execute_move_operations function."""

    def test_execute_move_operations_empty_list(self, temp_dir: str) -> None:
        """Test executing empty operations list."""
        result = execute_move_operations([], temp_dir)
        assert result["moved_count"] == 0
        assert result["deleted_count"] == 0
        assert result["failed_count"] == 0
        assert result["errors"] == []

    def test_execute_move_operations_single_move(self, temp_dir: str) -> None:
        """Test executing single move operation."""
        # Create file to move
        src = os.path.join(temp_dir, "source.txt")
        with open(src, "w") as f:
            f.write("test")

        # Create destination directory
        dest_dir = os.path.join(temp_dir, "dest")
        os.makedirs(dest_dir)

        operations = [
            {
                "original": src,
                "target_copy": src,
                "action": "move",
            }
        ]

        result = execute_move_operations(operations, dest_dir)
        assert result["moved_count"] == 1
        assert result["failed_count"] == 0
        assert result["deleted_count"] == 0
        assert len(result["errors"]) == 0

    def test_execute_move_operations_single_delete(self, temp_dir: str) -> None:
        """Test executing single delete operation."""
        # Create file to delete
        file_path = os.path.join(temp_dir, "file.txt")
        with open(file_path, "w") as f:
            f.write("test")

        operations = [
            {
                "original": file_path,
                "target_copy": file_path,
                "action": "delete",
            }
        ]

        result = execute_move_operations(operations, temp_dir)
        assert result["deleted_count"] == 1
        assert result["failed_count"] == 0
        assert result["moved_count"] == 0
        assert len(result["errors"]) == 0
        assert not os.path.exists(file_path)

    def test_execute_move_operations_mixed(self, temp_dir: str) -> None:
        """Test executing mixed move and delete operations."""
        # Create files
        move_file = os.path.join(temp_dir, "move.txt")
        delete_file = os.path.join(temp_dir, "delete.txt")
        with open(move_file, "w") as f:
            f.write("move")
        with open(delete_file, "w") as f:
            f.write("delete")

        # Create destination directory
        dest_dir = os.path.join(temp_dir, "dest")
        os.makedirs(dest_dir)

        operations = [
            {"original": move_file, "target_copy": move_file, "action": "move"},
            {"original": delete_file, "target_copy": delete_file, "action": "delete"},
        ]

        result = execute_move_operations(operations, dest_dir)
        assert result["moved_count"] == 1
        assert result["deleted_count"] == 1
        assert result["failed_count"] == 0

    def test_execute_move_operations_file_not_found(self, temp_dir: str) -> None:
        """Test operation on non-existent file."""
        operations = [
            {
                "original": "fake.txt",
                "target_copy": "/nonexistent/file.txt",
                "action": "delete",
            }
        ]

        result = execute_move_operations(operations, temp_dir)
        assert result["failed_count"] == 1
        assert result["deleted_count"] == 0
        assert len(result["errors"]) == 1
        assert result["errors"][0]["file"] == "/nonexistent/file.txt"

    def test_execute_move_operations_invalid_action(self, temp_dir: str) -> None:
        """Test operation with invalid action."""
        file_path = os.path.join(temp_dir, "file.txt")
        with open(file_path, "w") as f:
            f.write("test")

        operations = [
            {
                "original": file_path,
                "target_copy": file_path,
                "action": "invalid_action",
            }
        ]

        result = execute_move_operations(operations, temp_dir)
        assert result["failed_count"] == 1
        assert result["moved_count"] == 0
        assert result["deleted_count"] == 0

    def test_execute_move_operations_missing_fields(self, temp_dir: str) -> None:
        """Test operation with missing required fields."""
        operations = [
            {
                "original": "file.txt",
                # Missing target_copy and action
            }
        ]

        result = execute_move_operations(operations, temp_dir)
        assert result["failed_count"] == 1
        assert len(result["errors"]) == 1

    def test_execute_move_operations_partial_failure(self, temp_dir: str) -> None:
        """Test that failures don't stop processing other operations."""
        # Create one valid and one invalid file
        valid_file = os.path.join(temp_dir, "valid.txt")
        with open(valid_file, "w") as f:
            f.write("valid")

        dest_dir = os.path.join(temp_dir, "dest")
        os.makedirs(dest_dir)

        operations = [
            {
                "original": "fake.txt",
                "target_copy": "/nonexistent/file.txt",
                "action": "delete",
            },
            {
                "original": valid_file,
                "target_copy": valid_file,
                "action": "delete",
            },
        ]

        result = execute_move_operations(operations, dest_dir)
        assert result["failed_count"] == 1
        assert result["deleted_count"] == 1
        assert len(result["errors"]) == 1

    def test_execute_move_operations_returns_dict(self, temp_dir: str) -> None:
        """Test that result is a properly formatted dictionary."""
        result = execute_move_operations([], temp_dir)
        assert isinstance(result, dict)
        assert "moved_count" in result
        assert "deleted_count" in result
        assert "failed_count" in result
        assert "errors" in result
        assert isinstance(result["moved_count"], int)
        assert isinstance(result["deleted_count"], int)
        assert isinstance(result["failed_count"], int)
        assert isinstance(result["errors"], list)


class TestFileManagerIntegration:
    """Integration tests for file manager."""

    def test_validate_and_move(self, temp_dir: str) -> None:
        """Test validating destination then moving files."""
        is_valid, _ = validate_destination(temp_dir)
        assert is_valid is True

        src = os.path.join(temp_dir, "file.txt")
        with open(src, "w") as f:
            f.write("test")

        dest = os.path.join(temp_dir, "moved.txt")
        result = move_file(src, dest)
        assert result is True

    def test_execute_after_validation(self, temp_dir: str) -> None:
        """Test executing operations after validating destination."""
        dest_dir = os.path.join(temp_dir, "archive")
        os.makedirs(dest_dir)

        is_valid, _ = validate_destination(dest_dir)
        assert is_valid is True

        file_path = os.path.join(temp_dir, "file.txt")
        with open(file_path, "w") as f:
            f.write("test")

        operations = [
            {
                "original": file_path,
                "target_copy": file_path,
                "action": "move",
            }
        ]

        result = execute_move_operations(operations, dest_dir)
        assert result["moved_count"] == 1
        assert result["failed_count"] == 0
