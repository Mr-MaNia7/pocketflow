import logging
from datetime import datetime
from typing import Any, Dict
import json
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table
import os

# Initialize Rich console
console = Console()


def setup_logger():
    """Set up the logger with rich formatting."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    return logging.getLogger("research_system")


logger = setup_logger()


class ResearchLogger:
    """A logger class for tracking research system steps."""

    def __init__(self):
        self.start_time = datetime.now()
        self.steps = []

    def log_step(
        self, node_name: str, action: str, message: str, data: Dict[str, Any] = None
    ):
        """Log a step in the research process."""
        step = {
            "timestamp": datetime.now().isoformat(),
            "node": node_name,
            "action": action,
            "message": message,
            "data": data or {},
        }
        self.steps.append(step)

        # Create a rich table for the step
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Node", node_name)
        table.add_row("Action", action)
        table.add_row("Message", message)
        if data:
            table.add_row("Data", json.dumps(data, indent=2))

        # Print the step in a panel
        console.print(
            Panel(table, title=f"Step {len(self.steps)}", border_style="blue")
        )

    def log_error(self, node_name: str, error: Exception, message: str):
        """Log an error in the research process."""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "message": message,
        }
        self.log_step(node_name, "ERROR", message, error_data)

    def log_completion(self, summary: Dict[str, Any]):
        """Log the completion of the research process."""
        duration = datetime.now() - self.start_time
        summary.update(
            {
                "total_steps": len(self.steps),
                "duration_seconds": duration.total_seconds(),
                "successful_steps": len(
                    [s for s in self.steps if s["action"] != "ERROR"]
                ),
            }
        )

        # Create a summary table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        for key, value in summary.items():
            table.add_row(key.replace("_", " ").title(), str(value))

        # Print the summary in a panel
        console.print(
            Panel(table, title="Research Process Summary", border_style="green")
        )

        # Save the log to a file
        os.makedirs("logs", exist_ok=True)
        log_file = os.path.join(
            "logs", f"research_log_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(log_file, "w") as f:
            json.dump(
                {
                    "start_time": self.start_time.isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "steps": self.steps,
                    "summary": summary,
                },
                f,
                indent=2,
            )

        console.print(f"\n[bold green]Log saved to {log_file}[/bold green]")


# Create a global logger instance
research_logger = ResearchLogger()
