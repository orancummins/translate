"""Flask web app: Tripadvisor hotel-manager sales roleplay trainer."""

import os

from dotenv import load_dotenv
from dotenv import set_key
from flask import Flask, Response, g, jsonify, render_template, request
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

import brands
import claude_client
import db
import tts
from personas import DIFFICULTY_BY_ID

# KEY_MODE "server" (the default, your own machine): keys live in .env and the key box saves them there.
# KEY_MODE "visitor" (a shared server): every visitor pastes their own Claude and ElevenLabs keys; they stay in that
# visitor's browser and come with each request; nothing is stored here, and each visitor sees only their own calls.
KEY_MODE = os.environ.get("KEY_MODE", "server").strip().lower()
VISITOR = KEY_MODE == "visitor"
ENV_PATH = claude_client.ENV_PATH

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)   # served at oran-dev.com/translate/ behind nginx
db.init_db()


@app.before_request
def keys_from_visitor():
    if VISITOR:
        g.claude_key = (request.headers.get("X-Claude-Key") or "").strip() or None
        g.voice_key = (request.headers.get("X-ElevenLabs-Key") or "").strip() or None
        g.owner = (request.headers.get("X-Visitor") or "").strip()[:64] or "anonymous"
    else:
        g.claude_key = None
        g.voice_key = os.environ.get("ELEVENLABS_API_KEY") or None
        g.owner = None


def owns(session):
    return session and (g.owner is None or session.get("owner") == g.owner)

BRAND = brands.get_brand()


def error(message, status=400):
    return jsonify({"error": message}), status


@app.get("/")
def index():
    return render_template("index.html", brand=BRAND)


@app.get("/api/options")
def api_options():
    return jsonify(brands.options_payload(BRAND))


@app.get("/api/config")
def api_get_config():
    if VISITOR:
        return jsonify({"mode": "visitor", "configured": bool(g.claude_key), "voice": bool(g.voice_key), "elevenlabs_configured": bool(g.voice_key)})
    return jsonify({"mode": "server", "configured": claude_client.is_configured(), "voice": bool(g.voice_key), "elevenlabs_configured": bool(g.voice_key)})


@app.post("/api/config")
def api_set_config():
    """Check the keys a visitor pasted. On your own machine (server mode) they are saved to .env; on a shared server
    (visitor mode) nothing is stored: the browser keeps them."""
    payload = request.get_json(silent=True) or {}
    if payload.get("clear_elevenlabs"):                     # back to the browser's voices
        if not VISITOR:
            from dotenv import unset_key
            unset_key(str(ENV_PATH), "ELEVENLABS_API_KEY")
            os.environ.pop("ELEVENLABS_API_KEY", None)
        return jsonify({"ok": True, "voice": False})
    api_key = (payload.get("api_key") or "").strip()
    voice_key = (payload.get("elevenlabs_key") or "").strip()
    if not api_key and not voice_key:
        return error("Paste a key first")
    if api_key:
        try:
            if VISITOR: claude_client.validate_key(api_key)
            else: claude_client.validate_and_store_key(api_key)
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a clean error
            body = getattr(exc, "body", None)
            message = (body.get("error", {}).get("message") if isinstance(body, dict) else None) or str(exc)
            return error(f"That Claude key didn't work: {message}", 400)
    if voice_key:
        try: tts.validate(voice_key)
        except Exception as exc:  # noqa: BLE001
            return error(f"That ElevenLabs key didn't work: {exc}", 400)
        if not VISITOR:
            set_key(str(ENV_PATH), "ELEVENLABS_API_KEY", voice_key)
            os.environ["ELEVENLABS_API_KEY"] = voice_key
    return jsonify({"ok": True, "mode": KEY_MODE})


@app.post("/api/tts")
def api_tts():
    """The reply spoken by ElevenLabs (audio/mpeg). 404 with no key, so the browser uses its own voices."""
    if not g.voice_key:
        return error("No ElevenLabs key", 404)
    payload = request.get_json(silent=True) or {}
    try:
        audio = tts.speech(payload.get("text"), payload.get("role") or "assistant", g.voice_key)
    except ValueError as exc:
        return error(str(exc))
    except Exception as exc:  # noqa: BLE001
        return error(f"Could not make the voice: {exc}", 502)
    return Response(audio, mimetype="audio/mpeg", headers={"Cache-Control": "private, max-age=86400"})


