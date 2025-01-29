import pytest
from mcp_command_server.command.parser import CommandParser
from mcp_command_server.security.validator import CommandValidator, ValidationError  # Added import
from pathlib import Path

@pytest.fixture
def setup_test_env(tmp_path):
    """Setup test environment with temporary directories"""
    test_dir = tmp_path / "test_dir"
    test_dir.mkdir()
    return test_dir

@pytest.fixture
def integrated_parser(tmp_path):
    """Create a parser with real validator integration"""
    allowed_commands = {
        "list": {
            "args": ["-l", "-a", "--hidden"],
            "paths": [str(tmp_path)]
        },
        "copy": {
            "args": ["-r", "-f"],
            "paths": [str(tmp_path)]
        }
    }
    validator = CommandValidator(allowed_commands)
    return CommandParser(validator)

class TestCommandIntegration:
    def test_full_command_flow(self, integrated_parser, setup_test_env):
        """Test complete flow of command parsing and validation"""
        test_file = setup_test_env / "test.txt"
        test_file.write_text("test content")
        
        result = integrated_parser.parse(f"list -l {str(setup_test_env)}")
        assert result.command == "list"
        assert "-l" in result.args
        assert Path(result.path).exists()

    def test_command_with_real_paths(self, integrated_parser, setup_test_env):
        """Test handling of real filesystem paths"""
        nested_dir = setup_test_env / "nested" / "path"
        nested_dir.mkdir(parents=True)
        
        result = integrated_parser.parse(f"copy -r {str(nested_dir)} {str(setup_test_env)}")
        assert result.command == "copy"
        assert "-r" in result.args
        assert Path(result.path).exists()

    def test_security_integration(self, integrated_parser):
        """Test integration of security validations"""
        with pytest.raises(ValidationError):
            integrated_parser.parse("list -l /etc/passwd")

        with pytest.raises(ValidationError):
            integrated_parser.parse("rm -rf /")

    def test_argument_validation_flow(self, integrated_parser, setup_test_env):
        """Test full argument validation flow"""
        with pytest.raises(ValidationError):
            integrated_parser.parse(f"list --invalid {str(setup_test_env)}")