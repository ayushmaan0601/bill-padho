"""
sarvam_helpers.py
-----------------
Three Sarvam API integrations used by Bill-Padho.

  1) extract_text_from_bill(image_path)         -> str    (Document Intelligence, job-based)
  2) explain_in_language(raw_text, language)    -> str    (Sarvam Chat - uses Bearer auth)
  3) text_to_speech(text, language)             -> bytes  (Bulbul v2 TTS)

Auth note: Sarvam's chat endpoint uses `Authorization: Bearer <key>`,
while the TTS endpoint uses `api-subscription-key`. Yes, this is inconsistent
in their API. Both are correct as of May 2026.
"""

import os
import base64
import zipfile
import tempfile
import requests
from sarvamai import SarvamAI

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
if not SARVAM_API_KEY:
    raise RuntimeError(
        "SARVAM_API_KEY is not set. Get one free at https://dashboard.sarvam.ai "
        "and add it to a .env file as SARVAM_API_KEY=your_key_here"
    )

# SDK client (used for Document Intelligence -- job-based async flow)
client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

BASE_URL = "https://api.sarvam.ai"

# Chat endpoint uses Bearer auth
CHAT_HEADERS = {
    "Authorization": f"Bearer {SARVAM_API_KEY}",
    "Content-Type": "application/json",
}

# TTS endpoint uses api-subscription-key
TTS_HEADERS = {
    "api-subscription-key": SARVAM_API_KEY,
    "Content-Type": "application/json",
}

# Friendly name -> BCP-47 language code.
LANGUAGES = {
    "Hindi":     "hi-IN",
    "Tamil":     "ta-IN",
    "Telugu":    "te-IN",
    "Bengali":   "bn-IN",
    "Marathi":   "mr-IN",
    "Gujarati":  "gu-IN",
    "Kannada":   "kn-IN",
    "Malayalam": "ml-IN",
    "Punjabi":   "pa-IN",
    "Odia":      "od-IN",
    "English":   "en-IN",
}


# --------------------------------------------------------------------------
# 1) Extract text from a bill image using Document Intelligence
# --------------------------------------------------------------------------
def extract_text_from_bill(image_path: str) -> str:
    """
    Runs a Document Intelligence job on the uploaded bill image.
    Takes ~30-60s end to end because the job is async.
    """
    job = client.document_intelligence.create_job(
        language="en-IN",
        output_format="md",
    )
    job.upload_file(image_path)
    job.start()
    job.wait_until_complete()

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
        zip_path = tmp_zip.name
    job.download_output(zip_path)

    markdown_text = _extract_markdown_from_zip(zip_path)

    try:
        os.unlink(zip_path)
    except Exception:
        pass

    return markdown_text


def _extract_markdown_from_zip(zip_path: str) -> str:
    """Pull the .md content out of the Document Intelligence output ZIP."""
    pieces = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            if name.endswith(".md"):
                with zf.open(name) as f:
                    pieces.append(f.read().decode("utf-8", errors="replace"))
    return "\n\n".join(pieces) if pieces else "(no text extracted)"


# --------------------------------------------------------------------------
# 2) Ask Sarvam to explain the bill in plain language
# --------------------------------------------------------------------------
def explain_in_language(raw_text: str, language: str = "Hindi") -> str:
    """Sends the extracted bill text to Sarvam-30b for a friendly explanation."""
    # Trim raw text to avoid context overflow on bills with huge tables
    if len(raw_text) > 6000:
        raw_text = raw_text[:6000] + "\n\n[...truncated for length...]"

    system_prompt = (
        f"You are a helpful assistant that explains bills to Indian users who "
        f"do not read English fluently. Reply ONLY in {language}. "
        f"Keep the tone warm, respectful, and very simple -- like you are "
        f"talking to a parent or grandparent. "
        f"Cover these four things, in this order, in short sentences: "
        f"1) What kind of bill this is and who it is from. "
        f"2) The total amount due, in rupees, spelled out clearly. "
        f"3) The due date, spelled out clearly. "
        f"4) Any one important note -- late fee, comparison to last month, "
        f"or anything that looks unusual. "
        f"Do NOT add disclaimers. Do NOT mention that you are an AI. "
        f"Do NOT translate the original bill word-for-word -- summarise it. "
        f"Do NOT use any markdown formatting like asterisks (*), bold, or bullet points. "
        f"Write in plain conversational sentences only. "
        f"Keep the response under 120 words so it can be spoken in under 45 seconds."
    )

    user_prompt = (
        f"Here is the extracted bill text:\n\n{raw_text}\n\n"
        f"Please explain it now in {language}."
    )

    payload = {
        "model": "sarvam-m",   # widely-supported chat model, stable on this endpoint
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 800,
        "reasoning_effort": "low",   # avoid long internal "thinking" chains
    }

    response = requests.post(
        f"{BASE_URL}/v1/chat/completions",
        headers=CHAT_HEADERS,
        json=payload,
        timeout=60,
    )

    # Surface a useful error if it fails
    if response.status_code != 200:
        raise RuntimeError(
            f"Chat API returned {response.status_code}: {response.text[:500]}"
        )

    raw_response = response.json()["choices"][0]["message"]["content"].strip()

    # Sarvam-M is a hybrid reasoning model and sometimes wraps its private
    # chain-of-thought in <think>...</think> tags before the final answer.
    # We strip that out so only the user-facing Hindi text remains.
    import re
    cleaned = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL).strip()

    # If for some reason the closing </think> is missing, drop everything before it
    if "</think>" in cleaned:
        cleaned = cleaned.split("</think>", 1)[1].strip()

    # Strip any residual markdown formatting (asterisks for bold, etc.)
    # so both the displayed text and the TTS audio are clean prose.
    cleaned = re.sub(r"\*+", "", cleaned)        # remove ** and *
    cleaned = re.sub(r"^[#>\-]\s*", "", cleaned, flags=re.MULTILINE)  # headings, quotes, bullets
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)  # collapse extra blank lines

    return cleaned.strip() if cleaned.strip() else raw_response


# --------------------------------------------------------------------------
# 3) Convert the explanation into spoken audio using Bulbul v2
# --------------------------------------------------------------------------
def text_to_speech(text: str, language: str = "Hindi") -> bytes:
    """Calls Sarvam's TTS endpoint and returns concatenated WAV bytes."""
    lang_code = LANGUAGES.get(language, "hi-IN")
    chunks = _split_for_tts(text, max_len=450)

    audio_bytes_concat = b""
    for chunk in chunks:
        payload = {
            "inputs": [chunk],
            "target_language_code": lang_code,
            "speaker": "anushka",
            "model": "bulbul:v2",
            "enable_preprocessing": True,
        }

        response = requests.post(
            f"{BASE_URL}/text-to-speech",
            headers=TTS_HEADERS,
            json=payload,
            timeout=60,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"TTS API returned {response.status_code}: {response.text[:500]}"
            )

        audio_b64 = response.json()["audios"][0]
        audio_bytes_concat += base64.b64decode(audio_b64)

    return audio_bytes_concat


# --------------------------------------------------------------------------
# Helper: split text on sentence boundaries for TTS chunking
# --------------------------------------------------------------------------
def _split_for_tts(text: str, max_len: int = 450) -> list:
    """Sentence-aware splitter so Bulbul doesn't choke on long input."""
    if len(text) <= max_len:
        return [text]

    import re
    sentences = re.split(r'(?<=[.!?।])\s+', text)

    chunks, current = [], ""
    for s in sentences:
        if len(current) + len(s) + 1 <= max_len:
            current = (current + " " + s).strip()
        else:
            if current:
                chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return chunks
