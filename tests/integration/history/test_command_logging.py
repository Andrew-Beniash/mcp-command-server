import pytest
import os
from datetime import datetime
from mcp_command_server.history.command_logger import CommandLogger, CommandRecord

@pytest.mark.asyncio
class TestCommandLogging:
    
    @pytest.fixture
    def log_file_path(self, tmp_path):
        """Create temporary log file"""
        return tmp_path / "command_history.log"
    
    @pytest.fixture
    async def command_logger(self, log_file_path):
        """Create CommandLogger instance"""
        logger = CommandLogger(log_file_path)
        yield logger
        # Cleanup
        if os.path.exists(log_file_path):
            os.remove(log_file_path)
    
    async def test_log_command_execution(self, command_logger):
        """Test logging of command execution"""
        record = CommandRecord(
            timestamp=datetime.now(),
            command="ls",
            args=["-l"],
            path="/test",
            user="testuser",
            status="success",
            risk_level="LOW"
        )
        
        await command_logger.log_command(record)
        history = await command_logger.get_command_history()
        
        assert len(history) == 1
        assert history[0].command == "ls"
        assert history[0].status == "success"
    
    async def test_sensitive_data_masking(self, command_logger):
        """Test that sensitive data is properly masked in logs"""
        record = CommandRecord(
            timestamp=datetime.now(),
            command="mysql",
            args=["-u", "root", "-p", "secretpass"],
            path="/",
            user="testuser",
            status="success",
            risk_level="HIGH"
        )
        
        await command_logger.log_command(record)
        history = await command_logger.get_command_history()
        
        assert "secretpass" not in str(history[0])
        assert "[MASKED]" in str(history[0])