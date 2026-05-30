#!/usr/bin/env python3
"""
Codebase scanner for Cartographer skill.
Scans a directory and provides file tree with token counts using tiktoken.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

try:
    import tiktoken
except ImportError:
    print("Error: tiktoken not installed. Install with: pip install tiktoken", file=sys.stderr)
    sys.exit(1)

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(text))
    except Exception as e:
        print(f"Warning: Could not count tokens: {e}", file=sys.stderr)
        return 0

def should_skip_file(file_path: Path, root_path: Path) -> bool:
    """Determine if a file should be skipped."""
    # Skip binary files and common non-code files
    skip_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.rar', '.7z',
        '.mp4', '.avi', '.mov', '.wmv', '.flv',
        '.mp3', '.wav', '.flac', '.aac',
        '.pyc', '.pyo', '__pycache__',
        '.log', '.lock', '.tmp', '.temp'
    }

    # Skip common directories
    skip_dirs = {
        'node_modules', '.git', '.svn', '.hg', '.DS_Store',
        '__pycache__', '.pytest_cache', '.next', '.nuxt',
        'build', 'dist', '.build', 'target', 'out',
        '.vscode', '.idea', '.cursor'
    }

    if file_path.suffix.lower() in skip_extensions:
        return True

    relative_parts = file_path.relative_to(root_path).parts

    # The workspace root itself may legitimately be a hidden directory
    # (for example ~/.cursor). Evaluate only descendants of the root.
    for part in relative_parts:
        if part in skip_dirs or part.startswith('.'):
            return True

    return False

def scan_directory(root_path: Path, max_file_size: int = 1024*1024) -> Tuple[Dict, int, int]:
    """
    Scan directory and return file tree with token counts.

    Returns:
        tuple: (file_tree_dict, total_files, total_tokens)
    """
    file_tree = {}
    total_files = 0
    total_tokens = 0

    try:
        for file_path in root_path.rglob('*'):
            if not file_path.is_file():
                continue

            if should_skip_file(file_path, root_path):
                continue

            try:
                # Check file size
                file_size = file_path.stat().st_size
                if file_size > max_file_size:
                    continue

                # Read file content
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except (UnicodeDecodeError, PermissionError):
                    continue

                # Count tokens
                token_count = count_tokens(content)
                total_tokens += token_count
                total_files += 1

                # Build nested dictionary structure
                parts = file_path.relative_to(root_path).parts
                current = file_tree
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                current[parts[-1]] = {
                    'tokens': token_count,
                    'size': file_size,
                    'path': str(file_path.relative_to(root_path))
                }

            except Exception as e:
                print(f"Warning: Could not process {file_path}: {e}", file=sys.stderr)
                continue

    except Exception as e:
        print(f"Error scanning directory: {e}", file=sys.stderr)
        sys.exit(1)

    return file_tree, total_files, total_tokens

def format_tree(tree: Dict, prefix: str = "", is_last: bool = True) -> List[str]:
    """Format file tree as ASCII art with token counts."""
    lines = []

    if not tree:
        return lines

    items = list(tree.items())
    for i, (name, value) in enumerate(items):
        is_last_item = i == len(items) - 1
        connector = "└── " if is_last_item else "├── "

        is_file_metadata = isinstance(value, dict) and {
            'tokens', 'size', 'path'
        }.issubset(value.keys())

        if isinstance(value, dict) and not is_file_metadata:
            # Directory
            lines.append(f"{prefix}{connector}{name}/")
            extension = "    " if is_last_item else "│   "
            lines.extend(format_tree(value, prefix + extension, is_last_item))
        else:
            # File with token info
            token_count = value.get('tokens', 0)
            lines.append(f"{prefix}{connector}{name} ({token_count} tokens)")

    return lines

def main():
    parser = argparse.ArgumentParser(description='Scan codebase for token counts')
    parser.add_argument('directory', help='Directory to scan')
    parser.add_argument('--format', choices=['json', 'tree'], default='json',
                       help='Output format')
    parser.add_argument('--max-file-size', type=int, default=1024*1024,
                       help='Maximum file size to process (bytes)')

    args = parser.parse_args()

    root_path = Path(args.directory).resolve()
    if not root_path.exists():
        print(f"Error: Directory {root_path} does not exist", file=sys.stderr)
        sys.exit(1)

    if not root_path.is_dir():
        print(f"Error: {root_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    file_tree, total_files, total_tokens = scan_directory(root_path, args.max_file_size)

    if args.format == 'json':
        output = {
            'root_directory': str(root_path),
            'total_files': total_files,
            'total_tokens': total_tokens,
            'file_tree': file_tree
        }
        print(json.dumps(output, indent=2))
    else:
        # Tree format
        print(f"Codebase: {root_path}")
        print(f"Total files: {total_files}")
        print(f"Total tokens: {total_tokens}")
        print()
        tree_lines = format_tree(file_tree)
        for line in tree_lines:
            print(line)

if __name__ == '__main__':
    main()
