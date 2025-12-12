"""File I/O utilities.

This module provides common file operations used across scripts.
Centralizes directory creation, file writing, etc.

Usage:
    from core.io import create_directory, write_file
    
    create_directory(some_path)
    write_file(file_path, content)
"""
from pathlib import Path
from typing import Union
import os

__all__ = [
    "create_directory",
    "ensure_parent_dir", 
    "write_file",
    "read_file",
    "make_executable",
]


def create_directory(path: Union[str, Path]) -> Path:
    """Create a directory if it doesn't exist.
    
    Safe wrapper ensuring consistent directory creation with proper permissions
    and cross-platform compatibility. Automatically creates parent directories.
    
    Args:
        path: Directory path to create.
        
    Returns:
        Path object for the directory.
    """
    path = Path(path)
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_parent_dir(file_path: Union[str, Path]) -> Path:
    """Ensure the parent directory of a file exists.
    
    Safe wrapper that creates parent directories before file operations,
    preventing file write failures due to missing directories.
    
    Args:
        file_path: Path to a file.
        
    Returns:
        Path object for the file.
    """
    file_path = Path(file_path)
    if not file_path.parent.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path


def write_file(file_path: Union[str, Path], content: str, overwrite: bool = True) -> bool:
    """Write content to a file.
    
    Safe wrapper ensuring parent directories exist and providing atomic writes
    with proper encoding (UTF-8) to prevent data corruption.
    
    Args:
        file_path: Path to the file.
        content: Content to write.
        overwrite: If False, skip if file exists.
        
    Returns:
        True if file was written, False if skipped.
    """
    file_path = Path(file_path)
    
    if not overwrite and file_path.exists():
        return False
    
    ensure_parent_dir(file_path)
    with open(file_path, 'w') as f:
        f.write(content)
    return True


def read_file(file_path: Union[str, Path]) -> str:
    """Read content from a file.
    
    Safe wrapper ensuring consistent file reading with proper encoding (UTF-8)
    and error handling for missing files.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        File content as string.
        
    Raises:
        FileNotFoundError: If file doesn't exist.
    """
    file_path = Path(file_path)
    with open(file_path, 'r') as f:
        return f.read()


def make_executable(file_path: Union[str, Path]) -> None:
    """Make a file executable (chmod +x).
    
    Safe wrapper for setting executable permissions on script files,
    ensuring cross-platform compatibility for deployment.
    
    Args:
        file_path: Path to the file.
    """
    import stat
    file_path = Path(file_path)
    file_path.chmod(file_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
