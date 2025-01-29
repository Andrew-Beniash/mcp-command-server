import pytest
from unittest.mock import Mock, patch
import subprocess
import asyncio
from mcp_command_server.terminal.terminal_interface import TerminalInterface, TerminalError, CommandTimeoutError

@pytest.fixture
def terminal():
    """Create a TerminalInterface instance for testing"""
    return TerminalInterface()

class TestTerminalInterface:
    @pytest.mark.asyncio
    async def test_execute_command_success(self, terminal):
        """Test successful command execution with output capture"""
        result = await terminal.execute("echo 'test'")
        assert result.stdout.strip() == "test"
        assert result.returncode == 0
        assert result.stderr == ""

    @pytest.mark.asyncio
    async def test_execute_command_with_error(self, terminal):
        """Test command execution that results in error"""
        with pytest.raises(TerminalError) as exc_info:
            await terminal.execute("nonexistent_command")
        assert "Command execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_command_timeout(self, terminal):
        """Test command execution timeout"""
        with pytest.raises(CommandTimeoutError):
            await terminal.execute("sleep 10", timeout=0.1)

    @pytest.mark.asyncio
    async def test_command_output_streaming(self, terminal):
        """Test streaming output capture from long-running command"""
        output_lines = []
        async for line in terminal.execute_streaming("for i in 1 2 3; do echo $i; sleep 0.1; done"):
            output_lines.append(line.strip())
        assert output_lines == ["1", "2", "3"]

    @pytest.mark.asyncio
    async def test_process_termination(self, terminal):
        """Test proper process termination"""
        process = await terminal.execute("echo 'test'")
        assert process.returncode == 0
        
        # Ensure process resources are cleaned up
        with pytest.raises(TerminalError):
            process.kill()  # Should raise error as process already terminated

    @pytest.mark.asyncio
    async def test_environment_variables(self, terminal):
        """Test command execution with custom environment variables"""
        env = {"TEST_VAR": "test_value"}
        result = await terminal.execute("echo $TEST_VAR", env=env)
        assert result.stdout.strip() == "test_value"

    @pytest.mark.asyncio
    async def test_working_directory(self, terminal, tmp_path):
        """Test command execution in specific working directory"""
        result = await terminal.execute("pwd", cwd=str(tmp_path))
        assert result.stdout.strip() == str(tmp_path)

    @pytest.mark.asyncio
    async def test_handle_large_output(self, terminal):
        """Test handling of commands with large output"""
        large_output = "echo " + "x" * 1024 * 1024  # 1MB of output
        result = await terminal.execute(large_output)
        assert len(result.stdout) == 1024 * 1024 + 1  # +1 for newline

    @pytest.mark.asyncio
    async def test_concurrent_execution(self, terminal):
        """Test concurrent command execution"""
        commands = ["sleep 0.1; echo 1", "sleep 0.2; echo 2", "sleep 0.3; echo 3"]
        tasks = [terminal.execute(cmd) for cmd in commands]
        results = await asyncio.gather(*tasks)
        
        outputs = [r.stdout.strip() for r in results]
        assert outputs == ["1", "2", "3"]