#!/usr/bin/env python3
"""
Security utilities for Warp Chat Archiver
Provides safe path validation and input sanitization
"""

import os
import re
from pathlib import Path
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass


def safe_path(user_path: Union[str, Path], 
              base_dir: Optional[Union[str, Path]] = None,
              allow_absolute: bool = True,
              must_exist: bool = False) -> Path:
    """
    Validate and sanitize a user-provided path to prevent directory traversal attacks.
    
    Args:
        user_path: User-provided path (can be relative or absolute)
        base_dir: Base directory to restrict paths to (optional)
        allow_absolute: Whether to allow absolute paths
        must_exist: Whether the path must exist
        
    Returns:
        Validated Path object
        
    Raises:
        SecurityError: If path validation fails
        FileNotFoundError: If must_exist=True and path doesn't exist
    """
    try:
        # Convert to Path object and resolve
        if isinstance(user_path, str):
            # Basic input sanitization
            if len(user_path) > 1000:  # Reasonable path length limit
                raise SecurityError("Path too long")
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'\.\.[\\/]',  # Directory traversal
                r'[\\/]\.\.[\\/]',  # Directory traversal in middle
                r'[\\/]\.\.$',  # Directory traversal at end
                r'^\.\.[\\/]',  # Directory traversal at start
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, user_path):
                    raise SecurityError(f"Potential directory traversal detected: {user_path}")
            
            path = Path(user_path)
        else:
            path = user_path
        
        # Resolve to absolute path (this handles .. and . components)
        try:
            resolved_path = path.resolve()
        except (OSError, ValueError) as e:
            raise SecurityError(f"Invalid path: {e}")
        
        # Check if absolute paths are allowed
        if not allow_absolute and resolved_path.is_absolute():
            # For relative paths, convert back to relative from current directory
            try:
                resolved_path = resolved_path.relative_to(Path.cwd())
            except ValueError:
                raise SecurityError("Path outside current directory not allowed")
        
        # Check base directory restriction
        if base_dir:
            base_path = Path(base_dir).resolve()
            try:
                resolved_path.relative_to(base_path)
            except ValueError:
                raise SecurityError(f"Path outside allowed directory: {base_path}")
        
        # Check existence if required
        if must_exist and not resolved_path.exists():
            raise FileNotFoundError(f"Path does not exist: {resolved_path}")
        
        logger.debug(f"Path validation successful: {user_path} -> {resolved_path}")
        return resolved_path
        
    except SecurityError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in path validation: {e}")
        raise SecurityError(f"Path validation failed: {e}")


def safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize a filename to prevent various filesystem attacks.
    
    Args:
        filename: User-provided filename
        max_length: Maximum allowed filename length
        
    Returns:
        Sanitized filename
        
    Raises:
        SecurityError: If filename cannot be safely sanitized
    """
    if not filename or not isinstance(filename, str):
        raise SecurityError("Invalid filename")
    
    # Remove or replace dangerous characters
    # Keep alphanumeric, dots, hyphens, underscores, spaces
    sanitized = re.sub(r'[^\w\s.-]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip('. ')
    
    # Check for reserved names (Windows)
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    if sanitized.upper() in reserved_names:
        sanitized = f"file_{sanitized}"
    
    # Enforce length limit
    if len(sanitized) > max_length:
        # Keep extension if present
        if '.' in sanitized:
            name, ext = sanitized.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            sanitized = name[:max_name_length] + '.' + ext
        else:
            sanitized = sanitized[:max_length]
    
    if not sanitized:
        raise SecurityError("Filename becomes empty after sanitization")
    
    logger.debug(f"Filename sanitized: {filename} -> {sanitized}")
    return sanitized


def validate_export_path(export_path: str, base_export_dir: Optional[str] = None) -> Path:
    """
    Validate an export path for security.
    
    Args:
        export_path: User-provided export path
        base_export_dir: Base directory for exports (optional)
        
    Returns:
        Validated export path
    """
    try:
        # Use safe_path with export-specific settings
        safe_export_path = safe_path(
            export_path,
            base_dir=base_export_dir,
            allow_absolute=True,
            must_exist=False
        )
        
        # Ensure parent directory exists or can be created
        parent_dir = safe_export_path.parent
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created export directory: {parent_dir}")
            except OSError as e:
                raise SecurityError(f"Cannot create export directory: {e}")
        
        return safe_export_path
        
    except Exception as e:
        logger.error(f"Export path validation failed: {e}")
        raise


def validate_import_path(import_path: str) -> Path:
    """
    Validate an import file path for security.
    
    Args:
        import_path: User-provided import file path
        
    Returns:
        Validated import path
    """
    try:
        # Import files must exist
        safe_import_path = safe_path(
            import_path,
            allow_absolute=True,
            must_exist=True
        )
        
        # Additional checks for import files
        if not safe_import_path.is_file():
            raise SecurityError("Import path must be a file")
        
        # Check file size (reasonable limit: 1GB)
        max_file_size = 1024 * 1024 * 1024  # 1GB
        if safe_import_path.stat().st_size > max_file_size:
            raise SecurityError(f"Import file too large (max {max_file_size} bytes)")
        
        return safe_import_path
        
    except Exception as e:
        logger.error(f"Import path validation failed: {e}")
        raise


if __name__ == "__main__":
    # Basic tests
    print("Testing security_utils...")
    
    # Test safe_path
    try:
        safe_path("normal_file.txt")
        print("✅ Normal path OK")
    except SecurityError:
        print("❌ Normal path failed")
    
    # Test directory traversal detection
    try:
        safe_path("../../../etc/passwd")
        print("❌ Directory traversal not detected")
    except SecurityError:
        print("✅ Directory traversal detected")
    
    # Test filename sanitization
    try:
        result = safe_filename("test<>file.txt")
        print(f"✅ Filename sanitized: test<>file.txt -> {result}")
    except SecurityError as e:
        print(f"❌ Filename sanitization failed: {e}")
    
    print("Security utils tests completed")