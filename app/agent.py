import os
from dotenv import load_dotenv
# Execute load_dotenv at the very top of the script
load_dotenv()

import json
import sys
import asyncio
import subprocess
from pathlib import Path
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from mcp import StdioServerParameters
from google.adk.tools.mcp_tool.mcp_toolset import StdioConnectionParams, McpToolset
from typing import Any

def find_agent_skills_dir() -> Path:
    """
    Finds the .agent/skills directory by checking the current working directory
    and parent directories.
    """
    current = Path.cwd().resolve()
    for directory in [current] + list(current.parents):
        skills_dir = directory / ".agent" / "skills"
        if skills_dir.exists():
            return skills_dir
    return Path(".agent/skills")

def load_skills() -> str:
    """
    Dynamically loads the instructions from SKILL.md files under the .agent/skills/ directory.
    """
    skills_dir = find_agent_skills_dir()
    skills_instructions = []
    
    if not skills_dir.exists():
        print(f"Warning: Skills directory {skills_dir.resolve()} does not exist.", file=sys.stderr)
        return ""
        
    for skill_md in skills_dir.glob("**/SKILL.md"):
        try:
            content = skill_md.read_text(encoding="utf-8")
            # Remove YAML frontmatter if present
            parts = content.split("---")
            if len(parts) >= 3:
                instruction_text = "\n".join(parts[2:]).strip()
            else:
                instruction_text = content.strip()
            skills_instructions.append(f"### Skill: {skill_md.parent.name}\n{instruction_text}")
        except Exception as e:
            print(f"Error reading skill {skill_md}: {e}", file=sys.stderr)
            
    return "\n\n".join(skills_instructions)

