from typing import Optional
import time
from dataclasses import dataclass
from ..security.confirmation import CommandConfirmation, UserConfirmationHandler

@dataclass
class ConfirmationResult:
    """Stores the result of a confirmation request"""
    confirmed: bool
    risk_level: str
    timestamp: float
    feedback: Optional[str] = None

class MCPUserPrompts:
    """Handles user interaction prompts and feedback for MCP"""
    
    def __init__(self):
        """Initialize the MCP prompts handler"""
        self.confirmation_handler = UserConfirmationHandler()
        
    async def request_confirmation(self, command: str, args: list, path: str, user: str) -> ConfirmationResult:
        """
        Request user confirmation through Claude Desktop interface
        
        Args:
            command: Command to be executed
            args: Command arguments
            path: Target path
            user: User executing the command
            
        Returns:
            ConfirmationResult: Object containing confirmation details
        """
        import time
        
        confirmation = CommandConfirmation(
            command=command,
            args=args,
            path=path,
            user=user,
            risk_level=self.confirmation_handler._assess_risk(command, args, path)
        )
        
        # Format confirmation message for Claude
        message = self._format_confirmation_message(confirmation)
        
        # Get confirmation through Claude
        confirmed = await self._get_claude_confirmation(message, confirmation.risk_level)
        
        return ConfirmationResult(
            confirmed=confirmed,
            risk_level=confirmation.risk_level,
            timestamp=time.time()
        )
    
    async def show_execution_feedback(self, command: str, status: str, message: str):
        """
        Display execution feedback to user
        
        Args:
            command: Executed command
            status: Execution status
            message: Feedback message
        """
        feedback = {
            "command": command,
            "status": status,
            "message": message,
            "timestamp": time.time()
        }
        
        await self._display_feedback(feedback)
    
    def _format_confirmation_message(self, confirmation: CommandConfirmation) -> str:
        """Format confirmation message for Claude"""
        return f"""
Command Execution Confirmation Required
-------------------------------------
Command: {confirmation.command}
Arguments: {' '.join(confirmation.args)}
Path: {confirmation.path}
User: {confirmation.user}
Risk Level: {confirmation.risk_level}

{self.confirmation_handler.RISK_LEVELS[confirmation.risk_level]}

Do you want to proceed with this command?
"""
    
    async def _get_claude_confirmation(self, message: str, risk_level: str) -> bool:
        """Get confirmation through Claude Desktop"""
        # This will be implemented by the Claude Desktop integration
        from ..integration.claude_desktop import get_claude_response
        return await get_claude_response(message, risk_level)
    
    async def _display_feedback(self, feedback: dict):
        """Display feedback through Claude Desktop"""
        # This will be implemented by the Claude Desktop integration
        from ..integration.claude_desktop import display_feedback
        await display_feedback(feedback)