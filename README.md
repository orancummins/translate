# Sales Call Trainer

A small web app for practicing Tripadvisor-style sales calls with hotel
managers. Claude plays a hotel manager persona and responds in character —
in English or Spanish (Spain, Mexico, Argentina, Colombia) — while you
practice pitching, handling objections, and asking questions, by voice or
by text. Conversations are saved so you can read the transcript back or
have it read aloud to you later.

## Features

- **Text or voice input**, in English or Spanish, using the browser's
  built-in speech recognition (works best in Chrome/Edge on desktop or
  Android; Safari/iOS support varies).
- **Claude plays the hotel manager** — a specific persona (skeptical
  veteran, data-driven analyst, overwhelmed owner-operator, corporate
  gatekeeper, eager newcomer, review-anxious manager) at a hotel type you
  choose (boutique, luxury resort, business/chain, budget motel, B&B,
  extended-stay), reacting specifically to what you say and occasionally
  asking you questions back, just like a real call.
- **Spanish country locales** — Spain, Mexico, Argentina, Colombia — pick
  the accent/voice used for speech recognition and text-to-speech, and the
  country the invented hotel/manager is set in.
- **Saved conversations** — every call is stored (SQLite) and available
  under "History": read the transcript, replay any single line or the
  whole call out loud, and optionally see an on-demand translation of any
  line.
- **Difficulty levels** — friendly / neutral / tough — controls how easily
  the manager persona is persuaded and how many objections they raise.

## How voice works

The Claude API doesn't do speech synthesis or recognition itself, so this
app uses the **browser's native Web Speech API** for both:

- **Speech-to-text** (`SpeechRecognition`) captures your spoken line and
  sends the transcribed text to Claude.
- **Text-to-speech** (`speechSynthesis`) reads the manager's reply back to
  you, in a voice matching the chosen locale, and is also used to replay
  saved conversations.

This keeps the app free of extra API keys/costs for voice and works
offline-ish on most phones, but voice quality and language coverage depend
on the voices installed on the device/browser, and `SpeechRecognition`
needs a secure context (HTTPS, or `localhost` during development).

Claude is used for the actual intelligence: playing the manager persona,
inventing each scenario (hotel name, manager name, situation), and
on-demand translation of any line between English and Spanish.

## Setup

```bash
pip install -r requirements.txt

# Auth: either export a key, or use `ant auth login` (see the Anthropic CLI)
export ANTHROPIC_API_KEY=sk-ant-...

python app.py
```

Then open `http://localhost:5000` (or `http://<your-machine-ip>:5000` from
your phone on the same network — but see the HTTPS note above for voice
input away from `localhost`).

### Configuration

| Env var | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Anthropic API credentials |
| `CLAUDE_MODEL` | `claude-opus-5` | Model used for the manager roleplay & scenario generation |
| `CLAUDE_TRANSLATE_MODEL` | `claude-haiku-4-5` | Cheaper/faster model used only for the optional line translations |
| `PORT` | `5000` | Port Flask listens on |

## Deploying for "on the go" use

To use voice features from your phone away from your home network, deploy
behind HTTPS (e.g. behind a reverse proxy with a TLS certificate, or a
platform that provides one) — `SpeechRecognition` requires a secure
context in most browsers. Text mode works anywhere.

## Project layout

```
app.py            Flask routes
claude_client.py  Anthropic API calls (scenario generation, manager replies, translation)
personas.py       Hotel types, manager personas, locales, difficulty levels
db.py             SQLite persistence for sessions/messages
templates/         index.html — single-page app shell
static/css/        styling
static/js/         app logic, Web Speech API integration
data/               SQLite database file (gitignored)
```
