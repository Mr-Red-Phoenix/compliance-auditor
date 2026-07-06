---
name: pii-auditor
description: Scanner skill designed to flag unmasked emails, phone numbers, and PII leaks in API responses or frontend renderings.
triggers:
  positive:
    - "Check for unmasked emails or telephone numbers in code"
    - "Audit Next.js frontend code for potential user data leaks"
    - "Analyze API JSON responses for unmasked customer records"
  negative:
    - "Analyze test database connection setup configurations"
    - "Debug backend server timeouts or route latency"
    - "Audit repository license compatibility or dependencies"
---

# PII Auditor Skill

This skill allows the agent to scan frontends (Next.js components) and API routes for unmasked Personally Identifiable Information (PII) leakage.

## Purpose
- Identify unmasked emails, phone numbers, and national identification numbers.
- Detect API endpoints that return broad user objects containing sensitive raw fields.
- Flag unmasked rendering of user profiles or context items.

## Execution Workflow
1. **Filter Files**: Invoke the helper script `filter_files.py` to identify relevant files for analysis (`.py`, `.tsx`, `.ts`, `.js`, `.jsx`).
2. **Scan Code**: Search for common PII patterns and raw user property renderings.
3. **Generate Vibe Diff**: Produce a human-readable "Vibe Diff" summary of findings.

## Output Format: Vibe Diff
The agent MUST output a structured 'Vibe Diff' using the following format:

```markdown
# Vibe Diff: PII Leaks Found

## [Risk Category: e.g., Unmasked Contact Info]
- **File**: `path/to/file`
- **Severity**: [CRITICAL | HIGH | MEDIUM | LOW]
- **Risk Description**: Plain-English explanation of the PII exposure risk and potential impact.
- **Recommended Remediation**: How to fix the issue securely (e.g., masking utilities, field exclusions).

---
```
