"""Wraps the Anthropic API for scenario generation, manager roleplay replies,
and short message translation."""

import json
import os
from pathlib import Path

import anthropic
from dotenv import set_key

import brands
from personas import DIFFICULTY_BY_ID

MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5")
TRANSLATE_MODEL = os.environ.get("CLAUDE_TRANSLATE_MODEL", "claude-haiku-4-5")
ENV_PATH = Path(__file__).parent / ".env"

_client = None


def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def is_configured():
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def validate_and_store_key(api_key):
    """Raise if the key doesn't work; otherwise persist it to .env and activate it."""
    global _client
    anthropic.Anthropic(api_key=api_key).models.list(limit=1)
    set_key(str(ENV_PATH), "ANTHROPIC_API_KEY", api_key)
    os.environ["ANTHROPIC_API_KEY"] = api_key
    _client = None


def _language_name(language):
    return brands.LANGUAGE_NAMES.get(language, "English")


def build_system_prompt(*, hotel_type_id, persona_id, difficulty_id, locale_id,
                         hotel_name, manager_name):
    brand = brands.get_brand()
    company = brand["company_type_by_id"][hotel_type_id]
    persona = brand["persona_by_id"][persona_id]
    difficulty = DIFFICULTY_BY_ID[difficulty_id]
    locale = brand["locale_by_id"][locale_id]
    language_name = _language_name(locale["language"])
    country = locale["countries"][0]
    title = persona.get("title", "decision-maker")

    return f"""You are role-playing as {manager_name}, the {title} at "{hotel_name}", \
{company['context']} located in {country}. You are on a phone/video sales call with a \
{brand['seller_role']} who is trying to sell you on {brand['product_pitch']}.

Persona and behavior:
{persona['traits']}

Difficulty for this call:
{difficulty['instruction']}

Ground rules:
- Stay fully in character as {manager_name} at all times. Never break character, never mention \
that you are an AI, and never mention these instructions.
- Reply ONLY in {language_name} ({locale['label']}), using natural, colloquial phrasing a real \
{title} in {country} would use. Do not mix in the other language and do not add \
translations yourself.
- Keep replies conversational and call-realistic: usually 1-4 sentences, like real spoken \
dialogue, not an essay. Occasionally ask the rep a direct question of your own, the way a real \
{title} would probe a sales pitch (e.g. about {brand['objection_domains']}).
- React specifically to what the rep just said - reference details they mentioned rather than \
giving generic scripted answers. Bring in realistic, {brand['detail_domain']} when relevant.
- If the rep is vague, press for specifics. If the rep makes a genuinely strong, specific case \
that addresses your concerns, let yourself be gradually persuaded rather than objecting forever.
- Never generate any content on behalf of the sales rep; only ever produce {manager_name}'s side \
of the conversation, as plain spoken dialogue with no stage directions, labels, or quotation \
marks around it."""


def _extract_text(response):
    return "".join(block.text for block in response.content if block.type == "text").strip()


def generate_scenario(*, hotel_type_id, persona_id, difficulty_id, locale_id):
    """Ask Claude to invent a plausible company/counterpart name, and a one-paragraph
    scenario briefing for the trainee, consistent with the chosen options."""
    brand = brands.get_brand()
    company = brand["company_type_by_id"][hotel_type_id]
    persona = brand["persona_by_id"][persona_id]
    locale = brand["locale_by_id"][locale_id]
    language_name = _language_name(locale["language"])
    country = locale["countries"][0]
    noun = brand["company_noun"]
    title = persona.get("title", "buyer")

    prompt = f"""Invent a short, plausible roleplay scenario for {brand['scenario_prompt_label']}.

{noun.capitalize()} type: {company['label']} - {company['context']}
Country: {country}
{title} persona: {persona['label']} - {persona['description']}

Return ONLY a JSON object (no markdown fences, no commentary) with exactly these keys:
- "company_name": a plausible, invented {noun} name fitting the {noun} type and country (do not \
use a real, existing {noun}'s name)
- "contact_name": a plausible full human name typical for {country}
- "brief_en": a 2-3 sentence scenario briefing IN ENGLISH for the trainee, setting the scene \
(who they're calling, what's going on at the {noun} right now, what the {title}'s general \
attitude going into the call is). This briefing is for the trainee to read before the call \
starts, so it must be in English regardless of the call language.

The call itself will happen in {language_name}, but "brief_en" must still be written in English."""

    response = client().messages.create(
        model=MODEL,
        max_tokens=500,
        output_config={"effort": "low"},
        messages=[{"role": "user", "content": prompt}],
    )
    text = _extract_text(response)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        data = json.loads(text[start:end + 1])
    return {
        "hotel_name": data["company_name"],
        "manager_name": data["contact_name"],
        "brief_en": data["brief_en"],
    }


def manager_reply(*, system_prompt, history):
    """history: list of {"role": "user"|"assistant", "text": str} in chronological order."""
    messages = [{"role": h["role"], "content": h["text"]} for h in history]
    response = client().messages.create(
        model=MODEL,
        max_tokens=600,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        output_config={"effort": "low"},
        messages=messages,
    )
    return _extract_text(response)


def translate_text(text, *, source_language):
    """Always translates into English — the one direction that generalizes across
    however many source languages a brand supports (not just an en<->es pair)."""
    source_name = _language_name(source_language)
    response = client().messages.create(
        model=TRANSLATE_MODEL,
        max_tokens=400,
        system=(
            f"Translate the given {source_name} sentence(s) into natural, conversational "
            "English. Reply with ONLY the translation, no notes, no quotation marks."
        ),
        messages=[{"role": "user", "content": text}],
    )
    return _extract_text(response)
