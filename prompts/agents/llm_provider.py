# agents/llm_provider.py
"""
Unified LLM calling layer with automatic retry + backoff on rate limits.

Why this exists:
StudyMate fires 2 Gemini calls in parallel (Notes + Planner), then a 3rd
(Questions) right after. Gemini's free tier enforces a requests-per-minute
(RPM) limit, not just a daily cap — so the 3rd call can get rate-limited
even though you haven't used your full daily quota. The fix is to retry
with increasing wait times instead of failing immediately.

Usage in any agent file:
    from agents.llm_provider import generate_text
    result = generate_text(prompt, api_key=user_gemini_key, temperature=0.4, max_tokens=8192)
"""

import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DEMO_GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Retry configuration
MAX_RETRIES     = 4          # total attempts = 1 original + 3 retries
INITIAL_WAIT    = 8           # seconds before first retry
BACKOFF_FACTOR  = 2           # wait doubles each retry: 8s, 16s, 32s


def _is_rate_limit_error(error_msg: str) -> bool:
    """Detect rate-limit / quota errors that are worth retrying."""
    err = error_msg.lower()
    return any(term in err for term in [
        "quota", "resource_exhausted", "rate limit", "429",
        "too many requests", "rate_limit_exceeded",
    ])


def _is_invalid_key_error(error_msg: str) -> bool:
    err = error_msg.lower()
    return any(term in err for term in ["api key not valid", "invalid api key", "permission denied"])


def _call_gemini(prompt: str, api_key: str, temperature: float, max_tokens: int) -> str:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        ),
    )
    return response.text if response.text else ""


def generate_text(
    prompt: str,
    api_key: str = None,
    temperature: float = 0.4,
    max_tokens: int = 8192,
    on_retry=None,
) -> str:
    """
    Generates text using Gemini, automatically retrying with exponential
    backoff if the request is rate-limited.

    api_key:  the user's own Gemini key, or None to use the project's
              demo key from .env.
    on_retry: optional callback(attempt, wait_seconds) — lets the UI show
              a "retrying in Xs..." message instead of just hanging.

    Raises ValueError with a clear message if all retries are exhausted
    or the key itself is invalid (no point retrying that).
    """
    key_to_use = api_key.strip() if api_key and api_key.strip() else DEMO_GEMINI_KEY
    if not key_to_use:
        raise ValueError(
            "No Gemini API key available. Paste your own key in the sidebar, "
            "or the project's demo key is missing from .env."
        )

    last_error = None
    wait_time  = INITIAL_WAIT

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = _call_gemini(prompt, key_to_use, temperature, max_tokens)
            if result and result.strip():
                return result
            last_error = "Gemini returned an empty response."
            # Empty responses are usually a content-filter issue, not worth
            # retrying with the same prompt — fail fast.
            break

        except Exception as e:
            err_str = str(e)
            last_error = err_str

            # Invalid key — retrying won't help, fail immediately.
            if _is_invalid_key_error(err_str):
                raise ValueError("INVALID_API_KEY")

            # Rate limit — worth retrying with backoff.
            if _is_rate_limit_error(err_str) and attempt < MAX_RETRIES:
                if on_retry:
                    on_retry(attempt, wait_time)
                time.sleep(wait_time)
                wait_time *= BACKOFF_FACTOR
                continue

            # Any other error, or rate limit on the final attempt — stop.
            break

    # All retries exhausted
    if last_error and _is_rate_limit_error(last_error):
        raise ValueError(
            "Gemini rate limit hit even after retrying. This usually clears "
            "within a minute — please wait briefly and try again, or use "
            "your own Gemini API key in the sidebar for a separate quota."
        )

    raise ValueError(last_error or "Unknown error calling Gemini.")
