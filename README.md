# 🛡️ Code Integration and Compliance Auditor

**Kaggle AI Agents: Intensive Vibe Coding Capstone Project**

An enterprise-grade, Human-in-the-Loop (HITL) compliance auditor built with the **Google Agent Development Kit (ADK)** and **Streamlit**. This project ensures that AI agents cannot execute sensitive repository operations without explicit human authorization.

## ⚠️ The Problem
As autonomous AI agents become more integrated into codebases, they introduce significant security and compliance risks. Allowing an agent to read, parse, or execute code without oversight can lead to accidental data exposure, unauthorized sandbox escapes, or non-compliant code modifications.

## 💡 The Solution
This project introduces a strict **Human-in-the-Loop Authorization Gate**. By decoupling the agent's execution layer from a standalone approval dashboard, the system intercepts critical tool calls (like `list_repository_files`). 

Instead of executing immediately, the agent pauses and sends a webhook to a custom **Streamlit Dashboard**. A human operator can review the exact tool arguments, approve the action, or deny it with a custom rejection reason that is fed directly back into the agent's context.

## 🏗️ Architecture

The system is separated into three distinct threads to prevent event loop collisions and ensure highly responsive state management:

1. **The Core Agent Platform (Google ADK):** Runs the Gemini model and the Model Context Protocol (MCP) server. It intercepts tool calls and forwards them to the API server.
2. **The Webhook Server (`server.py`):** A lightweight FastAPI Uvicorn server running on port `8502` that manages the state of pending tool requests.
3. **The SOC Dashboard (`gui.py`):** A Streamlit frontend running on port `8501` that provides a clean UI for operators to monitor, approve, or deny pending requests with specific compliance rationales.

*(Insert your architecture diagram here: `![Architecture Diagram](assets/architecture.png)`)*

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/compliance-auditor.git](https://github.com/Mr-Red-Phoenix/compliance-auditor.git)
cd compliance-auditor
