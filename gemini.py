"""
Helena — Gemini API Wrapper
Uses the new google-genai SDK.
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

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


def get_reply(history: list, new_message: str) -> str:
    contents = list(history)
    contents.append({
        "role": "user",
        "parts": [{"text": new_message}],
    })

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=1.8,
                max_output_tokens=512,
            ),
        )
        return response.text
    except Exception as exc:
        print(f"[Helena] Gemini API error: {exc}")
        return (
            "Even my server is embarrassed to deal with you right now. "
            "Something broke on my end. Try again, I guess."
        )