"""
Subtitle utilities for extracting and offsetting subtitles for video segments.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Optional


def extract_segment_subtitles(
    full_srt_path: Path,
    output_path: Path,
    start_time: float,
    end_time: float,
) -> bool:
    """Extract subtitles for a segment and save to file."""
    subs = parse_srt_segment(full_srt_path, start_time, end_time)
    if not subs:
        return False
        
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, sub in enumerate(subs, 1):
            start_str = format_srt_time(sub['start'])
            end_str = format_srt_time(sub['end'])
            f.write(f"{i}\n{start_str} --> {end_str}\n{sub['text']}\n\n")
    return True


def parse_srt_segment(
    full_srt_path: Path,
    start_time: float,
    end_time: float,
) -> List[Dict]:
    """Parse and extract subtitle entries for a specific time segment."""
    if not full_srt_path.exists():
        return []
    
    with open(full_srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    blocks = content.strip().split('\n\n')
    results = []
    
    time_pattern = re.compile(
        r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})'
    )
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        
        for i, line in enumerate(lines):
            match = time_pattern.search(line)
            if match:
                g = match.groups()
                sub_start = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
                sub_end = int(g[4]) * 3600 + int(g[5]) * 60 + int(g[6]) + int(g[7]) / 1000
                
                if sub_end > start_time and sub_start < end_time:
                    new_start = max(0, sub_start - start_time)
                    new_end = min(end_time - start_time, sub_end - start_time)
                    
                    text_lines = lines[i + 1:]
                    text = "\n".join(text_lines)
                    
                    if text.strip():
                        results.append({
                            'start': new_start,
                            'end': new_end,
                            'text': text
                        })
                break
    return results


def generate_drawtext_filter(
    subtitles: List[Dict],
    font_path: str = "/System/Library/Fonts/Helvetica.ttc",
    font_size: int = 24,
    is_vertical: bool = False,
) -> str:
    """Generate a complex drawtext filter chain for hard burning subtitles."""
    filters = []
    
    # Adjust resolution-based settings
    # Assuming video is scaled to height 1080 (vertical) or 720/1080 (horizontal)
    if is_vertical:
        # Vertical 9:16 (1080x1920)
        # Font size needs to be larger relative to width
        final_font_size = 60
        margin_v = 200
    else:
        # Horizontal 16:9 (1920x1080)
        final_font_size = 48
        margin_v = 100
        
    for sub in subtitles:
        start = sub['start']
        end = sub['end']
        text = sub['text']
        
        # Escape text for drawtext
        # 1. Escape \ as \\
        # 2. Escape ' as \u2019 (smart quote) or complex escaping
        # Simple approach: replace ' with nothing or simple escape
        clean_text = text.replace("\\", "\\\\").replace("'", "\u2019").replace(":", "\\:")
        clean_text = clean_text.replace("\n", " ") # Force single line for simplicity or strictly split
        
        # Drawtext filter
        # box=1:boxcolor=black@0.5:boxborderw=10
        dt = (
            f"drawtext=fontfile='{font_path}':text='{clean_text}':"
            f"fontsize={final_font_size}:fontcolor=white:"
            f"box=1:boxcolor=black@0.6:boxborderw=10:"
            f"x=(w-text_w)/2:y=h-th-{margin_v}:"
            f"enable='between(t,{start:.3f},{end:.3f})'"
        )
        filters.append(dt)
        
    return ",".join(filters)


def format_srt_time(seconds: float) -> str:
    """Format seconds to SRT timestamp format HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"
