from typing import Dict, List, Any
import re
from pathlib import Path

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class CommandValidator:
    """Validates commands against a predefined set of allowed commands, arguments, and paths"""
    
    def __init__(self, allowed_commands: Dict[str, Dict[str, Any]]):
        """
        Initialize the validator with allowed commands configuration.
        
        Args:
            allowed_commands: Dictionary mapping command names to their allowed arguments and paths
                Format: {
                    "command": {
                        "args": [list of allowed arguments],
                        "paths": [list of allowed path patterns]
                    }
                }
        """
        if not allowed_commands:
            raise ValueError("Allowed commands cannot be empty")
        self.allowed_commands = allowed_commands
        
    def validate_command(self, command: str, args: List[str], path: str) -> bool:
        """
        Validate a command, its arguments, and target path.
        
        Args:
            command: The command to validate
            args: List of command arguments
            path: Target path for the command
            
        Returns:
            True if validation passes
            
        Raises:
            ValidationError: If any validation check fails
        """
        # Check for invalid characters that might indicate injection attempts
        if not re.match("^[a-zA-Z0-9_-]+$", command):
            raise ValidationError("Command contains invalid characters")
            
        # Verify command is in allowed list
        if command not in self.allowed_commands:
            raise ValidationError(f"Command '{command}' is not allowed")
            
        # Validate arguments
        allowed_args = self.allowed_commands[command]["args"]
        for arg in args:
            if arg not in allowed_args:
                raise ValidationError(f"Argument '{arg}' is not allowed for command '{command}'")
                
        # Validate path
        allowed_paths = self.allowed_commands[command]["paths"]
        path_obj = Path(path).resolve()
        if not any(path_obj.is_relative_to(Path(allowed_path)) for allowed_path in allowed_paths):
            raise ValidationError(f"Path '{path}' is not allowed for command '{command}'")
            
        return True

    def is_path_allowed(self, path: str, command: str) -> bool:
        """
        Check if a path is allowed for a specific command.
        
        Args:
            path: Path to validate
            command: Command to check against
            
        Returns:
            bool: True if path is allowed, False otherwise
        """
        if command not in self.allowed_commands:
            return False
            
        path_obj = Path(path).resolve()
        allowed_paths = self.allowed_commands[command]["paths"]
        return any(path_obj.is_relative_to(Path(allowed_path)) for allowed_path in allowed_paths)