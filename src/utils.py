"""
Utility functions for the Viral Video Clipper.
Includes progress bar and logging helpers.
"""

from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.panel import Panel
from rich.table import Table
from contextlib import contextmanager
import subprocess
import sys


console = Console()


def get_ffmpeg_path() -> str:
    """Get path to ffmpeg binary (local bin/ffmpeg or system default)."""
    # Check for local bin/ffmpeg relative to project root
    import os
    base_dir = __file__.split("src")[0]
    local_ffmpeg = f"{base_dir}bin/ffmpeg"
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    return "ffmpeg"


def print_header(title: str):
    """Print a styled header."""
    console.print(Panel(f"[bold cyan]{title}[/bold cyan]", expand=False))


def print_step(step: str, description: str):
    """Print a step with description."""
    console.print(f"[bold green]▶[/bold green] [bold]{step}[/bold]: {description}")


def print_success(message: str):
    """Print a success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str):
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_info(message: str):
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


@contextmanager
def progress_context(description: str):
    """Context manager for showing a progress spinner."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        yield progress


def create_progress():
    """Create a progress bar instance."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    )


def run_ffmpeg(args: list, description: str = "Processing", progress=None, task_id=None):
    """
    Run ffmpeg with progress tracking.
    Parses ffmpeg output to update progress bar.
    """
    cmd = ["ffmpeg", "-y", "-progress", "pipe:1", "-nostats"] + args
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    
    duration = None
    current_time = 0
    
    for line in process.stdout:
        line = line.strip()
        if line.startswith("out_time_ms="):
            try:
                time_ms = int(line.split("=")[1])
                current_time = time_ms / 1_000_000  # Convert to seconds
                if progress and task_id and duration:
                    pct = min(100, (current_time / duration) * 100)
                    progress.update(task_id, completed=pct)
            except ValueError:
                pass
    
    process.wait()
    
    if process.returncode != 0:
        stderr = process.stderr.read()
        raise RuntimeError(f"ffmpeg failed: {stderr}")
    
    return True


def format_time(seconds: float) -> str:
    """Format seconds to HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_time(time_str: str) -> float:
    """Parse HH:MM:SS or MM:SS to seconds."""
    parts = time_str.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    elif len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    else:
        return float(parts[0])


def print_clips_summary(clips: list):
    """Print a summary table of detected clips."""
    table = Table(title="Detected Viral Segments")
    table.add_column("Clip", style="cyan")
    table.add_column("Start", style="green")
    table.add_column("End", style="green")
    table.add_column("Duration", style="yellow")
    table.add_column("Score", style="magenta")
    
    for i, clip in enumerate(clips, 1):
        start = format_time(clip["start"])
        end = format_time(clip["end"])
        duration = format_time(clip["end"] - clip["start"])
        score = f"{clip.get('score', 0):.1f}"
        table.add_row(f"Clip {i}", start, end, duration, score)
    
    console.print(table)
