"""MCP server for secure command execution with full security and audit capabilities"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP, Context
from mcp_command_server.security.validator import CommandValidator, ValidationError
from mcp_command_server.security.sanitizer import CommandSanitizer
from mcp_command_server.security.confirmation import UserConfirmationHandler
from mcp_command_server.security.audit import AuditLogger

class CommandServer:
    """MCP server for secure command execution"""
    
    DEFAULT_ALLOWED_COMMANDS = {
        "ls": {"args": ["-l", "-a", "-h"], "paths": ["/"]},
        "cd": {"args": [], "paths": ["/"]},
        "npm": {"args": ["run", "dev", "install", "test"], "paths": ["./"]},
        "python": {"args": ["-m", "pytest", "run"], "paths": ["./"]},
        "pip": {"args": ["install", "list", "freeze"], "paths": ["./"]},
        "git": {"args": ["status", "pull", "push", "checkout"], "paths": ["./"]},
    }
    
    def __init__(
        self,
        allowed_commands: Optional[Dict[str, Dict[str, Any]]] = None,
        audit_log_path: str = "logs/audit.log",
        user: str = "default_user"
    ):
        """
        Initialize the command execution server.
        
        Args:
            allowed_commands: Dictionary of allowed commands and their configurations
            audit_log_path: Path to audit log file
            user: Username for audit logging
        """
        self.mcp = FastMCP("CommandServer", dependencies=["asyncio", "subprocess"])
        self.allowed_commands = allowed_commands or self.DEFAULT_ALLOWED_COMMANDS
        self.user = user
        
        # Initialize security components
        self.validator = CommandValidator(self.allowed_commands)
        self.sanitizer = CommandSanitizer()
        self.confirmation = UserConfirmationHandler()
        self.audit = AuditLogger(audit_log_path)
        
        # Register MCP tools
        self._register_tools()
        
    def _register_tools(self) -> None:
        """Register all command execution tools with MCP server"""
        
        @self.mcp.tool()
        async def execute_command(
            command: str,
            args: List[str],
            path: str,
            ctx: Context
        ) -> str:
            """
            Execute a system command with full security checks.
            
            Args:
                command: Command to execute
                args: Command arguments
                path: Working directory
                ctx: MCP context for progress reporting
                
            Returns:
                str: Command output or error message
            """
            try:
                # Security validation
                ctx.info(f"Validating command: {command} {' '.join(args)}")
                await ctx.report_progress(10, 100)
                
                # Sanitize inputs
                command = self.sanitizer.sanitize_command(command)
                args = self.sanitizer.sanitize_arguments(args)
                path = self.sanitizer.sanitize_path(path)
                
                await ctx.report_progress(30, 100)
                
                # Validate against allowed commands
                self.validator.validate_command(command, args, path)
                
                await ctx.report_progress(50, 100)
                
                # Get user confirmation
                if not self.confirmation.require_confirmation(command, args, path, self.user):
                    raise PermissionError("Command execution not confirmed by user")
                    
                await ctx.report_progress(70, 100)
                
                # Execute command
                result = await self._execute_command_async(command, args, path)
                
                # Log successful execution
                self.audit.log_command_execution(
                    command=command,
                    arguments=args,
                    path=path,
                    status="success",
                    user=self.user
                )
                
                await ctx.report_progress(100, 100)
                return result
                
            except Exception as e:
                # Log failure
                self.audit.log_command_execution(
                    command=command,
                    arguments=args,
                    path=path,
                    status="failed",
                    user=self.user,
                    error_message=str(e)
                )
                raise
                
        @self.mcp.tool()
        async def check_command_allowed(
            command: str,
            args: List[str],
            path: str
        ) -> bool:
            """
            Check if a command would be allowed without executing it.
            
            Args:
                command: Command to check
                args: Command arguments
                path: Working directory
                
            Returns:
                bool: True if command would be allowed
            """
            try:
                # Sanitize and validate
                command = self.sanitizer.sanitize_command(command)
                args = self.sanitizer.sanitize_arguments(args)
                path = self.sanitizer.sanitize_path(path)
                self.validator.validate_command(command, args, path)
                return True
            except (ValueError, ValidationError):
                return False
                
    async def _execute_command_async(
        self,
        command: str,
        args: List[str],
        path: str
    ) -> str:
        """
        Execute a command asynchronously.
        
        Args:
            command: Command to execute
            args: Command arguments
            path: Working directory
            
        Returns:
            str: Command output
            
        Raises:
            subprocess.CalledProcessError: If command execution fails
        """
        cmd = [command] + args
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Command execution failed"
            raise subprocess.CalledProcessError(
                process.returncode,
                cmd,
                output=stdout,
                stderr=stderr
            )
            
        return stdout.decode()
        
    def run(self) -> None:
        """Start the MCP server"""
        self.mcp.run()