# MCP Productivity Server

A Model Context Protocol (MCP) server built for the Personal Productivity domain. It lets an MCP client (like Claude Desktop) manage a simple task list and email a summary of it, using a locally stored JSON file and an SMTP connection.

## What it does

**Tools:**
- `add_task(description, priority, due_date)` — adds a task to a local task list (`tasks.json`), with input validation (length limits, control-character rejection, priority restricted to low/medium/high).
- `email_task_summary(recipient_email)` — emails a formatted summary of all current tasks via SMTP.

**Prompt:**
- `daily_plan` — reads the current task list, sorts it by priority, and returns a prompt asking the connected LLM to turn it into a short daily plan.

## Security best practices implemented

1. **Input sanitization** — `add_task` rejects empty descriptions, descriptions over 200 characters, and descriptions containing control characters (which could otherwise corrupt the JSON store or manipulate downstream text). See `tests/exploit_input_sanitization.py` for the exploit test proving this.
2. **Safe error disclosure** — `email_task_summary` catches both `smtplib.SMTPException` and `OSError` (covering DNS/connection failures) and always returns a generic error message, never a raw exception or traceback that could leak SMTP credentials or internal hostnames. See `tests/exploit_error_disclosure.py` for the exploit test proving this.

## Setup

1. Install [`uv`](https://docs.astral.sh/uv/) if you don't have it.
2. Clone this repository and `cd` into it.
3. Install dependencies:
uv sync
4. Copy `.env.example` to `.env` and fill in real SMTP credentials (an [Ethereal](https://ethereal.email/create) test account works well for development — no real email is sent, just a preview link).

cp .env.example .env

5. Verify the server starts and imports cleanly:

uv run python -c "import src.mcp_productivity_server.server"


## Running the exploit tests
uv run python tests/exploit_input_sanitization.py
uv run python tests/exploit_error_disclosure.py


## Connecting to Claude Desktop

Add the following to your `claude_desktop_config.json` (on macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`), inside the `mcpServers` object:

```json
"productivity-server": {
  "command": "uv",
  "args": [
    "run",
    "--directory",
    "/absolute/path/to/mcp-productivity-server",
    "python",
    "src/mcp_productivity_server/server.py"
  ]
}
```
Replace the path with this project's actual absolute path on your machine, then fully quit and reopen Claude Desktop.

## Project structure

mcp-productivity-server/
├── src/mcp_productivity_server/
│ └── server.py # MCP server: tools, prompt, task storage
├── tests/
│ ├── exploit_input_sanitization.py
│ └── exploit_error_disclosure.py
├── .env.example # Template for required environment variables
├── pyproject.toml
└── README.md