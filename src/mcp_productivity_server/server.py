from pathlib import Path
import json
import os
import re
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer

# Server structure (MCPServer setup, @mcp.tool()/@mcp.prompt() decorators) follows
# the pattern from the official MCP Python SDK documentation:
# https://github.com/modelcontextprotocol/python-sdk

load_dotenv()

mcp = MCPServer("productivity-server")

TASKS_FILE = Path(__file__).parent / "tasks.json"

CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_DESCRIPTION_LENGTH = 200


def _load_tasks() -> list[dict]:
    if not TASKS_FILE.exists():
        return []
    return json.loads(TASKS_FILE.read_text())


def _save_tasks(tasks: list[dict]) -> None:
    TASKS_FILE.write_text(json.dumps(tasks, indent=2))


@mcp.tool()
def add_task(description: str, priority: str = "medium", due_date: str = "") -> dict:
    """Add a new task to the tracker.

    Args:
        description: What the task is.
        priority: One of "low", "medium", "high".
        due_date: Optional date string like "2026-09-25".
    """
    description = description.strip()

    if not description:
        return {"success": False, "error": "Task description cannot be empty."}

    if len(description) > MAX_DESCRIPTION_LENGTH:
        return {"success": False, "error": f"Task description must be under {MAX_DESCRIPTION_LENGTH} characters."}

    if CONTROL_CHAR_PATTERN.search(description):
        return {"success": False, "error": "Task description contains invalid control characters."}

    if priority not in {"low", "medium", "high"}:
        return {"success": False, "error": "Priority must be low, medium, or high."}

    tasks = _load_tasks()
    tasks.append({
        "description": description,
        "priority": priority,
        "due_date": due_date,
        "completed": False,
    })
    _save_tasks(tasks)
    return {"success": True, "task_count": len(tasks)}


@mcp.tool()
def email_task_summary(recipient_email: str) -> dict:
    """Email a summary of all current tasks to the given address.

    Args:
        recipient_email: Where to send the task summary.
    """
    recipient_email = recipient_email.strip()
    if "@" not in recipient_email or "." not in recipient_email:
        return {"success": False, "error": "That doesn't look like a valid email address."}

    tasks = _load_tasks()
    if not tasks:
        body = "You have no tasks right now."
    else:
        lines = [
            f"- [{t['priority'].upper()}] {t['description']}"
            + (f" (due {t['due_date']})" if t["due_date"] else "")
            for t in tasks
        ]
        body = "Your current tasks:\n\n" + "\n".join(lines)

    msg = MIMEText(body)
    msg["Subject"] = "Your Task Summary"
    msg["From"] = os.environ["SMTP_USERNAME"]
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
            server.starttls()
            server.login(os.environ["SMTP_USERNAME"], os.environ["SMTP_PASSWORD"])
            server.send_message(msg)
    except (smtplib.SMTPException, OSError):
        return {"success": False, "error": "Failed to send email. Please try again later."}

    return {"success": True, "sent_to": recipient_email, "task_count": len(tasks)}


@mcp.prompt()
def daily_plan() -> str:
    """Generate a prompt that turns the current task list into a simple daily plan."""
    tasks = _load_tasks()
    if not tasks:
        return "I have no tasks right now. Let me know if I should add some."

    order = {"high": 0, "medium": 1, "low": 2}
    sorted_tasks = sorted(tasks, key=lambda t: order.get(t["priority"], 1))

    lines = [
        f"- [{t['priority'].upper()}] {t['description']}"
        + (f" (due {t['due_date']})" if t["due_date"] else "")
        for t in sorted_tasks
    ]

    return (
        "Here are my tasks, sorted by priority. "
        "Please turn this into a short, encouraging daily plan I can follow:\n\n"
        + "\n".join(lines)
    )


if __name__ == "__main__":
    mcp.run()