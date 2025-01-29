import pytest
import os
import asyncio
from mcp_command_server.terminal.terminal_interface import TerminalInterface
from pathlib import Path

@pytest.fixture
def terminal():
    """Create a TerminalInterface instance for testing"""
    return TerminalInterface()

class TestTerminalIntegration:
    @pytest.mark.asyncio
    async def test_file_creation_and_reading(self, terminal, tmp_path):
        """Test creating and reading file through terminal commands"""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        
        # Create file
        await terminal.execute(f"echo '{test_content}' > {test_file}")
        
        # Read file
        result = await terminal.execute(f"cat {test_file}")
        assert result.stdout.strip() == test_content
        
        # Clean up
        assert test_file.exists()
        test_file.unlink()

    @pytest.mark.asyncio
    async def test_pipeline_commands(self, terminal):
        """Test execution of pipeline commands"""
        result = await terminal.execute("echo 'hello world' | grep 'hello'")
        assert "hello world" in result.stdout

    @pytest.mark.asyncio
    async def test_background_process_handling(self, terminal):
        """Test handling of background processes"""
        # Start a background process
        await terminal.execute("sleep 10 &")
        
        # Check if process exists
        ps_result = await terminal.execute("ps aux | grep 'sleep 10' | grep -v grep")
        assert "sleep 10" in ps_result.stdout
        
        # Kill the process
        await terminal.execute("pkill -f 'sleep 10'")
        
        # Verify process is killed
        await asyncio.sleep(0.1)  # Give some time for process to be killed
        ps_result = await terminal.execute("ps aux | grep 'sleep 10' | grep -v grep")
        assert ps_result.stdout.strip() == ""

    @pytest.mark.asyncio
    async def test_interactive_command(self, terminal):
        """Test handling of interactive commands that require input"""
        command = "read -p 'Enter value: ' value; echo $value"
        input_data = "test_input\n"
        
        result = await terminal.execute(command, input_data=input_data)
        assert "test_input" in result.stdout

    @pytest.mark.asyncio
    async def test_signal_handling(self, terminal):
        """Test proper handling of system signals"""
        # Start a long-running process
        process = await terminal.execute_async("sleep 30")
        
        # Send SIGTERM
        process.terminate()
        
        # Wait for process to finish
        try:
            await asyncio.wait_for(process.wait(), timeout=1.0)
            assert process.returncode != 0
        except asyncio.TimeoutError:
            pytest.fail("Process did not terminate properly")