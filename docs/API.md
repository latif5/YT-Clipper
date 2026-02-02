# YT Clipper API Documentation

Base URL: `http://localhost:8000`

## Endpoints

### 1. Analyze Video

Starts the analysis process for a YouTube video.

- **URL**: `/analyze`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body**:

```json
{
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "callback_url": "https://your-server.com/webhook" // Optional
}
```

**Response**:

```json
{
  "video_id": "kg7f...convex_id...",
  "status": "analyzing"
}
```

### 2. Select Clip

Triggers the physical clipping and processing of a selected viral candidate.

- **URL**: `/select`
- **Method**: `POST`
- **Content-Type**: `application/json`

**Request Body**:

```json
{
  "clip_id": "jd8a...convex_id..."
}
```

**Response**:

```json
{
  "status": "queued"
}
```

## Webhooks

If `callback_url` is provided, the service sends POST requests on status changes.

**Payload**:

```json
{
  "video_id": "kg7f...",
  "clip_id": "jd8a...", // Only for clipping events
  "status": "waiting_for_selection" | "done" | "failed",
  "error": "Error message if failed",
  "output_path": "/path/to/clip.mp4" // Only on success
}
```

## Convex Data Model

You can subscribe to these tables directly using the Convex Client.

**Table: videos**

- `url`: String
- `status`: String
- `title`: String
- `duration`: Number
- `callbackUrl`: String

**Table: clips**

- `videoId`: ID (videos)
- `start`: Number (Seconds)
- `end`: Number (Seconds)
- `score`: Number (0-100)
- `reasoning`: String
- `status`: String
- `selected`: Boolean
- `output_path`: String
