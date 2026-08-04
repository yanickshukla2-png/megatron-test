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
- OpenSSL (for convenience scripts) or another method to create a localhost cert

Install and run (HTTP)
1. cd server
2. python -m venv .venv
3. source .venv/bin/activate   # or .venv\Scripts\activate on Windows
4. pip install -r requirements.txt
5. cp .env.example .env and fill in your keys
6. uvicorn server.app:app --reload --host 0.0.0.0 --port 8000

Test with curl (HTTP)

curl -X POST "http://localhost:8000/voice" -F "audio=@/path/to/file.mp3" --output reply.wav

Run with HTTPS (localhost)

The server supports HTTPS when you provide a certificate and key. The repository includes helper scripts to generate a self-signed certificate for localhost and run uvicorn with it.

1. Ensure openssl is installed and on your PATH.
2. From the server folder, generate cert and run server (Linux/macOS):
   - chmod +x run_https.sh
   - ./run_https.sh

   Or on Windows (PowerShell, run as Administrator if needed):
   - ./generate_cert.ps1

This will create server/ssl/cert.pem and server/ssl/key.pem and start uvicorn with --ssl-keyfile/--ssl-certfile.

Browser note: Browsers will warn about the self-signed certificate. To use the static HTML client at https://localhost:8000/static/index.html you must trust the generated cert in your OS/browser. Alternatively, test with curl using -k to ignore certificate errors:

curl -k -X POST "https://localhost:8000/voice" -F "audio=@/path/to/file.mp3" --output reply.wav

Static client (simple in-browser demo)

A simple HTML client is included at server/static/index.html. It records microphone audio and sends it to https://localhost:8000/voice. To use it in the browser:
- Run the server with HTTPS (see above).
- Trust the generated certificate in your OS/browser (or use a browser profile that allows proceeding on localhost).
- Open https://localhost:8000/static/index.html in the browser.

Troubleshooting
- If conversion fails, verify ffmpeg is installed and accessible (ffmpeg -version).
- If OpenAI or Azure calls fail, check .env values and quotas/permissions.
- If the browser blocks the request due to certificate issues, use curl -k for testing or trust the cert.

Security note
- Self-signed certificates are only for local development. For production use a certificate from a trusted CA.
- Do not commit real API keys. Use the .env file or a secret manager.
