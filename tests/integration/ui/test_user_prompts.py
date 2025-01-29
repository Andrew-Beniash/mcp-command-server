import pytest
from unittest.mock import AsyncMock, patch
from mcp_command_server.security.confirmation import CommandConfirmation, UserConfirmationHandler
from mcp_command_server.ui.prompts import MCPUserPrompts

@pytest.mark.asyncio
class TestMCPUserPrompts:
    
    @pytest.fixture
    async def mcp_prompts(self):
        """Create MCPUserPrompts instance for testing"""
        return MCPUserPrompts()
    
    @pytest.fixture
    def mock_claude_response(self):
        """Mock Claude's response to confirmation requests"""
        return AsyncMock(return_value=True)
        
    async def test_command_confirmation_flow(self, mcp_prompts, mock_claude_response):
        """Test complete command confirmation flow with Claude integration"""
        with patch('mcp_command_server.ui.prompts.get_claude_response', mock_claude_response):
            result = await mcp_prompts.request_confirmation(
                command="rm",
                args=["-rf", "/test/path"],
                path="/test/path",
                user="testuser"
            )
            assert result.confirmed is True
            assert result.risk_level == "HIGH"
            assert mock_claude_response.called
            
    async def test_confirmation_with_sensitive_command(self, mcp_prompts):
        """Test confirmation handling for sensitive commands"""
        with patch('mcp_command_server.ui.prompts.get_claude_response', return_value=False):
            result = await mcp_prompts.request_confirmation(
                command="sudo",
                args=["rm", "-rf", "/"],
                path="/",
                user="testuser"
            )
            assert result.confirmed is False
            assert result.risk_level == "HIGH"
            
    async def test_user_feedback_display(self, mcp_prompts, mock_claude_response):
        """Test user feedback mechanism"""
        with patch('mcp_command_server.ui.prompts.display_feedback') as mock_display:
            await mcp_prompts.show_execution_feedback(
                command="ls",
                status="success",
                message="Successfully listed directory contents"
            )
            mock_display.assert_called_once()