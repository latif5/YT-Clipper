# YT Clipper Service - Setup Guide

## Prerequisites

- **Python 3.9+**
- **Node.js 18+** (for Convex)
- **FFmpeg** (must be in system PATH)
- **Convex Account** (https://convex.dev)
- **OpenRouter Account** (https://openrouter.ai) with valid API Key.

## Installation

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/your-repo/yt_clipper_service.git
    cd yt_clipper_service
    ```

2.  **Install Python Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Node Dependencies** (for Convex CLI)

    ```bash
    npm install -g convex
    ```

4.  **Environment Configuration**
    Copy `.env.example` to `.env` and fill in your keys:

    ```bash
    cp .env.example .env
    ```

    Edit `.env`:

    ```dotenv
    OPENROUTER_API_KEY=sk-or-v1-...
    CONVEX_URL=https://...convex.cloud
    ```

5.  **Initialize Database**
    Login to Convex and initialize the project:
    ```bash
    npx convex dev
    ```
    This will push the schema (`convex/schema.ts`) and functions (`convex/*.ts`) to your cloud instance.

## Running the Service

1.  **Start the API Server**

    ```bash
    uvicorn main:app --reload
    ```

    The server will run on `http://localhost:8000`.

2.  **Documentation**
    - Swagger UI: `http://localhost:8000/docs`
    - Redoc: `http://localhost:8000/redoc`

## Troubleshooting

- **FFmpeg not found**: Ensure `ffmpeg -version` works in your terminal. On macOS: `brew install ffmpeg`.
- **Convex Errors**: Ensure `npx convex dev` is running or you have deployed changes with `npx convex deploy`.
- **OpenAI/AI Errors**: Check your OpenRouter credits and API key validity.
