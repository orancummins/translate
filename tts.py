"""Text to speech with ElevenLabs, for the manager's replies and for replaying a call.

The key comes from the visitor's own request (visitor mode: the X-ElevenLabs-Key header) or from ELEVENLABS_API_KEY in
.env (server mode, the owner's machine). With no key, /api/tts says so and the browser falls back to its own voices.
Audio is cached in data/tts_cache by voice, model and text, so a line already spoken costs nothing the second time.

Voices (set in .env to change them): ELEVENLABS_VOICE_MANAGER for the other side of the call, ELEVENLABS_VOICE_USER for
your own lines when a call is replayed. eleven_multilingual_v2 speaks English and Spanish with the same voice."""
import hashlib
import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path

try:
    import certifi
    _TLS = ssl.create_default_context(cafile=certifi.where())   # a python.org build has no certificates of its own
except ImportError:
    _TLS = ssl.create_default_context()

CACHE = Path(__file__).parent / "data" / "tts_cache"
MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
VOICES = {
    "assistant": os.environ.get("ELEVENLABS_VOICE_MANAGER", "21m00Tcm4TlvDq8ikWAM"),   # "Rachel", a premade voice every account has
    "user": os.environ.get("ELEVENLABS_VOICE_USER", "pNInz6obpgDQGcFmaJgB"),           # "Adam"
}
API = "https://api.elevenlabs.io/v1"


def _cache_file(voice, text):
    return CACHE / (hashlib.sha1(f"{voice}|{MODEL}|{text}".encode("utf-8")).hexdigest() + ".mp3")


def validate(key):
    """Raise ValueError with a readable reason if the key does not work."""
    req = urllib.request.Request(f"{API}/user", headers={"xi-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=15, context=_TLS) as r:
            r.read()
    except urllib.error.HTTPError as e:
        try: msg = json.loads(e.read()).get("detail", {})
        except ValueError: msg = {}
        reason = msg.get("message") if isinstance(msg, dict) else str(msg)
        raise ValueError(reason or f"ElevenLabs said HTTP {e.code}")


def speech(text, role, key):
    """MP3 bytes for text in the voice for role ("assistant" or "user"), from the cache or from ElevenLabs."""
    text = (text or "").strip()[:2500]
    if not text: raise ValueError("Nothing to say")
    voice = VOICES.get(role) or VOICES["assistant"]
    f = _cache_file(voice, text)
    if f.exists(): return f.read_bytes()
    body = json.dumps({"text": text, "model_id": MODEL, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}).encode()
    req = urllib.request.Request(f"{API}/text-to-speech/{voice}?output_format=mp3_44100_128", data=body, method="POST",
                                 headers={"xi-api-key": key, "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(req, timeout=60, context=_TLS) as r:
            audio = r.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"ElevenLabs said HTTP {e.code}")
    CACHE.mkdir(parents=True, exist_ok=True)
    tmp = f.with_suffix(".tmp"); tmp.write_bytes(audio); tmp.replace(f)
    return audio
