import pytest
from src.mcp_command_server.security.sanitizer import CommandSanitizer

def test_sanitize_command_basic():
    sanitizer = CommandSanitizer()
    result = sanitizer.sanitize_command("ls")
    assert result == "ls"

def test_sanitize_command_with_args():
    sanitizer = CommandSanitizer()
    result = sanitizer.sanitize_command("ls -l /path")
    assert result == "ls -l /path"

def test_sanitize_command_with_injection_attempt():
    sanitizer = CommandSanitizer()
    with pytest.raises(ValueError, match="Command contains disallowed characters"):
        sanitizer.sanitize_command("ls; rm -rf /")

def test_sanitize_command_with_shell_metacharacters():
    sanitizer = CommandSanitizer()
    with pytest.raises(ValueError, match="Command contains disallowed characters"):
        sanitizer.sanitize_command("ls `whoami`")

def test_sanitize_path():
    sanitizer = CommandSanitizer()
    result = sanitizer.sanitize_path("/allowed/path")
    assert result == "/allowed/path"

def test_sanitize_path_with_traversal_attempt():
    sanitizer = CommandSanitizer()
    with pytest.raises(ValueError, match="Path contains disallowed characters"):
        sanitizer.sanitize_path("../../../etc/passwd")

def test_sanitize_arguments():
    sanitizer = CommandSanitizer()
    result = sanitizer.sanitize_arguments(["-l", "-a"])
    assert result == ["-l", "-a"]

def test_sanitize_arguments_with_injection():
    sanitizer = CommandSanitizer()
    with pytest.raises(ValueError, match="Arguments contain disallowed characters"):
        sanitizer.sanitize_arguments(["-l; rm -rf /"])