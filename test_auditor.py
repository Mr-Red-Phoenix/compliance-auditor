import os
import pytest
from pathlib import Path
from mcp_repo_server import _validate_path, read_file_content
from app.agent import load_skills, get_filtered_files

def test_mcp_path_restriction_guardrail():
    """
    Verifies that the MCP server enforces strict path restrictions
    and raises PermissionError for any access outside target_repo.
    """
    # Valid targets
    valid_file = Path("./target_repo/main.py").resolve()
    assert _validate_path(str(valid_file)) == valid_file

    # Invalid targets (escaping target_repo)
    invalid_file = Path("./mcp_repo_server.py").resolve()
    with pytest.raises(PermissionError) as exc_info:
        _validate_path(str(invalid_file))
    
    assert "Security Violation" in str(exc_info.value)
    assert "outside the authorized './target_repo' boundary" in str(exc_info.value)

    # Testing read_file_content tool directly for invalid files
    with pytest.raises(PermissionError):
        read_file_content(str(invalid_file))

def test_skills_loader():
    """
    Verifies that the dynamic skills loader successfully scans .agent/skills/
    and imports instructions without syntax errors.
    """
    skills_data = load_skills()
    assert "security-scanner" in skills_data
    assert "pii-auditor" in skills_data
    assert "dangerouslySetInnerHTML" in skills_data or "secret" in skills_data

def test_file_filtering():
    """
    Verifies that the helper file filtering script correctly identifies target repo files.
    """
    filtered = get_filtered_files()
    assert any("main.py" in f for f in filtered)
    assert any("page.tsx" in f for f in filtered)
    
    # Verify non-matching formats are omitted (if any exist)
    assert not any(f.endswith(".md") for f in filtered)
