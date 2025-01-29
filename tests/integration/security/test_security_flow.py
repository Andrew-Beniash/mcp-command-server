import pytest
import os
import json
from pathlib import Path
from typing import Generator
from unittest.mock import Mock

from mcp_command_server.security.validator import CommandValidator, ValidationError
from mcp_command_server.security.sanitizer import CommandSanitizer
from mcp_command_server.security.audit import AuditLogger
from mcp_command_server.security.confirmation import UserConfirmationHandler, CommandConfirmation

class TestSecurityFlow:
    @pytest.fixture
    def temp_audit_log(self, tmp_path) -> Generator[Path, None, None]:
        """Create a temporary audit log file"""
        audit_log = tmp_path / "audit.log"
        yield audit_log
        if audit_log.exists():
            audit_log.unlink()

    @pytest.fixture
    def temp_work_dir(self, tmp_path) -> Generator[Path, None, None]:
        """Create a temporary working directory"""
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        yield work_dir
        # Cleanup after test

    @pytest.fixture
    def allowed_commands(self, temp_work_dir) -> dict:
        """Define allowed commands for testing"""
        return {
            "ls": {
                "args": ["-l", "-a", "-la"],
                "paths": [str(temp_work_dir)]
            },
            "cat": {
                "args": [],
                "paths": [str(temp_work_dir)]
            }
        }

    @pytest.fixture
    def security_components(self, allowed_commands, temp_audit_log):
        """Initialize all security components"""
        validator = CommandValidator(allowed_commands)
        sanitizer = CommandSanitizer()
        audit_logger = AuditLogger(str(temp_audit_log))
        confirmation_handler = UserConfirmationHandler()
        
        return {
            "validator": validator,
            "sanitizer": sanitizer,
            "audit_logger": audit_logger,
            "confirmation_handler": confirmation_handler
        }

    def test_successful_command_execution_flow(self, security_components, temp_work_dir, temp_audit_log):
        """Test a complete successful command execution flow"""
        # Setup test file
        test_file = temp_work_dir / "test.txt"
        test_file.write_text("test content")

        # Command to test
        command = "ls"
        args = ["-l"]
        path = str(temp_work_dir)
        user = "testuser"

        # Mock user confirmation to always return True
        security_components["confirmation_handler"]._callback = Mock(return_value=True)

        try:
            # 1. Sanitize inputs
            sanitized_command = security_components["sanitizer"].sanitize_command(command)
            sanitized_args = security_components["sanitizer"].sanitize_arguments(args)
            sanitized_path = security_components["sanitizer"].sanitize_path(path)

            # 2. Validate command
            security_components["validator"].validate_command(
                sanitized_command, 
                sanitized_args, 
                sanitized_path
            )

            # 3. Get user confirmation
            confirmed = security_components["confirmation_handler"].require_confirmation(
                sanitized_command,
                sanitized_args,
                sanitized_path,
                user
            )
            assert confirmed is True

            # 4. Log the execution
            security_components["audit_logger"].log_command_execution(
                sanitized_command,
                sanitized_args,
                sanitized_path,
                "success",
                user
            )

            # 5. Verify audit log
            with open(temp_audit_log) as f:
                log_entry = json.loads(f.readline())
                assert log_entry["command"] == command
                assert log_entry["arguments"] == args
                assert log_entry["path"] == str(temp_work_dir)
                assert log_entry["status"] == "success"
                assert log_entry["user"] == user

        except Exception as e:
            pytest.fail(f"Security flow failed: {str(e)}")

    def test_failed_validation_flow(self, security_components, temp_work_dir, temp_audit_log):
        """Test command failure due to validation"""
        command = "rm"  # Unauthorized command
        args = ["-rf"]
        path = str(temp_work_dir)
        user = "testuser"

        try:
            # 1. Sanitize inputs
            sanitized_command = security_components["sanitizer"].sanitize_command(command)
            sanitized_args = security_components["sanitizer"].sanitize_arguments(args)
            sanitized_path = security_components["sanitizer"].sanitize_path(path)

            # 2. Validate command (should fail)
            with pytest.raises(ValidationError):
                security_components["validator"].validate_command(
                    sanitized_command,
                    sanitized_args,
                    sanitized_path
                )

            # 3. Log the failed attempt
            security_components["audit_logger"].log_command_execution(
                command,
                args,
                path,
                "failed",
                user,
                error_message="Command not allowed"
            )

            # 4. Verify audit log contains failure
            with open(temp_audit_log) as f:
                log_entry = json.loads(f.readline())
                assert log_entry["status"] == "failed"
                assert "error" in log_entry

        except Exception as e:
            if not isinstance(e, ValidationError):
                pytest.fail(f"Unexpected error in security flow: {str(e)}")

    def test_injection_attempt_flow(self, security_components, temp_work_dir, temp_audit_log):
        """Test handling of command injection attempt"""
        command = "ls; rm -rf /"  # Injection attempt
        args = ["-l"]
        path = str(temp_work_dir)
        user = "testuser"

        try:
            # 1. Sanitize inputs (should fail)
            with pytest.raises(ValueError) as exc_info:
                security_components["sanitizer"].sanitize_command(command)

            # 2. Log the injection attempt
            security_components["audit_logger"].log_command_execution(
                command,
                args,
                path,
                "failed",
                user,
                error_message=str(exc_info.value)
            )

            # 3. Verify audit log contains injection attempt
            with open(temp_audit_log) as f:
                log_entry = json.loads(f.readline())
                assert log_entry["status"] == "failed"
                assert "disallowed characters" in log_entry["error"].lower()

        except Exception as e:
            if not isinstance(e, ValueError):
                pytest.fail(f"Unexpected error in security flow: {str(e)}")

    def test_unauthorized_path_flow(self, security_components, temp_work_dir, temp_audit_log):
        """Test handling of unauthorized path access attempt"""
        command = "ls"
        args = ["-l"]
        path = "/etc"  # Unauthorized path
        user = "testuser"

        try:
            # 1. Sanitize inputs
            sanitized_command = security_components["sanitizer"].sanitize_command(command)
            sanitized_args = security_components["sanitizer"].sanitize_arguments(args)
            sanitized_path = security_components["sanitizer"].sanitize_path(path)

            # 2. Validate command (should fail due to path)
            with pytest.raises(ValidationError):
                security_components["validator"].validate_command(
                    sanitized_command,
                    sanitized_args,
                    sanitized_path
                )

            # 3. Log the unauthorized attempt
            security_components["audit_logger"].log_command_execution(
                command,
                args,
                path,
                "failed",
                user,
                error_message="Unauthorized path access attempt"
            )

            # 4. Verify audit log contains unauthorized attempt
            with open(temp_audit_log) as f:
                log_entry = json.loads(f.readline())
                assert log_entry["status"] == "failed"
                assert "unauthorized" in log_entry["error"].lower()

        except Exception as e:
            if not isinstance(e, ValidationError):
                pytest.fail(f"Unexpected error in security flow: {str(e)}")