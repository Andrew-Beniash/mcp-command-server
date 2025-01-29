import json
import os
import time
import aiofiles  
from typing import List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

@dataclass
class CommandRecord:
    """Represents a command execution record"""
    timestamp: datetime
    command: str
    args: list
    path: str
    user: str
    status: str
    risk_level: str
    duration: Optional[float] = None
    error: Optional[str] = None

class CommandLogger:
    """Handles command execution logging and history"""
    
    # Sensitive parameters that should be masked
    SENSITIVE_PARAMS = ["-p", "--password", "PASSWORD", "TOKEN", "KEY", "SECRET"]
    
    def __init__(self, log_file: Path):
        """
        Initialize the command logger
        
        Args:
            log_file: Path to the log file
        """
        self.log_file = log_file
        self._ensure_log_directory()
    
    async def log_command(self, record: CommandRecord):
        """
        Log a command execution record
        
        Args:
            record: CommandRecord to log
        """
        # Mask sensitive data
        masked_record = self._mask_sensitive_data(record)
        
        # Convert to JSON-serializable format
        log_entry = {
            **asdict(masked_record),
            "timestamp": masked_record.timestamp.isoformat()
        }
        
        # Append to log file
        async with aiofiles.open(self.log_file, mode='a') as f:
            await f.write(json.dumps(log_entry) + '\n')
    
    async def get_command_history(self, limit: int = 100) -> List[CommandRecord]:
        """
        Retrieve command execution history
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List[CommandRecord]: List of command records
        """
        records = []
        
        if not os.path.exists(self.log_file):
            return records
            
        async with aiofiles.open(self.log_file, mode='r') as f:
            async for line in f:
                if line.strip():
                    entry = json.loads(line)
                    entry['timestamp'] = datetime.fromisoformat(entry['timestamp'])
                    records.append(CommandRecord(**entry))
                
                if len(records) >= limit:
                    break
                    
        return records
    
    def _ensure_log_directory(self):
        """Ensure log directory exists"""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
    
    def _mask_sensitive_data(self, record: CommandRecord) -> CommandRecord:
        """
        Mask sensitive data in command record
        
        Args:
            record: CommandRecord to mask
            
        Returns:
            CommandRecord: Masked record
        """
        masked_args = []
        skip_next = False
        
        for i, arg in enumerate(record.args):
            if skip_next:
                masked_args.append("[MASKED]")
                skip_next = False
                continue
                
            if arg in self.SENSITIVE_PARAMS:
                masked_args.append(arg)
                skip_next = True
            else:
                masked_args.append(arg)
                
        return CommandRecord(
            timestamp=record.timestamp,
            command=record.command,
            args=masked_args,
            path=record.path,
            user=record.user,
            status=record.status,
            risk_level=record.risk_level,
            duration=record.duration,
            error=record.error
        )