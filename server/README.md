# Server — Voice assistant prototype

This folder contains a minimal FastAPI server demonstrating an end-to-end voice flow:
- Receive an audio file (WAV)
- Transcribe with Azure Speech SDK
- Send transcript to OpenAI for a reply
- Synthesize reply with Azure TTS and return audio/wav

Run locally
1. cd server
2. python -m venv .venv
3. source .venv/bin/activate   # or .venv\Scripts\activate on Windows
4. pip install -r requirements.txt
5. cp .env.example .env and fill in your keys
6. uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

Quick test (curl)

curl -X POST "http://localhost:8000/voice" -F "audio=@path/to/file.wav" --output reply.wav

Notes
- The Azure Speech SDK examples generally expect WAV audio with a compatible sample rate. If you upload MP3/M4A/FLAC you may need to convert to WAV first.
- This scaffold uses synchronous Azure SDK calls for simplicity. For production you may want streaming recognition and async TTS.
- Do not commit real API keys. Use the .env file or a secret store.
