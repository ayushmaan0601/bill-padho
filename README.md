# 🧾 Bill-Padho

> *Photograph any bill. Hear it explained in your language.*

A proof-of-concept built on the **Sarvam AI** API stack that lets non-English-reading Indians understand their utility, medical, and phone bills through voice — in 10+ Indian languages.

---

## Why this exists

India has ~70% of its population that does not read English fluently, yet bills, prescriptions, and government notices arrive in English by default. Sarvam has already built the pickaxes for this problem — Sarvam Vision for document understanding, Sarvam-M for reasoning, Bulbul for speech. Bill-Padho is what happens when you compose them into a single consumer-facing flow.

It is not a product. It is a 150-line proof of concept of what an FDSE at Sarvam would prototype on day one for a public-utility client.

---

## How it works

```
       ┌──────────────────┐
       │  Photo of bill   │
       │  (jpg/png/pdf)   │
       └────────┬─────────┘
                │
                ▼
       ┌──────────────────┐         Step 1: OCR
       │  Sarvam Vision   │  ── extracts text + layout
       │  (Doc. Digitis.) │     across 22 Indian scripts
       └────────┬─────────┘
                │
                ▼  raw markdown text
       ┌──────────────────┐         Step 2: Reasoning
       │     Sarvam-M     │  ── summarises into 4 simple
       │  (chat / LLM)    │     sentences in target language
       └────────┬─────────┘
                │
                ▼  natural-language explanation
       ┌──────────────────┐         Step 3: Voice
       │  Bulbul v2 TTS   │  ── speaker "anushka"
       │                  │     10 Indic voices supported
       └────────┬─────────┘
                │
                ▼
        🔊  audio output
```

Three API calls. No intermediate ML models, no orchestration framework, no database. The design is deliberately minimal — the point is to demonstrate that Sarvam's stack is *already enough* to ship this without a frontier model dependency.

---

## Quickstart (local)

```bash
git clone https://github.com/<your-username>/bill-padho.git
cd bill-padho

# Set up environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Add your Sarvam API key
cp .env.example .env
# edit .env and paste your key from https://dashboard.sarvam.ai

# Run
streamlit run app.py
```

The app opens at `http://localhost:8501`. Drop in any bill, pick a language, hit "Explain".

---

## Live demo

Try it at: **[bill-padho.hf.space](https://huggingface.co/spaces/your-username/bill-padho)**

---

## Project structure

```
bill-padho/
├── app.py                # Streamlit UI + flow control
├── sarvam_helpers.py     # 3 functions, one per Sarvam API
├── requirements.txt
├── .env.example
└── README.md
```

Everything that talks to Sarvam lives in **one file** (`sarvam_helpers.py`) so the API surface is auditable in 5 minutes.

---

## Design choices worth defending

| Choice | Why |
| --- | --- |
| Used the official `sarvam-ai` Python SDK over raw HTTP | Cleaner retries, typed responses, lower surface area for bugs |
| Markdown output from Sarvam Vision (not JSON) | Bills are tables-and-prose hybrids; Markdown preserves both for the LLM |
| `temperature=0.3` on the LLM call | Factual summarisation, not creative writing |
| Naive sentence-aware chunking before TTS | Bulbul caps at ~500 chars/call; chunking on `.|!|?|।` preserves prosody |
| One speaker (`anushka`) across languages | A/B'd against `meera`; `anushka` had cleaner Indic prosody on bill-style numerals |
| No caching layer | Intentional. Every PoC choice here is "what's the minimum that ships." |

---

## What this is *not*

- Not a replacement for **Sarvam Akshar** (enterprise document digitisation batch product) — Akshar is for B2B pipelines; this is a single-bill consumer flow on top of Vision
- Not production-ready — no auth, no rate-limit handling, no PII redaction (bills contain account numbers)
- Not a multi-turn agent — one-shot pipeline by design

## What I'd build next (if this were real)

1. **PII redaction layer** before LLM/TTS — account numbers and addresses should never leave the device unredacted
2. **WhatsApp Business API integration** — most target users will not install another app
3. **Voice query mode** — *"jab bharna hai?"* → re-extract just the due date from the cached bill
4. **Bill-history view** — track month-over-month for the same utility/phone number
5. **On-device fallback via Sarvam Edge** — offline OCR + TTS for low-connectivity regions

---

## Built with

- [Sarvam Vision / Document Digitisation API](https://www.sarvam.ai/apis/document-digitisation)
- [Sarvam-M Chat Completions](https://docs.sarvam.ai/api-reference-docs/introduction)
- [Bulbul v2 Text-to-Speech](https://docs.sarvam.ai/api-reference-docs/introduction)
- [Streamlit](https://streamlit.io/)

---

## Acknowledgement

Built for the BITS Pilani PS-II application to **Sarvam AI** (May 2026). Not affiliated with Sarvam AI.
