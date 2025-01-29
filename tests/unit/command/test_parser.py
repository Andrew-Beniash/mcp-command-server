import pytest
from mcp_command_server.command.parser import CommandParser, CommandParseError
from mcp_command_server.security.validator import CommandValidator, ValidationError

# Test fixtures
@pytest.fixture
def allowed_commands():
    return {
        "list": {
            "args": ["-l", "-a", "--hidden"],
            "paths": ["/home", "/usr/local"]
        },
        "copy": {
            "args": ["-r", "-f"],
            "paths": ["/home", "/tmp"]
        }
    }

@pytest.fixture
def command_parser(allowed_commands):
    validator = CommandValidator(allowed_commands)
    return CommandParser(validator)

class TestCommandParser:
    def test_parse_simple_command(self, command_parser):
        """Test parsing a simple command without arguments"""
        result = command_parser.parse("list /home/user")
        assert result.command == "list"
        assert result.args == []
        assert result.path == "/home/user"

    def test_parse_command_with_args(self, command_parser):
        """Test parsing a command with arguments"""
        result = command_parser.parse("list -l -a /home/user")
        assert result.command == "list"
        assert result.args == ["-l", "-a"]
        assert result.path == "/home/user"

    def test_invalid_command_format(self, command_parser):
        """Test handling of invalid command format"""
        with pytest.raises(CommandParseError, match="Invalid command format"):
            command_parser.parse("")

    def test_command_with_invalid_chars(self, command_parser):
        """Test handling of commands with invalid characters"""
        with pytest.raises(ValidationError):
            command_parser.parse("list; rm -rf /home/user")

    def test_command_not_in_whitelist(self, command_parser):
        """Test handling of non-whitelisted commands"""
        with pytest.raises(ValidationError):
            command_parser.parse("delete /home/user")

    def test_unsafe_path_traversal(self, command_parser):
        """Test handling of path traversal attempts"""
        with pytest.raises(ValidationError):
            command_parser.parse("list ../../../etc/passwd")

    def test_command_with_quotes(self, command_parser):
        """Test parsing commands with quoted paths"""
        result = command_parser.parse('copy -r "/home/user/My Documents" /home/backup')
        assert result.command == "copy"
        assert result.args == ["-r"]
        assert result.path == "/home/user/My Documents"

    def test_invalid_arguments(self, command_parser):
        """Test handling of invalid arguments"""
        with pytest.raises(ValidationError):
            command_parser.parse("list --invalid /home/user")