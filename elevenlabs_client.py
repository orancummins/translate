"""Wraps the ElevenLabs text-to-speech REST API for higher-quality, less
robotic voice playback than the browser's built-in speechSynthesis.

Entirely optional: if ELEVENLABS_API_KEY isn't set, is_configured() is False
and the frontend falls back to the existing browser-voice system."""

import os

import requests

API_BASE = "https://api.elevenlabs.io/v1"
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # "Rachel" — stable premade voice
MODEL_ID = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
MAX_CHARS = 2000  # sanity cap — a manager reply/translation is a few hundred chars


def is_configured():
    return bool(os.environ.get("ELEVENLABS_API_KEY"))


def synthesize(text):
    """Returns MP3 audio bytes for the given text, or None if not configured."""
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        return None
    if len(text) > MAX_CHARS:
        raise ValueError(f"Text too long to synthesize ({len(text)} > {MAX_CHARS} characters)")

    response = requests.post(
        f"{API_BASE}/text-to-speech/{VOICE_ID}",
        params={"output_format": "mp3_44100_128"},
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json={
            "text": text,
            "model_id": MODEL_ID,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=20,
    )
    response.raise_for_status()
    return response.content
