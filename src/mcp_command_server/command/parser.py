from dataclasses import dataclass
from typing import List
import shlex
from pathlib import Path
from ..security.validator import CommandValidator, ValidationError

@dataclass
class ParsedCommand:
    """
    Represents a parsed and validated command
    
    Attributes:
        command: The validated command string
        args: List of validated command arguments
        path: Validated target path
    """
    command: str
    args: List[str]
    path: str

class CommandParseError(Exception):
    """Raised when command parsing fails"""
    pass

class CommandParser:
    """
    Parses and validates command strings according to security rules
    
    Handles command parsing, argument extraction, and security validation
    by integrating with the CommandValidator.
    """
    
    def __init__(self, validator: CommandValidator):
        """
        Initialize the parser with a security validator
        
        Args:
            validator: CommandValidator instance for security checks
        """
        self.validator = validator

    def parse(self, command_string: str) -> ParsedCommand:
        """
        Parse and validate a command string
        
        Args:
            command_string: Raw command string to parse
            
        Returns:
            ParsedCommand object containing validated components
            
        Raises:
            CommandParseError: If parsing fails
            ValidationError: If security validation fails
        """
        if not command_string:
            raise CommandParseError("Invalid command format: empty command")
            
        try:
            # Use shlex to properly handle quoted strings and spaces
            parts = shlex.split(command_string)
        except ValueError as e:
            raise CommandParseError(f"Failed to parse command: {str(e)}")
            
        if len(parts) < 2:
            raise CommandParseError(
                "Invalid command format: must include command and path"
            )
            
        # Extract command, arguments and path
        command = parts[0]
        path = parts[-1]  # Last part is always the path
        args = parts[1:-1]  # Everything in between is args
        
        try:
            # Normalize path for security checks
            normalized_path = str(Path(path).resolve())
            
            # Validate all components through security validator
            self.validator.validate_command(
                command=command,
                args=args,
                path=normalized_path
            )
            
            return ParsedCommand(
                command=command,
                args=args,
                path=normalized_path
            )
            
        except (ValidationError, ValueError) as e:
            # Re-raise validation errors
            raise ValidationError(f"Command validation failed: {str(e)}")
        except Exception as e:
            # Convert unexpected errors to parse errors
            raise CommandParseError(f"Failed to process command: {str(e)}")

    def is_dangerous_command(self, command_string: str) -> bool:
        """
        Check if a command might be dangerous
        
        Args:
            command_string: Command string to check
            
        Returns:
            bool: True if command appears dangerous
        """
        dangerous_patterns = [
            ';', '&&', '||',  # Command chaining
            '>', '>>', '<',   # Redirection
            '|', '`',         # Pipes and backticks
            '$(',             # Command substitution
            'rm', 'chmod',    # Dangerous commands
            '/etc', '/dev',   # Sensitive directories
            '../',            # Path traversal
        ]
        
        return any(pattern in command_string for pattern in dangerous_patterns)