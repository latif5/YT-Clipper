# Viral Video Clipper

A Python tool to automatically clip viral segments from YouTube videos with subtitles.

## Features

- 🔍 Automatic viral segment detection
- 📝 Subtitle burning with black background
- 📱 Vertical (9:16) video conversion
- 📊 Progress bar with status info
- 📁 Organized folder output

## Requirements

- Python 3.9+
- ffmpeg
- yt-dlp

## Installation

```bash
pip install -r requirements.txt
```

## Usage (API Service)

1. **Start the Server**:

   ```bash
   uvicorn main:app --reload
   ```

2. **Analyze a Video**:

   ```bash
   curl -X POST "http://localhost:8000/analyze" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://youtu.be/VIDEO_ID", "callback_url": "http://your-webhook.com"}'
   ```

   Response: `{"video_id": "convex_id", "status": "analyzing"}`

3. **Select a Clip**:
   Once you receive a callback or check status (via Convex dashboard), select a clip:
   ```bash
   curl -X POST "http://localhost:8000/select" \
        -H "Content-Type: application/json" \
        -d '{"clip_id": "convex_clip_id"}'
   ```

## CLI Usage (Legacy)

```bash
python clip_viral.py "https://youtu.be/VIDEO_ID"
```

## Output Structure

```
clips/
└── [video_id]/
    ├── clip_1/
    │   ├── original/
    │   │   ├── with_subs.mp4
    │   │   └── no_subs.mp4
    │   └── vertical/
    │       ├── with_subs.mp4
    │       └── no_subs.mp4
    ├── clip_2/...
    └── clip_3/...
```
