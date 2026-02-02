import os
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

from src.db import create_video, update_video_status, add_clips, get_clip, update_clip_status, get_video, select_clip, client as convex_client
from src.downloader import get_video_info, download_subtitles, parse_srt, download_full_video
from src.analyzer import analyze_viral_segments
from src.clipper import process_clip

load_dotenv()

app = FastAPI(title="YT Clipper Service")

# Request Models
class AnalyzeRequest(BaseModel):
    url: str
    callback_url: Optional[str] = None

class SelectClipRequest(BaseModel):
    clip_id: str # Convex ID

def trigger_callback(url: str, data: dict):
    if not url:
        return
    try:
        requests.post(url, json=data, timeout=5)
    except Exception as e:
        print(f"Callback failed: {e}")

# Background Tasks
def run_analysis(video_id: str, url: str, callback_url: str = None):
    try:
        print(f"Starting analysis for {video_id}")
        
        # 1. Info
        info = get_video_info(url)
        title = info.get("title", "Unknown")
        duration = info.get("duration", 0)
        
        update_video_status(video_id, "analyzing", title=title, duration=duration)
        
        # 2. Subtitles
        # Use a temp dir or specific ID dir
        base_dir = Path("clips") / video_id
        base_dir.mkdir(parents=True, exist_ok=True)
        
        subtitle_path = download_subtitles(url, base_dir)
        if not subtitle_path:
             update_video_status(video_id, "failed", error="No subtitles found")
             trigger_callback(callback_url, {"video_id": video_id, "status": "failed", "error": "No subtitles"})
             return

        subtitles = parse_srt(subtitle_path)
        
        # 3. Analyze
        segments = analyze_viral_segments(subtitles)
        
        if not segments:
            update_video_status(video_id, "failed", error="No viral segments found")
            trigger_callback(callback_url, {"video_id": video_id, "status": "failed", "error": "No segments"})
            return
            
        # 4. Save Clips
        formatted_clips = []
        for seg in segments:
            formatted_clips.append({
                "start": seg["start"],
                "end": seg["end"],
                "score": seg.get("score", 0),
                "reasoning": seg.get("reasoning", "AI selected"),
            })
            
        add_clips(video_id, formatted_clips)
        update_video_status(video_id, "waiting_for_selection")
        print(f"Analysis complete for {video_id}")
        trigger_callback(callback_url, {"video_id": video_id, "status": "waiting_for_selection"})
        
    except Exception as e:
        print(f"Analysis failed: {e}")
        update_video_status(video_id, "failed", error=str(e))
        trigger_callback(callback_url, {"video_id": video_id, "status": "failed", "error": str(e)})

def run_clipping(clip_id: str):
    try:
        # Get clip and video data
        clip = get_clip(clip_id)
        if not clip:
            print("Clip not found")
            return
            
        video = get_video(clip["videoId"])
        if not video:
             print("Video not found")
             return
             
        video_id = video["_id"] # ID string
        url = video["url"]
        callback_url = video.get("callbackUrl")
        
        update_clip_status(clip_id, "processing")
        
        # Setup directories
        base_dir = Path("clips") / video_id
        base_dir.mkdir(parents=True, exist_ok=True)
        video_path = base_dir / "full_video.mp4"
        subtitle_path = base_dir / "subs.srt" # Assumption: subs exist from analysis step
        
        # Ensure video exists
        if not video_path.exists():
            print("Downloading full video...")
            download_full_video(url, video_path)
            
        # Clip
        # process_clip returns dict of paths
        result = process_clip(
            video_path=video_path,
            segment={"start": clip["start"], "end": clip["end"]},
            clip_num=1, # Todo: maybe use clip ID suffix
            output_dir=base_dir,
            subtitle_path=subtitle_path if subtitle_path.exists() else None
        )
        
        # Update status
        # Just use one output path for now (e.g. vertical with subs)
        # Ideally we store all permutations, but let's store the main one
        output_path = str(result.get("vertical_with_subs", ""))
        
        update_clip_status(clip_id, "done", output_path=output_path)
        print(f"Clipping success: {output_path}")
        
        trigger_callback(callback_url, {
            "video_id": video_id, 
            "clip_id": clip_id, 
            "status": "done", 
            "output_path": output_path
        })
        
    except Exception as e:
        print(f"Clipping failed: {e}")
        update_clip_status(clip_id, "failed")
        # Need to fetch video callback url again if not in scope, but we likely have it
        if 'video' in locals():
             trigger_callback(video.get("callbackUrl"), {"clip_id": clip_id, "status": "failed", "error": str(e)})

@app.post("/analyze")
async def analyze_video(req: AnalyzeRequest, background_tasks: BackgroundTasks):
    # Create DB entry
    video_id = create_video(req.url, callback_url=req.callback_url)
    
    # Start background task
    background_tasks.add_task(run_analysis, video_id, req.url, req.callback_url)
    
    return {"video_id": video_id, "status": "analyzing"}

@app.post("/select")
async def select_clip(req: SelectClipRequest, background_tasks: BackgroundTasks):
    # Select in DB
    select_clip(req.clip_id)
    background_tasks.add_task(run_clipping, req.clip_id)
    return {"status": "queued"}

@app.get("/")
def read_root():
    return {"status": "ok", "service": "YT Clipper"}
