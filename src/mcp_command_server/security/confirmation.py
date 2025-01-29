from typing import Optional, Callable
from dataclasses import dataclass

@dataclass
class CommandConfirmation:
    command: str
    args: list
    path: str
    user: str
    risk_level: str

class UserConfirmationHandler:
    """Handles user confirmation for potentially dangerous operations"""
    
    RISK_LEVELS = {
        "LOW": "This operation is safe but requires confirmation.",
        "MEDIUM": "This operation could modify files or data.",
        "HIGH": "This operation could significantly impact the system."
    }
    
    def __init__(self, confirmation_callback: Optional[Callable] = None):
        """
        Initialize the confirmation handler.
        
        Args:
            confirmation_callback: Optional callback function for getting user confirmation
        """
        self._callback = confirmation_callback or self._default_confirmation
        
    def require_confirmation(self, command: str, args: list, path: str, user: str) -> bool:
        """
        Request user confirmation for a command.
        
        Args:
            command: The command to be executed
            args: Command arguments
            path: Target path
            user: User executing the command
            
        Returns:
            bool: True if user confirmed, False otherwise
        """
        # Determine risk level
        risk_level = self._assess_risk(command, args, path)
        
        confirmation = CommandConfirmation(
            command=command,
            args=args,
            path=path,
            user=user,
            risk_level=risk_level
        )
        
        return self._callback(confirmation)
        
    def _assess_risk(self, command: str, args: list, path: str) -> str:
        """
        Assess the risk level of a command.
        
        Args:
            command: The command to assess
            args: Command arguments
            path: Target path
            
        Returns:
            str: Risk level (LOW/MEDIUM/HIGH)
        """
        # Conservative default
        risk_level = "MEDIUM"
        
        # Read operations are generally lower risk
        if command in ["ls", "cat", "head", "tail"]:
            risk_level = "LOW"
            
        # Destructive operations are high risk
        elif command in ["rm", "mv"] or "-f" in args or "--force" in args:
            risk_level = "HIGH"
            
        return risk_level
        
    def _default_confirmation(self, confirmation: CommandConfirmation) -> bool:
        """
        Default implementation of confirmation dialog.
        
        Args:
            confirmation: CommandConfirmation object
            
        Returns:
            bool: True if user confirmed, False otherwise
        """
        print("\nCommand Execution Confirmation")
        print("------------------------------")
        print(f"Command: {confirmation.command}")
        print(f"Arguments: {' '.join(confirmation.args)}")
        print(f"Path: {confirmation.path}")
        print(f"User: {confirmation.user}")
        print(f"Risk Level: {confirmation.risk_level}")
        print(f"Warning: {self.RISK_LEVELS[confirmation.risk_level]}")
        
        response = input("\nDo you want to proceed? (yes/no): ")
        return response.lower() == 'yes'