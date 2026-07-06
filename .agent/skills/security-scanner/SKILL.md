---
name: security-scanner
description: Scanner skill designed to catch hardcoded secrets, SQL injections, and unsafe React/Next.js prop usage like dangerouslySetInnerHTML.
triggers:
  positive:
    - "Scan repository for credentials, private keys, or token leaks"
    - "Analyze React or Next.js components for unsafe HTML rendering"
    - "Audit FastAPI database queries for potential SQL injections"
  negative:
    - "Generate CSS stylesheets or visual UI layouts"
    - "Update unit tests or package dependencies"
    - "Format text documentation, readme files, or markdown guides"
---

# Security Scanner Skill

This skill allows the agent to audit code for critical security vulnerabilities, including exposed credentials, SQL injection patterns, and unsafe client-side rendering props.

## Purpose
- Identify hardcoded secrets, API tokens, JWT secrets, and database connection strings.
- Detect SQL injection patterns in database query builders and raw SQL executions.
- Flag unsafe React/Next.js properties such as `dangerouslySetInnerHTML`.

## Execution Workflow
1. **Filter Files**: Invoke the helper script `filter_files.py` to identify relevant files for analysis (`.py`, `.tsx`, `.ts`, `.js`, `.jsx`).
2. **Scan Code**: Perform regex matching and AST-based scans.
3. **Generate Vibe Diff**: Produce a human-readable "Vibe Diff" summary of findings.

## Output Format: Vibe Diff
The agent MUST output a structured 'Vibe Diff' using the following format:

```markdown
# Vibe Diff: Security Risks Found

## [Risk Category: e.g., Secret Exposure]
- **File**: `path/to/file`
- **Severity**: [CRITICAL | HIGH | MEDIUM | LOW]
- **Risk Description**: Plain-English explanation of the security risk and potential impact.
- **Recommended Remediation**: How to fix the issue securely.

---
```
