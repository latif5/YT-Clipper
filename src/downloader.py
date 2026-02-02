"""
Video and subtitle downloader using yt-dlp.
"""

import subprocess
import json
import re
import os
from pathlib import Path
from datetime import timedelta
from .utils import print_step, print_success, print_error, console


def get_video_info(url: str) -> dict:
    """Get video metadata from YouTube."""
    print_step("Fetching", "Video metadata...")
    
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--print-json",
        url,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to get video info: {result.stderr}")
    
    # Parse JSON from output (first line)
    lines = result.stdout.strip().split("\n")
    for line in lines:
        if line.startswith("{"):
            info = json.loads(line)
            print_success(f"Found: {info.get('title', 'Unknown')}")
            return info
    
    raise RuntimeError("No video info found")


def download_full_video(url: str, output_path: Path) -> Path:
    """Download full video once for processing all clips."""
    print_step("Downloading", "Full video (one-time)...")
    
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        "--quiet",
        "--no-warnings",
        url,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to download video: {result.stderr}")
    
    # Handle possible extension issues
    if not output_path.exists():
        for ext in [".mp4", ".webm", ".mkv"]:
            alt = output_path.with_suffix(ext)
            if alt.exists():
                return alt
    
    print_success(f"Video downloaded: {output_path.name}")
    return output_path


def download_subtitles(url: str, output_dir: Path) -> Path:
    """Download auto-generated subtitles in VTT format."""
    print_step("Downloading", "Subtitles...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "subs"
    
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-auto-subs",
        "--sub-lang", "id,en",
        "--sub-format", "vtt",
        "--convert-subs", "srt",
        "-o", str(output_path),
        url,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Find the downloaded subtitle file
    for ext in [".id.srt", ".en.srt", ".srt"]:
        srt_path = Path(str(output_path) + ext)
        if srt_path.exists():
            print_success(f"Subtitles saved: {srt_path.name}")
            return srt_path
    
    # Try VTT
    for ext in [".id.vtt", ".en.vtt", ".vtt"]:
        vtt_path = Path(str(output_path) + ext)
        if vtt_path.exists():
            # Convert VTT to SRT
            srt_path = vtt_path.with_suffix(".srt")
            convert_vtt_to_srt(vtt_path, srt_path)
            print_success(f"Subtitles converted: {srt_path.name}")
            return srt_path
    
    print_error("No subtitles found, proceeding without...")
    return None


def convert_vtt_to_srt(vtt_path: Path, srt_path: Path):
    """Convert VTT subtitle to SRT format."""
    with open(vtt_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Remove VTT header
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    
    # Remove VTT-specific tags
    content = re.sub(r"<[^>]+>", "", content)
    
    # Convert timestamps from VTT (00:00:00.000) to SRT (00:00:00,000)
    content = re.sub(r"(\d{2}:\d{2}:\d{2})\.(\d{3})", r"\1,\2", content)
    
    # Remove position/alignment info
    content = re.sub(r" align:.*$", "", content, flags=re.MULTILINE)
    content = re.sub(r" position:.*$", "", content, flags=re.MULTILINE)
    
    # Add sequence numbers
    blocks = content.strip().split("\n\n")
    srt_content = []
    
    for i, block in enumerate(blocks, 1):
        lines = block.strip().split("\n")
        if len(lines) >= 2 and "-->" in lines[0]:
            srt_content.append(f"{i}\n{block}")
    
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(srt_content))


def parse_srt(srt_path: Path) -> list:
    """Parse SRT file and return list of subtitle entries."""
    if not srt_path or not srt_path.exists():
        return []
    
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    entries = []
    blocks = content.strip().split("\n\n")
    
    time_pattern = re.compile(
        r"(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})"
    )
    
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        
        # Find timestamp line
        for i, line in enumerate(lines):
            match = time_pattern.search(line)
            if match:
                g = match.groups()
                start = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
                end = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
                text = " ".join(lines[i + 1:])
                
                entries.append({
                    "start": start,
                    "end": end,
                    "text": text.strip(),
                })
                break
    
    return entries


def download_video_segment(url: str, start: float, end: float, output_path: Path):
    """Download a specific segment of the video."""
    start_str = format_time_yt(start)
    end_str = format_time_yt(end)
    
    cmd = [
        "yt-dlp",
        "--download-sections", f"*{start_str}-{end_str}",
        "--force-keyframes-at-cuts",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "-o", str(output_path),
        url,
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to download segment: {result.stderr}")
    
    return output_path


def format_time_yt(seconds: float) -> str:
    """Format seconds to MM:SS or HH:MM:SS for yt-dlp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"
