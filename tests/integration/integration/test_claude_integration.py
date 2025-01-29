import pytest
from unittest.mock import patch, AsyncMock
from mcp_command_server.integration.claude_desktop import ClaudeDesktopIntegration

@pytest.mark.asyncio
class TestClaudeDesktopIntegration:
    
    @pytest.fixture
    async def claude_integration(self):
        """Create ClaudeDesktopIntegration instance"""
        return ClaudeDesktopIntegration()
    
    async def test_tool_registration(self, claude_integration):
        """Test registering command execution tools with Claude"""
        with patch('mcp_command_server.integration.claude_desktop.register_tool') as mock_register:
            await claude_integration.register_command_tools()
            assert mock_register.called
            
    async def test_confirmation_handling(self, claude_integration):
        """Test handling of confirmation requests through Claude"""
        with patch('mcp_command_server.integration.claude_desktop.request_confirmation') as mock_confirm:
            mock_confirm.return_value = True
            
            result = await claude_integration.get_user_confirmation(
                command="rm",
                args=["-rf", "/test"],
                risk_level="HIGH"
            )
            
            assert result is True
            assert mock_confirm.called
            
    async def test_error_handling(self, claude_integration):
        """Test error handling in Claude integration"""
        with patch('mcp_command_server.integration.claude_desktop.execute_command') as mock_execute:
            mock_execute.side_effect = Exception("Test error")
            
            with pytest.raises(Exception):
                await claude_integration.execute_command("invalid_command")