import json
import time
from pathlib import Path
import streamlit as st
import requests

# Streamlit Page Config
st.set_page_config(
    page_title="Compliance HITL Dashboard",
    page_icon="🛡️",
    layout="centered"
)

# Custom Sleek Styling for Premium Dark Mode Dashboard
st.markdown("""
    <style>
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    }
    h1 {
        color: #58a6ff !important;
        font-weight: 700;
        text-align: center;
        margin-bottom: 5px !important;
    }
    .subtitle {
        color: #8b949e;
        text-align: center;
        margin-bottom: 30px;
        font-size: 1.1rem;
    }
    .status-card {
        border-radius: 12px;
        padding: 24px;
        background-color: #161b22;
        border: 1px solid #30363d;
        text-align: center;
        margin-bottom: 20px;
    }
    .tool-details {
        background-color: #0d1117;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 16px;
        font-family: monospace;
        text-align: left;
        margin-top: 15px;
        color: #e6edf3;
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        flex: 1;
        margin: 0 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>🛡️ Compliance Security Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Interactive Human-in-the-Loop (HITL) Web Clearance Center</p>", unsafe_allow_html=True)

STATUS_FILE = Path("approval_status.json")

def read_status() -> dict:
    if not STATUS_FILE.exists():
        return {"status": "NONE", "tool_name": "", "arguments": {}, "reason": ""}
    try:
        data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        if "reason" not in data:
            data["reason"] = ""
        return data
    except Exception:
        return {"status": "NONE", "tool_name": "", "arguments": {}, "reason": ""}

def update_status(status: str, reason: str = ""):
    try:
        requests.post("http://127.0.0.1:8502/update_decision", json={"status": status, "reason": reason})
    except Exception:
        # Fallback to direct file write if server is temporarily unreachable
        if STATUS_FILE.exists():
            try:
                current = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
                current["status"] = status
                current["reason"] = reason
                STATUS_FILE.write_text(json.dumps(current, indent=2), encoding="utf-8")
            except Exception:
                pass

# Initialize session state for denial flow
if "denial_pending" not in st.session_state:
    st.session_state.denial_pending = False

state = read_status()
status = state.get("status", "NONE")

# Overall visual metric headers
st.markdown("""
<div class="metric-container">
    <div class="metric-box">
        <span style="color: #8b949e; font-size: 0.9rem;">System Status</span><br>
        <strong style="color: #56d364; font-size: 1.2rem;">ONLINE</strong>
    </div>
    <div class="metric-box">
        <span style="color: #8b949e; font-size: 0.9rem;">Clearance Gate</span><br>
        <strong style="color: #58a6ff; font-size: 1.2rem;">ACTIVE</strong>
    </div>
</div>
""", unsafe_allow_html=True)

if status == "PENDING":
    tool_name = state.get("tool_name", "Unknown")
    arguments = state.get("arguments", {})
    
    st.warning("⚠️ SECURITY ACTION REQUIRED: Tool execution requires authorization.")
    
    st.markdown(f"""
    <div class="status-card">
        <h3 style="color: #ff7b72; margin-top: 0; font-size: 1.3rem;">Access Request Pending</h3>
        <p style="color: #8b949e; font-size: 0.95rem; margin-bottom: 10px;">The compliance agent requests authorization for the following tool:</p>
        <div class="tool-details">
            <span style="color: #58a6ff; font-weight: bold;">[Action]</span> {tool_name}<br><br>
            <span style="color: #79c0ff; font-weight: bold;">[Arguments]</span><br>
            {json.dumps(arguments, indent=2)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render Action Buttons
    if not st.session_state.denial_pending:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 Approve Execution", use_container_width=True):
                update_status("APPROVED")
                st.success("Execution approved. Releasing agent...")
                time.sleep(1.0)
                st.rerun()
        with col2:
            if st.button("🔴 Deny Execution", use_container_width=True):
                st.session_state.denial_pending = True
                st.rerun()
    else:
        # Prompt for rejection reason
        st.error("Access Denial Flow")
        rejection_reason = st.text_input("Provide Rejection Reason:", value="Access denied due to security policy violations.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Deny", use_container_width=True):
                update_status("DENIED", rejection_reason)
                st.session_state.denial_pending = False
                st.success("Denial successfully submitted.")
                time.sleep(1.0)
                st.rerun()
        with col2:
            if st.button("Cancel", use_container_width=True):
                st.session_state.denial_pending = False
                st.rerun()
else:
    # No pending request, reset denial state
    st.session_state.denial_pending = False
    
    st.markdown(f"""
    <div class="status-card" style="border-color: #2ea44f;">
        <h3 style="color: #56d364; margin-top: 0; font-size: 1.3rem;">🟢 Security Status: CLEAR</h3>
        <p style="color: #8b949e; font-size: 1rem; margin-bottom: 0;">
            No pending tool execution requests. Standing by for compliance sweeps...
        </p>
    </div>
    """, unsafe_allow_html=True)

# Polling loop: automatically refresh Streamlit dashboard to check for new requests
time.sleep(1.0)
st.rerun()
