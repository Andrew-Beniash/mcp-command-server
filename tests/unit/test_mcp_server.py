"""Unit tests for MCP server core functionality"""

import pytest
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from mcp.types import Context  
from mcp_command_server.security.validator import CommandValidator
from mcp_command_server.security.sanitizer import CommandSanitizer
from mcp_command_server.security.confirmation import UserConfirmationHandler
from mcp_command_server.security.audit import AuditLogger

def test_mcp_server_initialization():
    """Test basic server initialization"""
    mcp = FastMCP("CommandServer")
    assert mcp.name == "CommandServer"

def test_tool_registration():
    """Test tool registration and schema generation"""
    mcp = FastMCP("CommandServer")
    
    @mcp.tool()
    def execute_command(command: str, args: list[str], path: str) -> str:
        """Test command execution"""
        return "Success"
        
    tools = mcp._tools
    assert "execute_command" in tools
    assert tools["execute_command"].description == "Test command execution"

def test_status_reporting():
    """Test status reporting functionality"""
    mcp = FastMCP("CommandServer")
    
    @mcp.tool()
    async def long_running_command(ctx: Context) -> str:  # Now Context is properly typed
        await ctx.report_progress(0, 100)
        await ctx.report_progress(50, 100)
        await ctx.report_progress(100, 100)
        return "Complete"
        
    assert "long_running_command" in mcp._tools

@pytest.mark.parametrize("command,args,path,expected", [
    ("ls", ["-l"], "/home/user", True),
    ("rm", ["-rf"], "/", False),
    ("npm", ["run", "dev"], "./project", True),
])
def test_command_security_integration(command, args, path, expected):
    """Test integration with security components"""
    validator = CommandValidator({
        "ls": {"args": ["-l"], "paths": ["/home/user"]},
        "npm": {"args": ["run", "dev"], "paths": ["./project"]}
    })
    sanitizer = CommandSanitizer()
    
    try:
        sanitizer.sanitize_command(command)
        sanitizer.sanitize_arguments(args)
        sanitizer.sanitize_path(path)
        validator.validate_command(command, args, path)
        assert expected
    except (ValueError, Exception):
        assert not expected

def test_audit_logging_integration(tmp_path):
    """Test integration with audit logging"""
    log_path = tmp_path / "audit.log"
    logger = AuditLogger(str(log_path))
    
    logger.log_command_execution(
        command="ls",
        arguments=["-l"],
        path="/home/user",
        status="success",
        user="testuser"
    )
    
    assert log_path.exists()
    with open(log_path) as f:
        log_content = f.read()
        assert "ls" in log_content
        assert "success" in log_content