@app.get("/api/sessions")
def api_list_sessions():
    return jsonify(db.list_sessions(g.owner))


@app.post("/api/sessions")
def api_create_session():
    payload = request.get_json(silent=True) or {}
    hotel_type_id = payload.get("hotel_type_id")
    persona_id = payload.get("persona_id")
    difficulty_id = payload.get("difficulty_id")
    locale_id = payload.get("locale_id")

    if hotel_type_id not in BRAND["company_type_by_id"]:
        return error("Unknown hotel_type_id")
    if persona_id not in BRAND["persona_by_id"]:
        return error("Unknown persona_id")
    if difficulty_id not in DIFFICULTY_BY_ID:
        return error("Unknown difficulty_id")
    if locale_id not in BRAND["locale_by_id"]:
        return error("Unknown locale_id")

    locale = BRAND["locale_by_id"][locale_id]

    try:
        scenario = claude_client.generate_scenario(
            hotel_type_id=hotel_type_id,
            persona_id=persona_id,
            difficulty_id=difficulty_id,
            locale_id=locale_id,
        )
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a clean error
        return error(f"Could not generate scenario: {exc}", 502)

    session_id = db.create_session(
        language=locale["language"],
        locale=locale_id,
        locale_label=locale["label"],
        hotel_type_id=hotel_type_id,
        hotel_type_label=BRAND["company_type_by_id"][hotel_type_id]["label"],
        persona_id=persona_id,
        persona_label=BRAND["persona_by_id"][persona_id]["label"],
        difficulty_id=difficulty_id,
        hotel_name=scenario["hotel_name"],
        manager_name=scenario["manager_name"],
        scenario_brief=scenario["brief_en"],
        owner=g.owner or "",
    )

    return jsonify(db.get_session(session_id)), 201


@app.get("/api/sessions/<session_id>")
def api_get_session(session_id):
    session = db.get_session(session_id)
    if not owns(session):
        return error("Session not found", 404)
    session["messages"] = db.get_messages(session_id)
    return jsonify(session)


@app.delete("/api/sessions/<session_id>")
def api_delete_session(session_id):
    session = db.get_session(session_id)
    if not owns(session):
        return error("Session not found", 404)
    db.delete_session(session_id)
    return jsonify({"ok": True})


@app.post("/api/sessions/<session_id>/messages")
def api_post_message(session_id):
    session = db.get_session(session_id)
    if not owns(session):
        return error("Session not found", 404)

    payload = request.get_json(silent=True) or {}
    text = (payload.get("text") or "").strip()
    if not text:
        return error("Message text is required")

    db.add_message(session_id, "user", text)

    system_prompt = claude_client.build_system_prompt(
        hotel_type_id=session["hotel_type_id"],
        persona_id=session["persona_id"],
        difficulty_id=session["difficulty_id"],
        locale_id=session["locale"],
        hotel_name=session["hotel_name"],
        manager_name=session["manager_name"],
    )
    history = [{"role": m["role"], "text": m["text"]} for m in db.get_messages(session_id)]

    try:
        reply_text = claude_client.manager_reply(system_prompt=system_prompt, history=history)
    except Exception as exc:  # noqa: BLE001
        return error(f"Could not get a reply: {exc}", 502)

    message_id = db.add_message(session_id, "assistant", reply_text)
    return jsonify(db.get_message(message_id)), 201


@app.post("/api/messages/<int:message_id>/translate")
def api_translate_message(message_id):
    message = db.get_message(message_id)
    if not message or not owns(db.get_session(message["session_id"])):
        return error("Message not found", 404)
    if message["translation"]:
        return jsonify(message)

    session = db.get_session(message["session_id"])
    try:
        translation = claude_client.translate_text(
            message["text"], source_language=session["language"]
        )
    except Exception as exc:  # noqa: BLE001
        return error(f"Could not translate: {exc}", 502)

    db.set_translation(message_id, translation)
    return jsonify(db.get_message(message_id))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    host = os.environ.get("HOST", "0.0.0.0")
    if os.environ.get("SERVE") == "1":                    # the always-on server (serve.sh): a proper WSGI server, no debugger
        from waitress import serve
        serve(app, host=host, port=port, threads=8)
    else:
        app.run(host=host, port=port, debug=os.environ.get("FLASK_DEBUG", "1") == "1")
