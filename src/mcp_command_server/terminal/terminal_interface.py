import asyncio
import subprocess
from typing import Optional, Dict, AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
import shlex
import logging
import signal
from asyncio.subprocess import Process

# Configure logging
logger = logging.getLogger(__name__)

class TerminalError(Exception):
    """Base exception for terminal-related errors"""
    pass

class CommandTimeoutError(TerminalError):
    """Exception raised when command execution times out"""
    pass

@dataclass
class CommandResult:
    """Container for command execution results"""
    stdout: str
    stderr: str
    returncode: int
    command: str

class TerminalInterface:
    """Handles terminal command execution and process management"""

    async def execute(
        self,
        command: str,
        timeout: Optional[float] = 60.0,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        input_data: Optional[str] = None
    ) -> CommandResult:
        """
        Execute a command and return its output.
        
        Args:
            command: The command to execute
            timeout: Maximum execution time in seconds
            env: Optional environment variables
            cwd: Optional working directory
            input_data: Optional input data for interactive commands
            
        Returns:
            CommandResult containing stdout, stderr, and return code
            
        Raises:
            TerminalError: If command execution fails
            CommandTimeoutError: If command exceeds timeout
        """
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd,
                stdin=asyncio.subprocess.PIPE if input_data else None
            )

            # Handle input data if provided
            if input_data:
                if not process.stdin:
                    raise TerminalError("Failed to open stdin for process")
                try:
                    process.stdin.write(input_data.encode())
                    await process.stdin.drain()
                finally:
                    process.stdin.close()

            try:
                # Wait for command completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                try:
                    # Try graceful termination first
                    process.terminate()
                    await asyncio.sleep(0.1)
                    if process.returncode is None:
                        process.kill()
                except Exception as e:
                    logger.error(f"Error killing process: {e}")
                raise CommandTimeoutError(f"Command timed out after {timeout} seconds: {command}")

            if process.returncode != 0:
                logger.error(f"Command failed: {command}")
                logger.error(f"stderr: {stderr.decode()}")
                raise TerminalError(
                    f"Command execution failed with return code {process.returncode}: {stderr.decode()}"
                )

            return CommandResult(
                stdout=stdout.decode(),
                stderr=stderr.decode(),
                returncode=process.returncode,
                command=command
            )

        except asyncio.CancelledError:
            logger.warning(f"Command execution cancelled: {command}")
            raise
        except Exception as e:
            if not isinstance(e, (TerminalError, CommandTimeoutError)):
                logger.error(f"Unexpected error executing command: {e}")
            raise

    async def execute_streaming(
        self,
        command: str,
        timeout: Optional[float] = 60.0,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute a command and stream its output line by line.
        
        Args:
            command: The command to execute
            timeout: Maximum execution time in seconds
            env: Optional environment variables
            cwd: Optional working directory
            
        Yields:
            Lines of output from the command
            
        Raises:
            TerminalError: If command execution fails
            CommandTimeoutError: If command exceeds timeout
        """
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=cwd
        )

        async def read_stream(stream: asyncio.StreamReader) -> AsyncGenerator[str, None]:
            while True:
                line = await stream.readline()
                if not line:
                    break
                yield line.decode()

        try:
            async def stream_with_timeout():
                async for line in read_stream(process.stdout):
                    yield line

            async with asyncio.timeout(timeout):
                async for line in stream_with_timeout():
                    yield line

            await process.wait()
            if process.returncode != 0:
                stderr = await process.stderr.read()
                raise TerminalError(
                    f"Command execution failed with return code {process.returncode}: {stderr.decode()}"
                )

        except asyncio.TimeoutError:
            process.terminate()
            await asyncio.sleep(0.1)
            if process.returncode is None:
                process.kill()
            raise CommandTimeoutError(f"Command timed out after {timeout} seconds: {command}")

        except Exception as e:
            process.kill()
            if not isinstance(e, (TerminalError, CommandTimeoutError)):
                logger.error(f"Unexpected error in streaming execution: {e}")
            raise

    async def execute_async(
        self,
        command: str,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None
    ) -> Process:
        """
        Execute a command asynchronously and return the process object.
        
        Args:
            command: The command to execute
            env: Optional environment variables
            cwd: Optional working directory
            
        Returns:
            asyncio.subprocess.Process object
            
        Raises:
            TerminalError: If command execution fails to start
        """
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd
            )
            return process
        except Exception as e:
            logger.error(f"Failed to start async process: {e}")
            raise TerminalError(f"Failed to start command: {e}")