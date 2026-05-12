# 🧾 Swar-Patra

> *Photograph any bill. Hear it explained in your language.*

A proof-of-concept built on the **Sarvam AI** API stack that lets non-English-reading Indians understand their utility, medical, and phone bills through voice — in 10+ Indian languages.

---

## Why this exists

India has ~70% of its population that does not read English fluently, yet bills, prescriptions, and government notices arrive in English by default. Sarvam has already built the pickaxes for this problem — Sarvam Vision for document understanding, Sarvam-M for reasoning, Bulbul for speech. Bill-Padho is what happens when you compose them into a single consumer-facing flow.



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

## Built with

- [Sarvam Vision / Document Digitisation API](https://www.sarvam.ai/apis/document-digitisation)
- [Sarvam-M Chat Completions](https://docs.sarvam.ai/api-reference-docs/introduction)
- [Bulbul v2 Text-to-Speech](https://docs.sarvam.ai/api-reference-docs/introduction)
- [Streamlit](https://streamlit.io/)

