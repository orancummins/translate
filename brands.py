"""Brand packs: lets the same app run as either a Tripadvisor hotel-sales
demo or an OysterHR global-employment-sales demo. Select with the BRAND
env var (BRAND=tripadvisor, the default, or BRAND=oyster)."""

import os

from personas import DIFFICULTIES, HOTEL_TYPES, LOCALES, MANAGER_PERSONAS

LANGUAGE_NAMES = {"en": "English", "es": "Spanish", "fr": "French", "de": "German"}


def _index_by_id(items):
    return {item["id"]: item for item in items}


# ---------------------------------------------------------------- Tripadvisor

_TRIPADVISOR_PERSONAS = [{**p, "title": "general manager"} for p in MANAGER_PERSONAS]

TRIPADVISOR = {
    "id": "tripadvisor",
    "app_subtitle": "Hotel manager roleplay practice",
    "setup_lede": "Pick a scenario. Claude will play the hotel manager and stay in character for the whole call.",
    "company_type_field_label": "Type of hotel",
    "persona_field_label": "Manager persona",
    "key_modal_role": "hotel manager",
    "logo_icon": "tripadvisor-icon.png",
    "logo_wordmark": "tripadvisor-wordmark-white.png",
    "monogram": "TA",
    "colors": {"accent": "#34e0a1", "accent_2": "#7cf0c4", "accent_dark": "#189969", "accent_ink": "#06251a"},
    "theme_color": "#0e2a24",
    "seller_role": "Tripadvisor partnerships sales representative",
    "product_pitch": "listing tools, advertising, or Tripadvisor Business Advantage products for your property",
    "objection_domains": "commission rates, contract length, review handling, how it compares to Booking.com/Expedia, or support",
    "detail_domain": "property-appropriate details (occupancy, average daily rate concerns, staffing, past OTA experiences)",
    "company_noun": "hotel",
    "scenario_prompt_label": "a Tripadvisor sales training app",
    "company_types": HOTEL_TYPES,
    "personas": _TRIPADVISOR_PERSONAS,
    "locales": LOCALES,
    "js_copy": {
        "counterpart_label": "manager",
        "counterpart_title": "Manager:",
        "mic_wait_tooltip": "Wait for the manager to finish talking",
        "mic_wait_toast": "Wait for the manager to finish talking before you respond.",
    },
}

# --------------------------------------------------------------------- Oyster

OYSTER_COMPANY_TYPES = [
    {
        "id": "series_b_tech",
        "label": "Series B Tech Scale-up",
        "description": "Venture-backed software company hiring internationally for the first time.",
        "context": "a 140-160 person, venture-backed Series B software company expanding into new international hiring markets",
    },
    {
        "id": "pe_backed_enterprise",
        "label": "PE-Backed Enterprise",
        "description": "Large private-equity-backed company consolidating headcount across several EORs.",
        "context": "a large, private-equity-backed enterprise consolidating global headcount currently split across several EOR vendors",
    },
    {
        "id": "us_smb_contractors",
        "label": "US SMB Converting Contractors",
        "description": "US small business moving long-standing international contractors onto compliant EOR employment.",
        "context": "a US small-to-mid-size business converting several long-standing international contractors onto compliant EOR employment",
    },
    {
        "id": "mission_ngo",
        "label": "Mission-Aligned NGO",
        "description": "Non-profit hiring program staff across multiple countries on grant-funded budgets.",
        "context": "a mission-driven non-profit hiring program staff across multiple countries on tight, grant-funded budgets",
    },
    {
        "id": "series_a_first_hire",
        "label": "Series A Startup, First International Hire",
        "description": "Early-stage startup making its very first hire outside its home country.",
        "context": "an early-stage, Series A startup making its very first hire outside its home country",
    },
    {
        "id": "public_company_expansion",
        "label": "Public Company Expanding Globally",
        "description": "Publicly traded company entering new international markets under board and audit scrutiny.",
        "context": "a publicly traded company entering new international markets under close board and audit scrutiny",
    },
]

