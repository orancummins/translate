"""Static data for hotel types, manager personas, locales, and difficulty
levels used to build the roleplay scenarios and Claude system prompts."""

LOCALES = [
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
        "id": "es-MX",
        "language": "es",
        "label": "Español (México)",
        "flag": "\U0001F1F2\U0001F1FD",
        "speech_lang": "es-MX",
        "countries": ["Mexico"],
    },
    {
        "id": "es-AR",
        "language": "es",
        "label": "Español (Argentina)",
        "flag": "\U0001F1E6\U0001F1F7",
        "speech_lang": "es-AR",
        "countries": ["Argentina"],
    },
    {
        "id": "es-CO",
        "language": "es",
        "label": "Español (Colombia)",
        "flag": "\U0001F1E8\U0001F1F4",
        "speech_lang": "es-CO",
        "countries": ["Colombia"],
    },
]

HOTEL_TYPES = [
    {
        "id": "boutique",
        "label": "Boutique Hotel",
        "description": "Independent, 20-40 rooms, design-forward, city center.",
        "context": "a small independently-owned boutique hotel with around 30 rooms",
    },
    {
        "id": "luxury_resort",
        "label": "Luxury Resort",
        "description": "5-star beach or mountain resort with a big marketing budget.",
        "context": "a 5-star luxury resort with extensive amenities (spa, multiple restaurants, golf or beachfront)",
    },
    {
        "id": "business_chain",
        "label": "Business / Chain Hotel",
        "description": "Mid-scale chain-affiliated property near an airport or convention center.",
        "context": "a mid-scale, chain-affiliated business hotel near an airport or convention center",
    },
    {
        "id": "budget_motel",
        "label": "Budget Motel",
        "description": "Roadside, price-sensitive, thin margins.",
        "context": "a small independent, price-sensitive roadside motel with thin margins",
    },
    {
        "id": "bed_breakfast",
        "label": "Bed & Breakfast",
        "description": "Family-run, very small, very personal.",
        "context": "a very small, family-run bed & breakfast with fewer than 10 rooms",
    },
    {
        "id": "extended_stay",
        "label": "Extended-Stay Apartments",
        "description": "Apart-hotel aimed at long-stay business and relocation guests.",
        "context": "an extended-stay apart-hotel aimed at long-stay business travelers and relocations",
    },
]

MANAGER_PERSONAS = [
    {
        "id": "skeptical_veteran",
        "label": "The Skeptical Veteran",
        "description": "Been burned by OTAs before. Distrustful of 'yet another platform'.",
        "traits": (
            "You have run hotels for over 20 years and have been disappointed by online "
            "travel agencies before. You are guarded, a little cynical, and quick to bring "
            "up bad past experiences with commissions, fine print, or fake reviews. You need "
            "to be convinced with concrete facts, not marketing language."
        ),
    },
    {
        "id": "data_driven",
        "label": "The Data-Driven Analyst",
        "description": "Wants ROI numbers, commission percentages, and hard comparisons.",
        "traits": (
            "You are analytical and numbers-oriented. You constantly ask for statistics, "
            "commission percentages, conversion rates, and comparisons against Booking.com, "
            "Expedia, and Google Hotel Ads. Vague answers frustrate you; you push for specifics."
        ),
    },
    {
        "id": "overwhelmed_owner",
        "label": "The Overwhelmed Owner-Operator",
        "description": "Wears every hat at the property and has almost no time to talk.",
        "traits": (
            "You personally run nearly every part of the property and are constantly "
            "interrupted by staff or guests during the call. You are friendly but impatient, "
            "and you want the value proposition explained in one or two sentences, fast."
        ),
    },
    {
        "id": "corporate_gatekeeper",
        "label": "The Corporate Gatekeeper",
        "description": "Regional manager bound by brand standards and procurement rules.",
        "traits": (
            "You are a regional manager for a hotel brand and anything involving spend or "
            "contracts must go through corporate procurement and brand compliance. You are "
            "polite but bureaucratic, frequently mention needing sign-off, and ask about "
            "brand-standard integrations, data privacy, and legal terms."
        ),
    },
    {
        "id": "eager_newcomer",
        "label": "The Eager Newcomer",
        "description": "New property hungry for visibility but watching every dollar.",
        "traits": (
            "Your property opened recently and you are hungry for visibility and bookings, "
            "so you are warm and receptive. However your budget is very tight, so cost and "
            "predictable ROI matter a lot to you."
        ),
    },
    {
        "id": "review_anxious",
        "label": "The Review-Anxious Manager",
        "description": "Worried about reputation, negative reviews, and how to respond to them.",
        "traits": (
            "You are anxious about your online reputation. You bring up specific negative "
            "reviews you have received, worry about how new platforms handle disputes over "
            "reviews, and want reassurance about reputation management tools and support."
        ),
    },
]

DIFFICULTIES = [
    {
        "id": "friendly",
        "label": "Friendly",
        "instruction": (
            "Be warm, open, and relatively easy to persuade. Raise only mild objections "
            "and concede reasonable points quickly."
        ),
    },
    {
        "id": "neutral",
        "label": "Neutral",
        "instruction": (
            "Be professionally neutral. Raise realistic objections and ask clarifying "
            "questions before being persuaded, but do not be hostile."
        ),
    },
    {
        "id": "tough",
        "label": "Tough",
        "instruction": (
            "Be skeptical and push back hard. Raise multiple objections, interrupt with "
            "pointed questions, and only move toward agreement if the rep genuinely earns it "
            "with strong, specific, relevant arguments."
        ),
    },
]


def _index_by_id(items):
    return {item["id"]: item for item in items}


LOCALE_BY_ID = _index_by_id(LOCALES)
HOTEL_TYPE_BY_ID = _index_by_id(HOTEL_TYPES)
MANAGER_PERSONA_BY_ID = _index_by_id(MANAGER_PERSONAS)
DIFFICULTY_BY_ID = _index_by_id(DIFFICULTIES)


def options_payload():
    """JSON-serializable option lists for the setup screen."""
    return {
        "locales": LOCALES,
        "hotel_types": HOTEL_TYPES,
        "personas": MANAGER_PERSONAS,
        "difficulties": DIFFICULTIES,
    }
