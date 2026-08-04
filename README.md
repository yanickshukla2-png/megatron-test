# Megatron Test — Voice Assistant Prototype

This repository contains a minimal prototype server demonstrating a voice pipeline: speech-to-text (Azure Speech) -> OpenAI (NLU/response) -> text-to-speech (Azure Speech).

Purpose
- Provide a starting point for the MVP voice flow.

Files added
- server/app.py — FastAPI server with /voice endpoint accepting an audio file and returning synthesized audio reply.
- server/requirements.txt — Python dependencies.
- server/.env.example — example environment variables.

Quick start
1. Clone the repo.
2. Create a Python 3.10+ virtual environment.
3. Copy server/.env.example to server/.env and fill in the keys (AZURE_SPEECH_KEY, AZURE_SPEECH_REGION, OPENAI_API_KEY).
4. Install dependencies: pip install -r server/requirements.txt
5. Run the server: uvicorn server.app:app --reload --host 0.0.0.0 --port 8000
6. POST an audio file (WAV/MP3) to POST /voice as form-data field `audio`. The endpoint returns an audio/wav reply.

Notes
- This is a demo scaffold. Replace the OpenAI call and Azure config with your preferred provider if you want (Azure OpenAI, different TTS voices, etc.).
- Do not commit your real .env keys to the repo.
