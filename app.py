"""Flask web app: Tripadvisor hotel-manager sales roleplay trainer."""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

import brands
import claude_client
import db
from personas import DIFFICULTY_BY_ID

app = Flask(__name__)
db.init_db()

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
    return jsonify({"configured": claude_client.is_configured()})


@app.post("/api/config")
def api_set_config():
    payload = request.get_json(silent=True) or {}
    api_key = (payload.get("api_key") or "").strip()
    if not api_key:
        return error("API key is required")
    try:
        claude_client.validate_and_store_key(api_key)
    except Exception as exc:  # noqa: BLE001 - surfaced to the caller as a clean error
        body = getattr(exc, "body", None)
        message = (
            body.get("error", {}).get("message") if isinstance(body, dict) else None
        ) or str(exc)
        return error(f"That key didn't work: {message}", 400)
    return jsonify({"ok": True})


@app.get("/api/sessions")
def api_list_sessions():
    return jsonify(db.list_sessions())


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
    )

    return jsonify(db.get_session(session_id)), 201


@app.get("/api/sessions/<session_id>")
def api_get_session(session_id):
    session = db.get_session(session_id)
    if not session:
        return error("Session not found", 404)
    session["messages"] = db.get_messages(session_id)
    return jsonify(session)


@app.delete("/api/sessions/<session_id>")
def api_delete_session(session_id):
    session = db.get_session(session_id)
    if not session:
        return error("Session not found", 404)
    db.delete_session(session_id)
    return jsonify({"ok": True})


@app.post("/api/sessions/<session_id>/messages")
def api_post_message(session_id):
    session = db.get_session(session_id)
    if not session:
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
    if not message:
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
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
