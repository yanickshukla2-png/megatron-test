from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import os
import tempfile
import uuid
from dotenv import load_dotenv
import openai
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

load_dotenv()

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION or not OPENAI_API_KEY:
    raise RuntimeError("Missing environment variables. Copy server/.env.example to server/.env and fill the keys.")

openai.api_key = OPENAI_API_KEY

app = FastAPI(title="Megatron Test — Voice Assistant Prototype")


def convert_to_wav(in_path: str) -> str:
    """Convert any supported audio file to a mono 16kHz WAV file (PCM 16-bit) using pydub/ffmpeg.

    Returns the path to the converted WAV file. The caller is responsible for removing the file.
    """
    try:
        audio = AudioSegment.from_file(in_path)
    except Exception as e:
        raise RuntimeError(f"Audio conversion failed (ffmpeg may be missing or file is invalid): {e}")

    # Normalize: mono, 16 kHz, 16-bit samples
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

    out_path = os.path.join(tempfile.gettempdir(), f"converted_{uuid.uuid4().hex}.wav")
    audio.export(out_path, format="wav")
    return out_path


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
async def voice_endpoint(background_tasks: BackgroundTasks, audio: UploadFile = File(...)):
    """Accepts an uploaded audio file and returns a synthesized WAV reply.

    Form field: audio (file)
    Returns: audio/wav file
    """
    suffix = os.path.splitext(audio.filename)[1] or ".wav"
    tmp_dir = tempfile.gettempdir()
    in_path = os.path.join(tmp_dir, f"upload_{uuid.uuid4().hex}{suffix}")
    out_path = os.path.join(tmp_dir, f"reply_{uuid.uuid4().hex}.wav")

    with open(in_path, "wb") as f:
        contents = await audio.read()
        f.write(contents)

    converted_path = None
    try:
        # Convert any incoming audio to WAV 16kHz mono for Azure compatibility
        converted_path = convert_to_wav(in_path)
        transcript = transcribe_audio_with_azure(converted_path)
    except Exception as e:
        # provide helpful error message (do not leak secrets)
        raise HTTPException(status_code=500, detail=f"Transcription/conversion error: {e}")

    try:
        reply_text = query_openai_system_reply(transcript)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI error: {e}")

    try:
        synthesize_speech_with_azure(reply_text, out_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    # Schedule temp file cleanup after response is sent
    background_tasks.add_task(lambda p: os.remove(p) if os.path.exists(p) else None, in_path)
    if converted_path:
        background_tasks.add_task(lambda p: os.remove(p) if os.path.exists(p) else None, converted_path)
    background_tasks.add_task(lambda p: os.remove(p) if os.path.exists(p) else None, out_path)

    return FileResponse(out_path, media_type="audio/wav", filename="reply.wav")
