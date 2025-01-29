import pytest
from unittest.mock import patch, mock_open
import json
from datetime import datetime
from src.mcp_command_server.security.audit import AuditLogger

def test_audit_logger_init():
    with patch('builtins.open', mock_open()):
        logger = AuditLogger("/path/to/audit.log")
        assert logger.log_path == "/path/to/audit.log"

def test_log_command_execution():
    mock_time = datetime(2025, 1, 1, 12, 0, 0)
    expected_log = {
        "timestamp": mock_time.isoformat(),
        "command": "ls",
        "arguments": ["-l"],
        "path": "/test/path",
        "status": "success",
        "user": "testuser"
    }
    
    with patch('builtins.open', mock_open()) as mock_file, \
         patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = mock_time
        
        logger = AuditLogger("/path/to/audit.log")
        logger.log_command_execution("ls", ["-l"], "/test/path", "success", "testuser")
        
        # Verify that the log was written correctly
        mock_file().write.assert_called_once_with(json.dumps(expected_log) + "\n")

def test_log_command_execution_failure():
    with patch('builtins.open', mock_open()) as mock_file:
        logger = AuditLogger("/path/to/audit.log")
        logger.log_command_execution("rm", ["-rf"], "/", "failed: permission denied", "testuser")
        
        # Verify that the failure was logged
        assert mock_file().write.called
        log_entry = json.loads(mock_file().write.call_args[0][0])
        assert log_entry["status"] == "failed: permission denied"

def test_audit_logger_file_permission_error():
    with patch('builtins.open', mock_open()) as mock_file:
        mock_file.side_effect = PermissionError
        with pytest.raises(PermissionError):
            AuditLogger("/path/to/audit.log")