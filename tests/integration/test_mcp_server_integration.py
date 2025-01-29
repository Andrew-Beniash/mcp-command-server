"""Integration tests for MCP server functionality"""

import pytest
import asyncio
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import Context 
from mcp_command_server.security.validator import CommandValidator
from mcp_command_server.security.sanitizer import CommandSanitizer
from mcp_command_server.security.confirmation import UserConfirmationHandler
from mcp_command_server.security.audit import AuditLogger

@pytest.fixture
def mcp_server(tmp_path):
    """Fixture providing configured MCP server"""
    audit_log = tmp_path / "audit.log"
    allowed_commands = {
        "ls": {"args": ["-l", "-a"], "paths": ["/home", "/tmp"]},
        "cd": {"args": [], "paths": ["/home", "/tmp"]},
        "npm": {"args": ["run", "dev", "install"], "paths": ["./"]},
        "python": {"args": ["-m", "pytest"], "paths": ["./"]},
    }
    
    mcp = FastMCP("CommandServer")
    validator = CommandValidator(allowed_commands)
    sanitizer = CommandSanitizer()
    confirmation = UserConfirmationHandler()
    audit = AuditLogger(str(audit_log))
    
    return mcp, validator, sanitizer, confirmation, audit

@pytest.mark.asyncio
async def test_command_execution_flow(mcp_server):
    """Test complete command execution flow with all security components"""
    mcp, validator, sanitizer, confirmation, audit = mcp_server
    
    @mcp.tool()
    async def execute_command(
        command: str, 
        args: list[str], 
        path: str,
        ctx: "Context"
    ) -> str:
        # Test the complete flow from validation to execution
        try:
            # Security checks
            sanitizer.sanitize_command(command)
            sanitizer.sanitize_arguments(args)
            sanitizer.sanitize_path(path)
            validator.validate_command(command, args, path)
            
            # Simulate execution
            await ctx.report_progress(50, 100)
            
            # Log success
            audit.log_command_execution(
                command=command,
                arguments=args,
                path=path,
                status="success",
                user="testuser"
            )
            
            return "Command executed successfully"
            
        except Exception as e:
            audit.log_command_execution(
                command=command,
                arguments=args,
                path=path,
                status="failed",
                user="testuser",
                error_message=str(e)
            )
            raise

@pytest.mark.asyncio
async def test_command_execution_with_progress(mcp_server):
    """Test command execution with progress reporting"""
    mcp, _, _, _, _ = mcp_server
    
    progress_updates = []
    
    @mcp.tool()
    async def long_running_command(ctx: "Context") -> str:
        total_steps = 5
        for i in range(total_steps):
            await asyncio.sleep(0.1)  # Simulate work
            progress = ((i + 1) / total_steps) * 100
            await ctx.report_progress(progress, 100)
            progress_updates.append(progress)
        return "Long running command completed"
    
    assert len(progress_updates) > 0
    assert progress_updates[-1] == 100.0

@pytest.mark.asyncio
async def test_multiple_concurrent_commands(mcp_server):
    """Test handling multiple concurrent command executions"""
    mcp, validator, sanitizer, confirmation, audit = mcp_server
    
    @mcp.tool()
    async def execute_parallel_commands(
        commands: list[dict],
        ctx: "Context"
    ) -> list[str]:
        results = []
        for cmd in commands:
            try:
                sanitizer.sanitize_command(cmd["command"])
                sanitizer.sanitize_arguments(cmd["args"])
                sanitizer.sanitize_path(cmd["path"])
                validator.validate_command(cmd["command"], cmd["args"], cmd["path"])
                
                # Simulate execution
                await asyncio.sleep(0.1)
                results.append(f"Executed: {cmd['command']}")
                
            except Exception as e:
                results.append(f"Failed: {cmd['command']} - {str(e)}")
                
        return results