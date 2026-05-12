"""
app.py
------
Streamlit front-end for Bill-Padho.

Flow:
  1) User uploads a bill image
  2) User picks a language
  3) App calls Sarvam Vision  -> raw text
  4) App calls Sarvam Chat    -> friendly explanation in chosen language
  5) App calls Sarvam Bulbul  -> audio of explanation
  6) Audio plays inline, text shown below

Run locally:
    streamlit run app.py
"""

import os
import tempfile
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # pulls SARVAM_API_KEY from .env when running locally

from sarvam_helpers import (
    extract_text_from_bill,
    explain_in_language,
    text_to_speech,
    LANGUAGES,
)

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Bill-Padho | Hear your bills in your language",
    page_icon="🧾",
    layout="centered",
)

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.title("🧾 Bill-Padho")
st.caption(
    "Upload any bill -- electricity, water, phone, medical -- and hear it "
    "explained simply in your language. Built on Sarvam Vision + Sarvam-M + Bulbul."
)

st.divider()

# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader(
        "Upload a bill",
        type=["jpg", "jpeg", "png", "pdf"],
        help="A clear photo of any bill works best.",
    )

with col2:
    language = st.selectbox(
        "Explain in",
        options=list(LANGUAGES.keys()),
        index=0,  # Hindi default
    )

explain_button = st.button(
    "Explain this bill",
    type="primary",
    disabled=(uploaded_file is None),
    use_container_width=True,
)

# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------
if explain_button and uploaded_file is not None:

    # Save uploaded file to a temp path because the Sarvam SDK takes a path
    suffix = "." + uploaded_file.name.split(".")[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # Show the uploaded image as feedback (skip for PDFs)
    if suffix.lower() in {".jpg", ".jpeg", ".png"}:
        st.image(tmp_path, caption="Your bill", use_container_width=True)

    # ---- Step 1: extract ------------------------------------------------
    with st.status("Reading the bill with Sarvam Vision (takes ~30-60 seconds)...", expanded=False) as status:
        try:
            raw_text = extract_text_from_bill(tmp_path)
            status.update(label="✓ Bill read successfully", state="complete")
        except Exception as e:
            status.update(label=f"✗ Vision step failed: {e}", state="error")
            st.stop()

    with st.expander("See raw text extracted by Sarvam Vision"):
        st.code(raw_text, language="markdown")

    # ---- Step 2: explain ------------------------------------------------
    with st.status(f"Explaining in {language} with Sarvam-M...", expanded=False) as status:
        try:
            explanation = explain_in_language(raw_text, language=language)
            status.update(label=f"✓ Explanation ready in {language}", state="complete")
        except Exception as e:
            status.update(label=f"✗ LLM step failed: {e}", state="error")
            st.stop()

    st.subheader(f"Explanation ({language})")
    st.write(explanation)

    # ---- Step 3: TTS ----------------------------------------------------
    with st.status("Generating audio with Bulbul TTS...", expanded=False) as status:
        try:
            audio_bytes = text_to_speech(explanation, language=language)
            status.update(label="✓ Audio ready", state="complete")
        except Exception as e:
            status.update(label=f"✗ TTS step failed: {e}", state="error")
            st.stop()

    st.audio(audio_bytes, format="audio/wav")

    # Clean up temp file
    try:
        os.unlink(tmp_path)
    except Exception:
        pass

# --------------------------------------------------------------------------
# Footer / context
# --------------------------------------------------------------------------
st.divider()
with st.expander("About this project"):
    st.markdown(
        """
        **Bill-Padho** is a proof-of-concept demonstrating how Sarvam's API stack
        can be composed into a consumer-facing accessibility tool.

        - **Sarvam Vision** (Document Digitisation) extracts structured text from any bill, including Indic scripts.
        - **Sarvam-M** rewrites the extracted text as a short, simple explanation in the user's preferred language.
        - **Bulbul v2** (Text-to-Speech) converts the explanation into natural-sounding audio.

        Built as part of a PS-II application to Sarvam AI (May 2026).
        Source: [GitHub](https://github.com/your-username/bill-padho)
        """
    )
