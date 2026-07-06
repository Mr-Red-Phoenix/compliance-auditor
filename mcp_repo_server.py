import os
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP Server
mcp = FastMCP("RepositoryComplianceAuditor")

# Security Guardrail: Hardcoded path restriction to target_repo relative to script directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_DIR = os.path.join(BASE_DIR, 'target_repo')
TARGET_REPO_DIR = Path(TARGET_DIR).resolve()

# Ensure the target directory exists for testing/operation
TARGET_REPO_DIR.mkdir(parents=True, exist_ok=True)

def _validate_path(path_str: str) -> Path:
    """
    Validates that the target path is strictly within the designated target repository directory.
    Throws PermissionError if the path attempts to escape the directory.
    """
    # If relative, resolve relative to TARGET_REPO_DIR
    p = Path(path_str)
    # Normalize path parts to strip 'target_repo' or './target_repo' if present
    parts = p.parts
    if parts and (parts[0] == 'target_repo' or parts[0] == './target_repo'):
        p = Path(*parts[1:])
    elif parts and len(parts) > 1 and parts[0] == '.' and parts[1] == 'target_repo':
        p = Path(*parts[2:])

    if not p.is_absolute():
        target_path = (TARGET_REPO_DIR / p).resolve()
    else:
        target_path = p.resolve()

    # Check if target_path is within TARGET_REPO_DIR
    if target_path != TARGET_REPO_DIR and TARGET_REPO_DIR not in target_path.parents:
        raise PermissionError(
            f"Security Violation: Access denied. Path '{path_str}' is outside the authorized './target_repo' boundary ({TARGET_REPO_DIR})."
        )
    return target_path

@mcp.tool()
def list_repository_files() -> str:
    """
    Lists the repository files recursively under the designated target repository directory
    and returns a directory tree representation.
    """
    _validate_path(str(TARGET_REPO_DIR))
    
    lines = [f"{TARGET_REPO_DIR.name}/"]
    
    def _build_tree(directory: Path, prefix: str = ""):
        try:
            items = sorted(list(directory.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            lines.append(f"{prefix}└── [Permission Denied]")
            return

        for i, item in enumerate(items):
            # Proactively validate the item path as a defense-in-depth measure
            try:
                _validate_path(str(item))
            except PermissionError:
                continue

            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            
            if item.is_dir():
                lines.append(f"{prefix}{connector}{item.name}/")
                new_prefix = prefix + ("    " if is_last else "│   ")
                _build_tree(item, new_prefix)
            else:
                lines.append(f"{prefix}{connector}{item.name}")

    _build_tree(TARGET_REPO_DIR)
    return "\n".join(lines)

@mcp.tool()
def read_file_content(file_path: str) -> str:
    """
    Reads the content of a file located within the designated target repository directory.
    
    Args:
        file_path: Relative or absolute path to the file to be read. Must reside within TARGET_REPO_DIR.
    """
    # Enforce path validation and security guardrail
    target_file = _validate_path(file_path)
    
    if not target_file.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    return target_file.read_text(encoding="utf-8")

if __name__ == "__main__":
    # Standard stdio server execution
    mcp.run()
