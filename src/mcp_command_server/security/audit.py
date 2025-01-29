import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import os

class AuditLogger:
    """Logs command executions for security auditing"""
    
    def __init__(self, log_path: str):
        """
        Initialize the audit logger.
        
        Args:
            log_path: Path to the audit log file
            
        Raises:
            PermissionError: If unable to write to log file
        """
        self.log_path = log_path
        
        # Ensure log directory exists
        log_dir = os.path.dirname(log_path)
        os.makedirs(log_dir, exist_ok=True)
        
        # Verify we can write to the log file
        try:
            with open(log_path, 'a') as _:
                pass
        except Exception as e:
            raise PermissionError(f"Cannot write to audit log: {str(e)}")
            
    def log_command_execution(
        self,
        command: str,
        arguments: List[str],
        path: str,
        status: str,
        user: str,
        error_message: Optional[str] = None
    ) -> None:
        """
        Log a command execution event.
        
        Args:
            command: The command that was executed
            arguments: List of command arguments
            path: Target path for the command
            status: Execution status (success/failed)
            user: User who executed the command
            error_message: Optional error message if execution failed
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "arguments": arguments,
            "path": path,
            "status": status,
            "user": user
        }
        
        if error_message:
            log_entry["error"] = error_message
            
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            # If we can't write to the audit log, this is a serious error
            raise RuntimeError(f"Failed to write to audit log: {str(e)}")