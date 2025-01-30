# MCP Command Server Documentation

## Overview

MCP Command Server is a secure Model Context Protocol (MCP) server implementation that allows controlled execution of system commands through Large Language Models (LLMs) like Claude.

## Table of Contents

- [Installation](#installation)
- [Security Guidelines](#security-guidelines)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

- Python 3.10 or higher
- pip or uv package manager
- Claude Desktop (for integration)
- Visual Studio Code (recommended for development)

### Quick Install

```bash
# Using uv (recommended)
uv pip install mcp-command-server

# Using pip
pip install mcp-command-server
```

### Development Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/mcp-command-server.git
cd mcp-command-server
```

2. Create and activate virtual environment:

```bash
# Using uv
uv venv
source .venv/bin/activate  # On Unix/macOS
.venv\Scripts\activate     # On Windows
```

3. Install dependencies:

```bash
uv pip install -e ".[dev]"
```

### Claude Desktop Integration

1. Open Claude Desktop configuration:

```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

2. Add server configuration:

```json
{
  "mcpServers": {
    "command-server": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_command_server"],
      "env": {
        "ALLOWED_COMMANDS": "ls,pwd,echo"
      }
    }
  }
}
```

## Security Guidelines

### Command Execution Safety

1. **Whitelist Commands**

   - Only explicitly allowed commands can be executed
   - Configure through `ALLOWED_COMMANDS` environment variable
   - Separate multiple commands with commas

2. **Input Sanitization**

   - All command inputs are sanitized
   - Special characters are escaped
   - Path traversal is prevented

3. **User Confirmation**

   - Commands require explicit user approval
   - Clear display of command to be executed
   - Timeout for confirmation requests

4. **Audit Logging**
   - All command executions are logged
   - Includes timestamp, command, and result
   - Logs stored in `~/Library/Logs/Claude/mcp-command-server.log`

### Environment Variables

| Variable             | Description                                     | Required | Default |
| -------------------- | ----------------------------------------------- | -------- | ------- |
| ALLOWED_COMMANDS     | Comma-separated list of allowed commands        | Yes      | None    |
| LOG_LEVEL            | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | No       | INFO    |
| CONFIRMATION_TIMEOUT | Seconds to wait for user confirmation           | No       | 30      |

## API Reference

### Tools

#### `execute_command`

Executes a system command from the allowed list.

```python
@mcp.tool()
async def execute_command(command: str, args: list[str]) -> str:
    """Execute a system command.

    Args:
        command: The command to execute (must be in whitelist)
        args: List of command arguments

    Returns:
        Command output as string

    Raises:
        SecurityError: If command not in whitelist
        ValidationError: If arguments invalid
    """
```

#### `list_allowed_commands`

Returns the list of allowed commands.

```python
@mcp.tool()
def list_allowed_commands() -> list[str]:
    """Get list of allowed commands.

    Returns:
        List of command names that can be executed
    """
```

### Resources

#### `audit_log`

Access the command execution audit log.

```python
@mcp.resource("audit://log")
def get_audit_log() -> str:
    """Get the command execution audit log.

    Returns:
        Formatted audit log entries
    """
```

## Usage Examples

### Basic Command Execution

```python
# List directory contents
response = await client.call_tool(
    "execute_command",
    {
        "command": "ls",
        "args": ["-la"]
    }
)

# Print working directory
response = await client.call_tool(
    "execute_command",
    {
        "command": "pwd",
        "args": []
    }
)
```

### Claude Desktop Interaction

Example conversation with Claude:

```
Human: What files are in the current directory?

Claude: I'll help you list the files in the current directory using the command server.

[Tool call: execute_command with args: ["ls", "-la"]]
Awaiting your confirmation to run: ls -la

[Output after confirmation]
total 56
drwxr-xr-x  10 user  staff   320 Mar 14 15:30 .
drwxr-xr-x   5 user  staff   160 Mar 14 15:30 ..
-rw-r--r--   1 user  staff  2516 Mar 14 15:30 README.md
drwxr-xr-x   4 user  staff   128 Mar 14 15:30 src
drwxr-xr-x   4 user  staff   128 Mar 14 15:30 tests

Here's a breakdown of the files and directories in your current location:

1. README.md - Documentation file
2. src/ - Source code directory
3. tests/ - Test files directory

Would you like me to examine any of these files or directories in more detail?

### Error Handling

When using the command server, you may encounter these common errors:

1. **Command Not Allowed**
```

Error: Command 'rm' is not in the allowed commands list
Solution: Add the command to ALLOWED_COMMANDS or use an allowed alternative

```

2. **Invalid Arguments**
```

Error: Invalid argument format: contains unsafe characters
Solution: Remove special characters or properly escape them

```

3. **Timeout**
```

Error: User confirmation timeout after 30 seconds
Solution: Respond to the confirmation prompt more quickly or adjust CONFIRMATION_TIMEOUT

````

## Troubleshooting

### Common Issues

#### Server Not Starting

**Problem**: Claude Desktop can't start the command server.

**Solutions**:
1. Verify Python installation:
```bash
python --version  # Should be 3.10 or higher
````

2. Check configuration path:

```bash
ls ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

3. Validate environment setup:

```bash
echo $ALLOWED_COMMANDS  # Should show allowed commands
```

#### Permission Errors

**Problem**: Commands fail with permission errors.

**Solutions**:

1. Check file permissions:

```bash
ls -l /path/to/directory
```

2. Verify user permissions:

```bash
whoami
groups
```

3. Update file permissions if needed:

```bash
chmod +r /path/to/file  # Add read permission
```

#### Logging Issues

**Problem**: Can't find command execution logs.

**Solutions**:

1. Check log file location:

```bash
ls ~/Library/Logs/Claude/mcp-command-server.log
```

2. Verify logging configuration:

```bash
echo $LOG_LEVEL
```

3. Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
```

### Getting Help

1. **Check Logs**:

```bash
tail -f ~/Library/Logs/Claude/mcp-command-server.log
```

2. **Issue Reporting**:

- Visit our GitHub Issues page
- Include log output
- Describe your environment
- List steps to reproduce

3. **Community Support**:

- Join our Discord server
- Post in GitHub Discussions
- Check Stack Overflow tags

## Extending Commands

### Adding New Commands

There are two ways to extend the available commands:

1. **Environment Configuration (Basic)**

Add commands to the `ALLOWED_COMMANDS` environment variable:

```bash
# In your shell or .env file
export ALLOWED_COMMANDS="ls,pwd,echo,cat,grep,find"

# Or in claude_desktop_config.json
{
  "mcpServers": {
    "command-server": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_command_server"],
      "env": {
        "ALLOWED_COMMANDS": "ls,pwd,echo,cat,grep,find"
      }
    }
  }
}
```

2. **Custom Command Configuration (Advanced)**

Create a command configuration file (`commands.yaml`):

```yaml
commands:
  ls:
    allowed_flags: ["-l", "-a", "-h", "-t"]
    allowed_paths: ["~/Documents", "~/Downloads"]
    description: "List directory contents"

  grep:
    allowed_flags: ["-i", "-v", "-n"]
    max_file_size: "10MB"
    description: "Search file contents"

  find:
    allowed_flags: ["-name", "-type"]
    excluded_paths: ["/etc", "/var"]
    description: "Search for files"
```

Then reference it in your configuration:

```json
{
  "mcpServers": {
    "command-server": {
      "command": "uv",
      "args": ["run", "python", "-m", "mcp_command_server"],
      "env": {
        "COMMAND_CONFIG": "/path/to/commands.yaml"
      }
    }
  }
}
```

### Security Considerations

When adding new commands:

1. **Risk Assessment**

   - Evaluate what the command can access
   - Consider potential misuse scenarios
   - Review command flags and options

2. **Access Control**

   - Limit commands to specific directories
   - Restrict dangerous flags
   - Consider read-only vs write operations

3. **Resource Limits**
   - Set timeouts for long-running commands
   - Limit output size
   - Restrict file size for operations

### Command Categories

Here are common command categories you might want to add:

1. **File Operations**

   ```
   cat, less, head, tail, grep, find
   ```

2. **Directory Operations**

   ```
   ls, pwd, cd, tree, du
   ```

3. **System Information**

   ```
   df, top, ps, free, uptime
   ```

4. **Network Tools**

   ```
   ping, curl, wget, netstat
   ```

5. **Text Processing**
   ```
   grep, sed, awk, sort, uniq
   ```

### Example: Adding Git Commands

To add Git support:

1. Add commands to allowlist:

```bash
export ALLOWED_COMMANDS="git-status,git-log,git-branch"
```

2. Create command configurations:

```yaml
commands:
  git-status:
    allowed_flags: ["--short", "--branch"]
    working_dir: "~/projects"
    description: "Show working tree status"

  git-log:
    allowed_flags: ["--oneline", "--graph", "-n"]
    max_entries: 100
    description: "Show commit logs"
```

3. Implement custom validation:

```python
@mcp.tool()
async def execute_git_command(command: str, args: list[str]) -> str:
    """Execute git commands safely.

    Args:
        command: Git subcommand (status, log, etc.)
        args: Command arguments

    Returns:
        Command output
    """
    # Your implementation here
```

### Testing New Commands

Always test new commands thoroughly:

1. **Unit Tests**

```python
def test_git_command_validation():
    # Test command validation
    assert validate_git_command("status", ["--short"]) is True
    assert validate_git_command("push", []) is False  # Dangerous command
```

2. **Integration Tests**

```python
async def test_git_command_execution():
    # Test actual execution
    result = await execute_git_command("status", ["--short"])
    assert result.startswith("## main")
```

### Common Issues

1. **Permission Errors**

   - Make sure the server has necessary permissions
   - Check file/directory ownership
   - Verify user permissions

2. **Command Not Found**

   - Verify command is in system PATH
   - Check command spelling
   - Confirm command installation

3. **Configuration Issues**
   - Validate YAML syntax
   - Check file paths
   - Verify environment variables

## License

This project is licensed under the MIT License. See the LICENSE file for details.