OYSTER_BUYER_PERSONAS = [
    {
        "id": "deel_defector",
        "label": "The Deel Defector",
        "title": "VP of People",
        "description": "Loyal to their current EOR vendor; skeptical of 'yet another platform'.",
        "traits": (
            "You already use a competitor EOR (Deel, Remote, or Rippling) and are reasonably "
            "satisfied with it. You are guarded and a little tired of vendor pitches, and you "
            "need a concrete, specific reason to even consider the cost and effort of switching, "
            "not generic platform-differentiation language."
        ),
    },
    {
        "id": "compliance_anxious_counsel",
        "label": "The Compliance-Anxious Counsel",
        "title": "General Counsel",
        "description": "Fixated on misclassification risk and labor-law exposure.",
        "traits": (
            "You are a General Counsel who has read (or heard secondhand about) a scary "
            "misclassification or labor-law enforcement case. You probe hard on how employees "
            "are classified, who bears legal liability, and what happens in a dispute. Vague "
            "reassurance frustrates you; you want specifics about how risk is actually managed."
        ),
    },
    {
        "id": "fx_burned_cfo",
        "label": "The FX-Burned CFO",
        "title": "CFO",
        "description": "Got hit with hidden FX markups before; hyper-focused on pricing transparency.",
        "traits": (
            "You are a CFO who was previously surprised by hidden foreign-exchange markups and "
            "opaque fees from a prior vendor. You push hard on exact, all-in pricing, ask for "
            "worked examples in specific currencies, and are suspicious of any answer that isn't "
            "a precise number."
        ),
    },
    {
        "id": "time_poor_vp_people",
        "label": "The Time-Poor VP People",
        "title": "VP of People",
        "description": "Extremely short on time; wants fast, concrete answers.",
        "traits": (
            "You are a VP of People with maybe five minutes for this call and frequent "
            "interruptions from your own team. You are friendly but impatient, and you want the "
            "value proposition explained in one or two sentences, fast, with no fluff."
        ),
    },
    {
        "id": "renewal_skeptic",
        "label": "The Renewal Skeptic",
        "title": "Director of HR Operations",
        "description": "Existing customer who had one bad experience and needs reassurance before renewing or expanding.",
        "traits": (
            "You are an existing customer who had one genuinely bad experience (for example, a "
            "termination in another country that went sideways and cost weeks of delay). You are "
            "willing to keep working together, but you bring up that specific incident, and you "
            "want concrete evidence that it won't happen again before renewing or expanding."
        ),
    },
    {
        "id": "eager_expansion_lead",
        "label": "The Eager Expansion Lead",
        "title": "Head of People",
        "description": "Excited about going global for the first time, but nervous about doing it right.",
        "traits": (
            "Your company is hiring internationally for the first time and you are genuinely "
            "excited about it, so you are warm and receptive. However you are nervous about "
            "getting compliance wrong on your first try, so you ask a lot of basic but earnest "
            "questions and want reassurance as much as features."
        ),
    },
]

OYSTER_LOCALES = [
    {
        "id": "en-US",
        "language": "en",
        "label": "English (United States)",
        "flag": "\U0001F1FA\U0001F1F8",
        "speech_lang": "en-US",
        "countries": ["the United States"],
    },
    {
        "id": "es-ES",
        "language": "es",
        "label": "Español (España)",
        "flag": "\U0001F1EA\U0001F1F8",
        "speech_lang": "es-ES",
        "countries": ["Spain"],
    },
    {
        "id": "fr-FR",
        "language": "fr",
        "label": "Français (France)",
        "flag": "\U0001F1EB\U0001F1F7",
        "speech_lang": "fr-FR",
        "countries": ["France"],
    },
    {
        "id": "de-DE",
        "language": "de",
        "label": "Deutsch (Deutschland)",
        "flag": "\U0001F1E9\U0001F1EA",
        "speech_lang": "de-DE",
        "countries": ["Germany"],
    },
]

OYSTER = {
    "id": "oyster",
    "app_subtitle": "Global employment buyer roleplay practice",
    "setup_lede": "Pick a scenario. Claude will play the HR, Finance, or Legal buyer and stay in character for the whole call.",
    "company_type_field_label": "Company type",
    "persona_field_label": "Buyer persona",
    "key_modal_role": "global employment buyer",
    "logo_icon": None,
    "logo_wordmark": None,
    "monogram": "OY",
    "colors": {"accent": "#00A699", "accent_2": "#4fe0d3", "accent_dark": "#00786d", "accent_ink": "#1a1a1a"},
    "theme_color": "#0d1f1c",
    "seller_role": "Oyster global employment sales representative",
    "product_pitch": "Oyster's global employment (EOR) platform",
    "objection_domains": "misclassification risk, hidden FX markups, contract terms, or why switch from Deel, Remote, or Rippling",
    "detail_domain": "buyer-appropriate details (headcount growth plans, current EOR vendor pain points, budget cycles, prior compliance incidents)",
    "company_noun": "company",
    "scenario_prompt_label": "an Oyster global employment sales training app",
    "company_types": OYSTER_COMPANY_TYPES,
    "personas": OYSTER_BUYER_PERSONAS,
    "locales": OYSTER_LOCALES,
    "js_copy": {
        "counterpart_label": "buyer",
        "counterpart_title": "Buyer:",
        "mic_wait_tooltip": "Wait for the buyer to finish talking",
        "mic_wait_toast": "Wait for the buyer to finish talking before you respond.",
    },
}

BRANDS = {"tripadvisor": TRIPADVISOR, "oyster": OYSTER}


def get_brand():
    brand_id = os.environ.get("BRAND", "tripadvisor").strip().lower()
    brand = dict(BRANDS.get(brand_id, TRIPADVISOR))
    brand["company_type_by_id"] = _index_by_id(brand["company_types"])
    brand["persona_by_id"] = _index_by_id(brand["personas"])
    brand["locale_by_id"] = _index_by_id(brand["locales"])
    return brand


def options_payload(brand):
    """JSON-serializable option lists for the setup screen, plus the brand's UI copy."""
    return {
        "locales": brand["locales"],
        "hotel_types": brand["company_types"],
        "personas": brand["personas"],
        "difficulties": DIFFICULTIES,
        "brand": {"id": brand["id"], **brand["js_copy"]},
    }
