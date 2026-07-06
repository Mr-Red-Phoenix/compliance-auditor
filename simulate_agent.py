import sys
import time
import requests

def run_simulation():
    server_url = "http://127.0.0.1:8502"
    
    print("\n--- 🛡️ HITL Gateway Simulation ---")
    print("This script simulates an agent requesting permission to execute a tool.")
    print("Checking if the server is running on port 8502...")
    
    try:
        # Check if the server is up
        res = requests.get(f"{server_url}/check_decision")
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: The server is not running!")
        print("Please start it first in another terminal: python server.py")
        sys.exit(1)
        
    tool_name = "read_file_content"
    tool_args = {"path": "target_repo/main.py", "reason": "scanning for credentials"}
    
    print(f"\n1. Simulating tool request: '{tool_name}' with args: {tool_args}")
    try:
        res = requests.post(
            f"{server_url}/request_approval",
            json={"tool_name": tool_name, "arguments": tool_args}
        )
        if res.status_code == 200:
            print("🟢 Tool call successfully registered with server.")
        else:
            print(f"❌ Failed to register tool call: {res.text}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error sending request: {e}")
        sys.exit(1)
        
    print("\n2. Polling for operator decision...")
    print("👉 Go to your Streamlit dashboard (http://localhost:8501)")
    print("👉 You will see the pending card. Click 'Approve' or 'Deny Execution' (with a reason).")
    print("\nWaiting for decision...")
    
    try:
        while True:
            time.sleep(1)
            check_res = requests.get(f"{server_url}/check_decision")
            if check_res.status_code == 200:
                state = check_res.json()
                status = state.get("status")
                
                if status == "APPROVED":
                    print("\n🟢 [DECISION] Tool execution APPROVED by operator!")
                    print("Action: Resetting server state.")
                    requests.post(f"{server_url}/reset_decision")
                    break
                elif status == "DENIED":
                    reason = state.get("reason", "No reason provided")
                    print("\n🔴 [DECISION] Tool execution DENIED by operator!")
                    print(f"Reason for rejection: '{reason}'")
                    print("Action: Resetting server state.")
                    requests.post(f"{server_url}/reset_decision")
                    break
    except KeyboardInterrupt:
        print("\nSimulation aborted.")
        requests.post(f"{server_url}/reset_decision")

if __name__ == "__main__":
    run_simulation()
