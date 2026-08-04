from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import tempfile
import uuid
from dotenv import load_dotenv
import openai
import azure.cognitiveservices.speech as speechsdk

load_dotenv()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION or not OPENAI_API_KEY:
    raise RuntimeError("Missing environment variables. Copy server/.env.example to server/.env and fill the keys.")

openai.api_key = OPENAI_API_KEY

app = FastAPI(title="Megatron Test — Voice Assistant Prototype")


def transcribe_audio_with_azure(wav_path: str) -> str:
    """Transcribe a WAV audio file using Azure Speech SDK (synchronous)."""
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    audio_input = speechsdk.audio.AudioConfig(filename=wav_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        raise RuntimeError(f"Speech recognition failed: {result.reason}")


def synthesize_speech_with_azure(text: str, out_path: str) -> None:
    """Synthesize text to WAV using Azure Speech SDK."""
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    # You can change the voice name to one available in your region.
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_text(text)
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"Speech synthesis failed: {result.reason}")


def query_openai_system_reply(user_text: str) -> str:
    """Send the transcribed text to OpenAI and return the assistant reply."""
    prompt_messages = [
        {"role": "system", "content": "You are a helpful voice assistant. Keep replies concise and action-oriented."},
        {"role": "user", "content": user_text},
    ]

    resp = openai.ChatCompletion.create(model=OPENAI_MODEL, messages=prompt_messages, max_tokens=300, temperature=0.6)
    return resp.choices[0].message.content.strip()


@app.post("/voice")
async def voice_endpoint(audio: UploadFile = File(...)):
    """Accepts an uploaded audio file (WAV) and returns a synthesized WAV reply.

    Form field: audio (file)
    Returns: audio/wav file
    """
    suffix = os.path.splitext(audio.filename)[1] or ".wav"
    if suffix.lower() not in [".wav", ".mp3", ".m4a", ".flac"]:
        # We'll accept common formats but Azure SDK examples use WAV. If you upload other formats, conversion may be required.
        pass

    tmp_dir = tempfile.gettempdir()
    in_path = os.path.join(tmp_dir, f"upload_{uuid.uuid4().hex}{suffix}")
    out_path = os.path.join(tmp_dir, f"reply_{uuid.uuid4().hex}.wav")

    with open(in_path, "wb") as f:
        contents = await audio.read()
        f.write(contents)

    try:
        # NOTE: Azure recognizer examples typically expect WAV with compatible sample rate.
        transcript = transcribe_audio_with_azure(in_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {e}")

    try:
        reply_text = query_openai_system_reply(transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    try:
        synthesize_speech_with_azure(reply_text, out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    return FileResponse(out_path, media_type="audio/wav", filename="reply.wav")
