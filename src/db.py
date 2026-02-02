import os
from dotenv import load_dotenv
from convex import ConvexClient

load_dotenv()

args = dict()
if os.getenv("CONVEX_URL"):
    args["url"] = os.getenv("CONVEX_URL")

client = ConvexClient(**args)

def create_video(url: str, status: str = "analyzing", callback_url: str = None):
    args = {"url": url, "status": status}
    if callback_url:
        args["callbackUrl"] = callback_url
    return client.mutation("videos:create", args)

def update_video_status(video_id: str, status: str, **kwargs):
    client.mutation("videos:updateStatus", {"id": video_id, "status": status, **kwargs})

def add_clips(video_id: str, clips: list):
    # clips is list of dicts {start, end, score, reasoning}
    for clip in clips:
        client.mutation("clips:create", {
            "videoId": video_id,
            "start": clip["start"],
            "end": clip["end"],
            "score": clip["score"],
            "reasoning": clip["reasoning"],
            "status": "pending",
            "selected": False
        })

def get_clip(clip_id: str):
    return client.query("clips:get", {"id": clip_id})

def select_clip(clip_id: str):
    client.mutation("clips:select", {"id": clip_id})

def update_clip_status(clip_id: str, status: str, output_path: str = None):
    args = {"id": clip_id, "status": status}
    if output_path:
        args["output_path"] = output_path
    client.mutation("clips:updateStatus", args)

def get_video(video_id: str):
    return client.query("videos:get", {"id": video_id})
