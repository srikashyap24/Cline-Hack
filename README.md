# Cline-Hack: Slack AI Simplifier Assistant

A robust, Python-based AI assistant designed to simplify technical jargon and communication for various audiences. This project leverages the **Model Context Protocol (MCP)** and **LangGraph** to provide a modular, high-performance reasoning engine that integrates seamlessly with Slack.

## 🚀 Overview

Cline-Hack automates the process of translating complex technical text into audience-appropriate content. Whether you're communicating with Management, Engineering, or General stakeholders, this assistant ensures your message is clear, concise, and technically accurate.

### Key Features
- **LangGraph Reasoning:** Advanced autonomous reasoning loop for processing and refining text.
- **MCP Architecture:** Decoupled tools and brain using SSE (Server-Sent Events) transport.
- **Audience-Aware Simplification:** Tailors tone and detail based on the target persona.
- **Accuracy Validation:** Cross-checks simplified text against the original source to ensure no loss of meaning.
- **Slack Integration:** Real-time processing via Slack Slash commands and interactions.

---

## 🏗️ Architecture

The project is split into two primary components:

1.  **Python MCP Server (`python-mcp-server`)**:
    - Exposes core simplification and validation tools.
    - Operates as a standalone service via SSE.
    - Handles external API calls (e.g., OpenRouter/Gemini).

2.  **Python AI Agent (`python-ai-agent`)**:
    - The "Brain" of the operation using LangGraph.
    - Connects to the MCP server to execute tools.
    - Manages Slack interactions and request lifecycle.

---

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.10+
- A Slack App with Slash Commands enabled.
- OpenRouter API Key.

### 1. Configure the MCP Server

```bash
cd python-mcp-server

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY
```

### 2. Configure the AI Agent

```bash
cd python-ai-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env and add your SLACK_SIGNING_SECRET and OPENROUTER_API_KEY
```

---

## 🏃 Running the Application

You need to run both services simultaneously.

### Start MCP Server
```bash
cd python-mcp-server
source venv/bin/activate
python server.py
```
*Default port: `4000`*

### Start AI Agent
```bash
cd python-ai-agent
source venv/bin/activate
python agent.py
```
*Default port: `3000`*

---

## 💬 Slack Configuration

1.  **Slash Command:** Create `/simplify`.
2.  **Request URL:** Point to your agent's endpoint (e.g., `https://<your-ngrok-url>/slack/simplify`).
3.  **Verification:** Ensure `SLACK_SIGNING_SECRET` in `python-ai-agent/.env` matches your Slack App's secret.

---

## 📄 License

MIT
