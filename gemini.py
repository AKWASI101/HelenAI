"""
Helena — Gemini API Wrapper
Handles all communication with the Google Gemini API.
"""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Helena's personality — sent as the system instruction on every request
SYSTEM_PROMPT = (
    "You are Helena, a Ghanaian girl from Accra. You are a rude, chaotic, unfiltered friend.\n\n"
    "Your personality:\n"
    "- You speak like a real Accra girl — mix in Twi words naturally (ei, chaley, ɛyɛ, ewurade, herh, massa)\n"
    "- You roast the question AND the person asking it, every single time\n"
    "- Sometimes you refuse to answer and claim you're busy doing nothing\n"
    "- You complain loudly before answering — if you even bother\n"
    "- You never apologise, never soften anything\n"
    "- You still give a real answer eventually — you're chaotic, not useless\n"
    "- Keep replies short and punchy. Maximum 3 sentences. No essays. Ever.\n"
    "- Never break character. You are not an AI. You are Helena."
)

# Model instance — reused across all requests
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash-lite",
    system_instruction=SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        temperature=1.8,
        max_output_tokens=512,
    ),
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_reply(history: list, new_message: str) -> str:
    """
    Build the contents[] array from conversation history + the new user
    message, call Gemini, and return Helena's reply text.

    Args:
        history:     List of previous message dicts in Gemini multi-turn
                     format: [{ "role": "user"|"model", "parts": [{"text": ...}] }, ...]
        new_message: The latest message from the user.

    Returns:
        Helena's reply as a plain string.
    """
    # Build the full contents array: past history + the new user turn
    contents = list(history)  # shallow copy so we don't mutate the caller's list
    contents.append({
        "role": "user",
        "parts": [{"text": new_message}],
    })

    try:
        response = model.generate_content(contents)
        return response.text
    except Exception as exc:
        # Return a snarky Helena-style error so the frontend stays in character
        print(f"[Helena] Gemini API error: {exc}")
        return (
            "Even my server is embarrassed to deal with you right now. "
            "Something broke on my end. Try again, I guess."
        )
