import pytest
from typing import List, Dict
from src.mcp_command_server.security.validator import CommandValidator, ValidationError

def test_validator_init_with_valid_commands():
    allowed_commands = {
        "ls": {"args": ["-l", "-a"], "paths": ["/allowed/path"]},
        "cat": {"args": [], "paths": ["/allowed/path"]},
    }
    validator = CommandValidator(allowed_commands)
    assert validator.allowed_commands == allowed_commands

def test_validator_init_with_empty_commands():
    with pytest.raises(ValueError, match="Allowed commands cannot be empty"):
        CommandValidator({})

def test_validate_command_success():
    allowed_commands = {
        "ls": {"args": ["-l", "-a"], "paths": ["/allowed/path"]},
    }
    validator = CommandValidator(allowed_commands)
    assert validator.validate_command("ls", ["-l"], "/allowed/path") is True

def test_validate_command_invalid_command():
    allowed_commands = {
        "ls": {"args": ["-l", "-a"], "paths": ["/allowed/path"]},
    }
    validator = CommandValidator(allowed_commands)
    with pytest.raises(ValidationError, match="Command 'rm' is not allowed"):
        validator.validate_command("rm", [], "/some/path")

def test_validate_command_invalid_args():
    allowed_commands = {
        "ls": {"args": ["-l", "-a"], "paths": ["/allowed/path"]},
    }
    validator = CommandValidator(allowed_commands)
    with pytest.raises(ValidationError, match="Argument '-r' is not allowed for command 'ls'"):
        validator.validate_command("ls", ["-r"], "/allowed/path")

def test_validate_command_invalid_path():
    allowed_commands = {
        "ls": {"args": ["-l", "-a"], "paths": ["/allowed/path"]},
    }
    validator = CommandValidator(allowed_commands)
    with pytest.raises(ValidationError, match="Path '/unauthorized/path' is not allowed for command 'ls'"):
        validator.validate_command("ls", ["-l"], "/unauthorized/path")

def test_validate_command_with_injection_attempt():
    allowed_commands = {
        "ls": {"args": ["-l", "-a"], "paths": ["/allowed/path"]},
    }
    validator = CommandValidator(allowed_commands)
    with pytest.raises(ValidationError, match="Command contains invalid characters"):
        validator.validate_command("ls; rm -rf /", ["-l"], "/allowed/path")