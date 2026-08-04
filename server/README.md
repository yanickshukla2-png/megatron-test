# Server — Voice assistant prototype

This folder contains a minimal FastAPI server demonstrating an end-to-end voice flow:
- Receive an audio file (WAV/MP3/M4A/FLAC)
- Convert uploaded audio to mono 16kHz WAV using pydub + ffmpeg
- Transcribe with Azure Speech SDK
- Send transcript to OpenAI for a reply
- Synthesize reply with Azure TTS and return audio/wav

Prerequisites
- Python 3.10+
- ffmpeg installed on the host (pydub uses ffmpeg). Install examples:
  - macOS (Homebrew): brew install ffmpeg
  - Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg
  - Windows (Chocolatey): choco install ffmpeg

Run locally
1. cd server
2. python -m venv .venv
3. source .venv/bin/activate   # or .venv\Scripts\activate on Windows
4. pip install -r requirements.txt
5. cp .env.example .env and fill in your keys
6. uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

Quick test (curl)

curl -X POST "http://localhost:8000/voice" -F "audio=@/path/to/file.wav" --output reply.wav

Notes
- The server now accepts common audio formats and converts them to a WAV file compatible with Azure Speech.
- pydub requires ffmpeg to be installed on the system. If conversion fails, ensure ffmpeg is available in PATH.
- This scaffold uses synchronous Azure SDK calls for simplicity. For production you may want streaming recognition and async TTS.
- Do not commit real API keys. Use the .env file or a secret store.
