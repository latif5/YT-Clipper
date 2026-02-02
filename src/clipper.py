"""
Video clipper and processor.
Handles video cutting, subtitle burning, and format conversion.
"""

import subprocess
import os
import shutil
from pathlib import Path
from typing import Dict, Optional
from .utils import (
    print_step, print_success, print_error, print_info,
    create_progress, format_time, console, get_ffmpeg_path,
)
from .subtitle_utils import extract_segment_subtitles
import os
import shutil


def process_clip(
    video_path: Path,
    segment: Dict,
    clip_num: int,
    output_dir: Path,
    subtitle_path: Optional[Path] = None,
    progress=None,
) -> Dict[str, Path]:
    """
    Process a single clip with all variants.
    
    Returns dict of output paths:
    - original_no_subs
    - original_with_subs
    - vertical_no_subs
    - vertical_with_subs
    """
    clip_dir = output_dir / f"clip_{clip_num}"
    original_dir = clip_dir / "original"
    vertical_dir = clip_dir / "vertical"
    
    original_dir.mkdir(parents=True, exist_ok=True)
    vertical_dir.mkdir(parents=True, exist_ok=True)
    
    start = segment["start"]
    end = segment["end"]
    duration = end - start
    
    # Paths
    temp_video = clip_dir / "temp_source.mp4"
    original_no_subs = original_dir / "no_subs.mp4"
    original_with_subs = original_dir / "with_subs.mp4"
    vertical_no_subs = vertical_dir / "no_subs.mp4"
    vertical_with_subs = vertical_dir / "with_subs.mp4"
    
    outputs = {}
    
    # Step 1: Download segment
    if progress:
        task = progress.add_task(f"[cyan]Clip {clip_num}: Downloading...", total=100)
    
    print_step(f"Clip {clip_num}", f"Cutting segment ({format_time(start)} - {format_time(end)})")
    cut_segment(video_path, start, end, temp_video)
    
    if progress:
        progress.update(task, completed=25, description=f"[cyan]Clip {clip_num}: Creating original...")
    
    # Step 2: Create original without subs
    print_info("Creating original version (no subs)...")
    create_clean_copy(temp_video, original_no_subs)
    outputs["original_no_subs"] = original_no_subs
    
    if progress:
        progress.update(task, completed=40, description=f"[cyan]Clip {clip_num}: Adding subtitles...")
    
    # Step 3: Create original with subs
    local_subs = clip_dir / "subs.srt"
    if subtitle_path and subtitle_path.exists():
        print_info("Creating original version (with subs)...")
        # Extract segment-specific subtitles with time offset
        if extract_segment_subtitles(subtitle_path, local_subs, start, end):
            burn_subtitles(temp_video, local_subs, original_with_subs, start)
            outputs["original_with_subs"] = original_with_subs
        else:
            print_info("No subtitles in this segment")
            create_clean_copy(temp_video, original_with_subs)
            outputs["original_with_subs"] = original_with_subs
    else:
        create_clean_copy(temp_video, original_with_subs)
        outputs["original_with_subs"] = original_with_subs
    
    if progress:
        progress.update(task, completed=60, description=f"[cyan]Clip {clip_num}: Creating vertical...")
    
    # Step 4: Create vertical without subs
    print_info("Creating vertical version (no subs)...")
    create_vertical(temp_video, vertical_no_subs)
    outputs["vertical_no_subs"] = vertical_no_subs
    
    if progress:
        progress.update(task, completed=80, description=f"[cyan]Clip {clip_num}: Vertical with subs...")
    
    # Step 5: Create vertical with subs
    if local_subs.exists():
        print_info("Creating vertical version (with subs)...")
        burn_subtitles_vertical(temp_video, local_subs, vertical_with_subs, start)
        outputs["vertical_with_subs"] = vertical_with_subs
    else:
        create_vertical(temp_video, vertical_with_subs)
        outputs["vertical_with_subs"] = vertical_with_subs
    
    if progress:
        progress.update(task, completed=100, description=f"[green]Clip {clip_num}: Done!")
    
    # Cleanup temp
    if temp_video.exists():
        temp_video.unlink()
    
    print_success(f"Clip {clip_num} complete: {clip_dir}")
    
    return outputs


