import json
from pathlib import Path
from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI(title="HITL Approval Webhook Server")
STATUS_FILE = Path("approval_status.json")

class ApprovalRequest(BaseModel):
    tool_name: str
    arguments: dict

class DecisionUpdate(BaseModel):
    status: str
    reason: str = ""

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

def write_status(data: dict):
    STATUS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

@app.post("/request_approval")
async def request_approval(req: ApprovalRequest):
    data = {
        "status": "PENDING",
        "tool_name": req.tool_name,
        "arguments": req.arguments,
        "reason": ""
    }
    write_status(data)
    return {"status": "PENDING"}

@app.get("/check_decision")
async def check_decision():
    return read_status()

@app.post("/update_decision")
async def update_decision(update: DecisionUpdate):
    current = read_status()
    current["status"] = update.status
    current["reason"] = update.reason
    write_status(current)
    return {"status": update.status, "reason": update.reason}

@app.post("/reset_decision")
async def reset_decision():
    data = {
        "status": "NONE",
        "tool_name": "",
        "arguments": {},
        "reason": ""
    }
    write_status(data)
    return {"status": "NONE"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8502, log_level="info")
