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

## Usage

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
