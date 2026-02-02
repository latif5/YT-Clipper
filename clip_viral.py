#!/usr/bin/env python3
"""
Viral Video Clipper
Automatically clips the most viral segments from YouTube videos.

Usage:
    python clip_viral.py "https://youtu.be/VIDEO_ID"
"""

import sys
import re
from pathlib import Path

from src.utils import (
    print_header, print_step, print_success, print_error, print_info,
    create_progress, console,
)
from src.downloader import get_video_info, download_subtitles, parse_srt, download_full_video
from src.analyzer import analyze_viral_segments
from src.clipper import process_clip


def extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    patterns = [
        r"(?:v=|/)([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return url  # Assume it's already an ID


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print_error("Usage: python clip_viral.py <youtube_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    video_id = extract_video_id(url)
    
    print_header("🎬 Viral Video Clipper")
    print_info(f"Processing video: {video_id}")
    
    # Setup paths
    base_dir = Path(__file__).parent
    clips_dir = base_dir / "clips" / video_id
    clips_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Get video info
        info = get_video_info(url)
        title = info.get("title", "Unknown")
        duration = info.get("duration", 0)
        print_info(f"Title: {title}")
        print_info(f"Duration: {duration // 60}:{duration % 60:02d}")
        
        # Step 2: Download subtitles
        subtitle_path = download_subtitles(url, clips_dir)
        
        # Step 3: Parse subtitles
        subtitles = []
        if subtitle_path:
            subtitles = parse_srt(subtitle_path)
            print_info(f"Parsed {len(subtitles)} subtitle entries")
        
        # Step 4: Analyze for viral segments
        segments = analyze_viral_segments(
            subtitles,
            num_clips=3,
            min_duration=60,
            max_duration=180,
            target_duration=120,
        )
        
        if not segments:
            print_error("No viral segments found!")
            sys.exit(1)
        
        # Step 4.5: Download full video (optimization)
        video_path = clips_dir / "full_video.mp4"
        download_full_video(url, video_path)
        
        # Step 5: Process each clip
        print_header("📹 Processing Clips")
        
        with create_progress() as progress:
            overall_task = progress.add_task(
                "[bold blue]Overall Progress", 
                total=len(segments) * 100
            )
            
            for i, segment in enumerate(segments, 1):
                process_clip(
                    video_path=video_path,
                    segment=segment,
                    clip_num=i,
                    output_dir=clips_dir,
                    subtitle_path=subtitle_path,
                    progress=progress,
                )
                progress.update(overall_task, advance=100)
        
        # Cleanup full video
        if video_path.exists():
            video_path.unlink()
            print_info("Cleaned up temporary full video")
        
        # Done!
        print_header("✅ Complete!")
        print_success(f"Output folder: {clips_dir}")
        print_info("Each clip has 4 versions:")
        print_info("  • original/no_subs.mp4")
        print_info("  • original/with_subs.mp4")
        print_info("  • vertical/no_subs.mp4")
        print_info("  • vertical/with_subs.mp4")
        
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