def get_filtered_files() -> list[str]:
    """
    Executes the helper script filter_files.py from the security-scanner skill
    to retrieve the list of files to be scanned within ./target_repo.
    """
    skills_dir = find_agent_skills_dir()
    script_path = skills_dir / "security-scanner" / "scripts" / "filter_files.py"
    if not script_path.exists():
        print(f"Warning: Helper script {script_path} not found. Defaulting to empty list.", file=sys.stderr)
        return []
        
    try:
        # Run the script using Python subprocess
        result = subprocess.run(
            [sys.executable, str(script_path), "./target_repo", ".py", ".tsx", ".ts", ".js", ".jsx"],
            capture_output=True,
            text=True,
            check=True
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception as e:
        print(f"Error filtering files via helper script: {e}", file=sys.stderr)
        return []

# 1. Dynamically load local skills
skills_instruction = load_skills()

# Base system prompt
base_instruction = (
    "You are the Lead Security Architect and Code Compliance Auditor Agent.\n"
    "Your task is to analyze the code content of the files passed to you.\n"
    "Analyze each file carefully according to the loaded security policies and instructions.\n"
    "If you find any security violations or compliance issues, output a highly detailed 'Vibe Diff' block.\n"
    "You MUST explicitly point out exactly what information is being leaked (e.g., exact passwords, URIs, or emails) and explain why it is a security risk.\n"
    "If a file has no security issues and is fully compliant, reply strictly with the word 'CLEAN'.\n\n"
    "Ensure you adhere strictly to the compliance guidelines below:\n\n"
)

full_instruction = base_instruction + skills_instruction

# 2. Configure MCP Client Subprocess Connection to mcp_repo_server.py
mcp_server_script = Path("mcp_repo_server.py").resolve()

server_params = StdioServerParameters(
    command=sys.executable,
    args=[str(mcp_server_script)],
    cwd=os.getcwd()
)

connection_params = StdioConnectionParams(
    server_params=server_params,
    timeout=15.0
)

mcp_toolset = McpToolset(connection_params=connection_params)

async def before_tool_approval(*args_list, **kwargs):
    # Extract parameters safely supporting varying keyword/positional parameters from ADK
    tool = kwargs.get("tool") or (args_list[0] if len(args_list) > 0 else None)
    tool_args = kwargs.get("args") or kwargs.get("arguments") or (args_list[1] if len(args_list) > 1 else {})
    
    # Resolve tool name
    tool_name = getattr(tool, "name", str(tool))

    print(f"\n[HITL] Sending approval request for tool '{tool_name}' to dashboard...")
    try:
        import requests
        # Register the pending request
        res = requests.post(
            "http://127.0.0.1:8502/request_approval",
            json={"tool_name": tool_name, "arguments": tool_args}
        )
        if res.status_code != 200:
            raise RuntimeError(f"Failed to register HITL approval: {res.status_code}")
            
        # Poll the server until status is no longer PENDING
        while True:
            await asyncio.sleep(0.5)
            check_res = requests.get("http://127.0.0.1:8502/check_decision")
            if check_res.status_code == 200:
                state = check_res.json()
                status = state.get("status")
                if status == "APPROVED":
                    print(f"[HITL] Tool '{tool_name}' APPROVED by operator.")
                    requests.post("http://127.0.0.1:8502/reset_decision")
                    return tool_args
                elif status == "DENIED":
                    reason = state.get("reason", "No reason provided")
                    print(f"[HITL] Tool '{tool_name}' DENIED by operator. Reason: {reason}")
                    requests.post("http://127.0.0.1:8502/reset_decision")
                    raise PermissionError(f"[SECURITY ACTION] Tool execution denied by operator. Reason: {reason}")
    except Exception as e:
        if isinstance(e, PermissionError):
            raise e
        print(f"[HITL Error] Failed to communicate with HITL server: {e}", file=sys.stderr)
        raise PermissionError(f"Access Denied: HITL communication failure: {e}")

from google.adk.tools.base_toolset import BaseToolset
from google.adk.tools.base_tool import BaseTool
import copy

class AuthorizedTool(BaseTool):
    """
    A custom wrapper around BaseTool that intercepts the execution path
    and redirects it through the Human-in-the-Loop (HITL) approval gate.
    """
    def __init__(self, underlying_tool: BaseTool):
        super().__init__(
            name=underlying_tool.name,
            description=underlying_tool.description,
            is_long_running=underlying_tool.is_long_running,
            custom_metadata=underlying_tool.custom_metadata
        )
        self.underlying_tool = underlying_tool

    def _get_declaration(self):
        return self.underlying_tool._get_declaration()

    async def run_async(self, *, args: dict[str, Any], tool_context) -> Any:
        # Pass execution parameters through the verification checkpoint
        await before_tool_approval(self.underlying_tool, args, tool_context)
        return await self.underlying_tool.run_async(args=args, tool_context=tool_context)

class HITLAuthorizationGateToolset(BaseToolset):
    """
    An intermediate Toolset that intercepts tool discovery, wrapping
    all underlying McpToolset tools inside the AuthorizedTool gate.
    """
    def __init__(self, mcp_toolset: McpToolset):
        super().__init__()
        self.mcp_toolset = mcp_toolset

    async def get_tools(self, readonly_context=None) -> list[BaseTool]:
        underlying_tools = await self.mcp_toolset.get_tools(readonly_context)
        return [AuthorizedTool(tool) for tool in underlying_tools]

    async def close(self) -> None:
        await self.mcp_toolset.close()

# Instantiate the custom gate toolset wrapping the MCP toolset
gate_toolset = HITLAuthorizationGateToolset(mcp_toolset)

# 3. Instantiate Google ADK LlmAgent globally (Exposed for ADK Web Server)
agent = LlmAgent(
    name="ComplianceAuditorAgent",
    description="Audits FastAPI and Next.js repositories for compliance. Integrates an intermediate HITLAuthorizationGateToolset that routes all McpToolset actions through a security clearance gate.",
    model="gemini-2.5-flash",
    instruction=full_instruction,
    tools=[gate_toolset]
)

async def main():
    print("Initializing Code Integration & Compliance Auditor Agent...")
    
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, session_service=session_service)
    
    # Get the files to scan
    files_to_scan = get_filtered_files()
    if not files_to_scan:
        print("No repository files found/matched for auditing under ./target_repo.")
        return
        
    print(f"Found {len(files_to_scan)} files to audit.")
    vibe_diffs = []
    
    # 4. File-by-file processing to prevent context exhaustion
    for idx, file_path in enumerate(files_to_scan, 1):
        print(f"[{idx}/{len(files_to_scan)}] Auditing file: {file_path} ...")
        
        prompt = f"Audit the file '{file_path}'. First, use read_file_content to retrieve its contents. Then analyze it and provide your Vibe Diff or CLEAN."
        
        try:
            response_text = ""
            events = runner.run(
                user_id="operator",
                session_id=f"audit_session_{file_path.replace('/', '_').replace('.', '_')}",
                new_message=prompt
            )
            for event in events:
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            response_text += part.text
            
            response_text = response_text.strip()
            if "CLEAN" not in response_text:
                vibe_diffs.append((file_path, response_text))
        except Exception as e:
            print(f"Error scanning file {file_path}: {e}", file=sys.stderr)
            vibe_diffs.append((file_path, f"Error: Failed to scan file due to an exception: {e}"))
            
    # Close the runner and MCP toolset connections
    runner.close()
    
    # Compile the final report summary
    print("\n" + "="*50)
    print("AUDIT RESULTS SUMMARY")
    print("="*50)
    
    if not vibe_diffs:
        vibe_diff_summary = "All scanned files are CLEAN. No vulnerabilities or compliance leaks detected."
    else:
        vibe_diff_summary = "\n\n".join([f"### Violations in {fp}:\n{diff}" for fp, diff in vibe_diffs])
        
    print(vibe_diff_summary)
    print("="*50)
    
    # 5. Security Requirement (Pillar 5): Human-in-the-Loop (HITL) checkpoint
    # Wrap in a conditional check to bypass terminal blocking when in ADK web server
    if os.environ.get("RUN_ENV") == "cli":
        print("\n[HITL Checkpoint] Verification Required.")
        print("Do you approve the audit results shown above? (Y/N): ", end="", flush=True)
        
        # Read user input from keyboard
        user_choice = sys.stdin.readline().strip().upper()
        
        if user_choice == "Y":
            print("\nDecision: APPROVED")
            if vibe_diffs:
                print("Status: FAILED (Violations detected but report approved for logging)")
            else:
                print("Status: PASSED (Clean audit)")
        else:
            print("\nDecision: REJECTED")
            print("Status: HALTED (Operator did not approve the audit results)")
    else:
        print("\nDecision: AUTO-PROCESSED (HITL skipped in web environment)")
        if vibe_diffs:
            print("Status: FAILED (Violations detected)")
        else:
            print("Status: PASSED (Clean audit)")
root_agent = agent
if __name__ == "__main__":
    asyncio.run(main())
