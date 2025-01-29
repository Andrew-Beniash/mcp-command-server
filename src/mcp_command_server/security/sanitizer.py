import re
from pathlib import Path
from typing import List

class CommandSanitizer:
    """Sanitizes command inputs to prevent injection attacks"""
    
    # Characters that could be used for command injection
    DANGEROUS_PATTERNS = [
        r';', r'&', r'\|', r'`', r'\$\(', r'\${',  # Command chaining/substitution
        r'>>', r'>', r'<',  # Redirection
        r'\[\[', r'\]\]',  # Bash test constructs
        r'\$\{[^}]*\}',  # Variable expansion
    ]
    
    def sanitize_command(self, command: str) -> str:
        """
        Sanitize a command string.
        
        Args:
            command: Command string to sanitize
            
        Returns:
            str: Sanitized command
            
        Raises:
            ValueError: If command contains disallowed characters
        """
        # Check for dangerous patterns
        pattern = '|'.join(self.DANGEROUS_PATTERNS)
        if re.search(pattern, command):
            raise ValueError("Command contains disallowed characters")
            
        # Only allow alphanumeric characters, underscore, and hyphen
        if not re.match("^[a-zA-Z0-9_-]+$", command):
            raise ValueError("Command contains disallowed characters")
            
        return command
        
    def sanitize_path(self, path: str) -> str:
        """
        Sanitize a path string.
        
        Args:
            path: Path string to sanitize
            
        Returns:
            str: Sanitized path
            
        Raises:
            ValueError: If path contains disallowed characters
        """
        try:
            # Resolve the path to eliminate '..' and symbolic links
            resolved_path = str(Path(path).resolve())
            
            # Check for dangerous patterns
            pattern = '|'.join(self.DANGEROUS_PATTERNS)
            if re.search(pattern, resolved_path):
                raise ValueError("Path contains disallowed characters")
                
            return resolved_path
            
        except Exception as e:
            raise ValueError(f"Invalid path: {str(e)}")
            
    def sanitize_arguments(self, args: List[str]) -> List[str]:
        """
        Sanitize command arguments.
        
        Args:
            args: List of argument strings to sanitize
            
        Returns:
            List[str]: Sanitized arguments
            
        Raises:
            ValueError: If arguments contain disallowed characters
        """
        sanitized_args = []
        for arg in args:
            # Check for dangerous patterns
            pattern = '|'.join(self.DANGEROUS_PATTERNS)
            if re.search(pattern, arg):
                raise ValueError("Arguments contain disallowed characters")
                
            # Only allow certain characters in arguments
            if not re.match("^[a-zA-Z0-9_\-\.\/]+$", arg):
                raise ValueError("Arguments contain disallowed characters")
                
            sanitized_args.append(arg)
            
        return sanitized_args