def cut_segment(video_path: Path, start: float, end: float, output_path: Path):
    """Cut a segment from local video using ffmpeg (fast, no re-encode)."""
    duration = end - start
    
    cmd = [
        get_ffmpeg_path(), "-y",
        "-ss", str(start),
        "-i", str(video_path),
        "-t", str(duration),
        "-c", "copy",  # No re-encode for speed
        str(output_path),
    ]
    
    subprocess.run(cmd, capture_output=True)


def create_clean_copy(input_path: Path, output_path: Path):
    """Create a clean copy of the video."""
    cmd = [
        get_ffmpeg_path(), "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        str(output_path),
    ]
    
    subprocess.run(cmd, capture_output=True)


def escape_ffmpeg_path(path: Path) -> str:
    """Escape path for ffmpeg subtitle filter."""
    s = str(path)
    # ffmpeg subtitle filter requires escaping: backslash, colon, single quote
    s = s.replace("\\", "\\\\")
    s = s.replace(":", "\\:")
    s = s.replace("'", "'\\''")
    return s


def burn_subtitles(
    input_path: Path,
    subtitle_path: Path,
    output_path: Path,
    time_offset: float = 0,
):
    """Hard burn subtitles using libass (static ffmpeg required)."""
    # Create temp copy of subs to avoid path escaping issues
    temp_subs = subtitle_path.parent / f"temp_{os.urandom(4).hex()}.srt"
    shutil.copy(subtitle_path, temp_subs)
    
    # Path handling for filter
    subs_arg = str(temp_subs.resolve()).replace(':', '\\:')
    
    # Style: Fontsize=18 (Horizontal), Opaque box
    style = "Fontsize=18,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,BorderStyle=3,Outline=2,Shadow=0,MarginV=50,Alignment=2"
    
    cmd = [
        get_ffmpeg_path(), "-y",
        "-i", str(input_path),
        "-vf", f"subtitles='{subs_arg}':force_style='{style}'",
        "-c:v", "libx264",
        "-c:a", "copy",
        "-preset", "fast",
        "-crf", "23",
        str(output_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Cleanup
    if temp_subs.exists():
        temp_subs.unlink()
    
    if result.returncode != 0:
        print_error(f"Subtitle burn failed: {result.stderr[-500:]}")
        create_clean_copy(input_path, output_path)


def create_vertical(input_path: Path, output_path: Path):
    """Convert video to 9:16 vertical format."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", "crop=ih*9/16:ih,scale=1080:1920",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        "-crf", "23",
        str(output_path),
    ]
    
    subprocess.run(cmd, capture_output=True)


def burn_subtitles_vertical(
    input_path: Path,
    subtitle_path: Path,
    output_path: Path,
    time_offset: float = 0,
):
    """Hard burn subtitles onto vertical video using libass."""
    # Create temp copy of subs
    temp_subs = subtitle_path.parent / f"temp_v_{os.urandom(4).hex()}.srt"
    shutil.copy(subtitle_path, temp_subs)
    
    subs_arg = str(temp_subs.resolve()).replace(':', '\\:')
    
    # Style: Fontsize=12 (Vertical 608 width logic matched from skill)
    # But we scale to 1080:1920. Skill used crop=608:1080.
    # We use crop=ih*9/16:ih,scale=1080:1920. Width is always 1080.
    # Style: Fontsize=14 (Vertical - smaller as requested)
    style = "Fontsize=14,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,BorderStyle=3,Outline=2,Shadow=0,MarginV=80,Alignment=2"
    
    # Filter chain: Crop -> Scale -> Subtitles
    vf = f"crop=ih*9/16:ih,scale=1080:1920,subtitles='{subs_arg}':force_style='{style}'"

    cmd = [
        get_ffmpeg_path(), "-y",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-c:a", "copy",
        "-preset", "fast",
        "-crf", "23",
        str(output_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if temp_subs.exists():
        temp_subs.unlink()
    
    if result.returncode != 0:
        print_error(f"Vertical subtitle burn failed: {result.stderr[-500:]}")
        create_vertical(input_path, output_path)


def format_time_yt(seconds: float) -> str:
    """Format seconds for yt-dlp."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"
