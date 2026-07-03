# agents/key_manager.py

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
DEMO_API_KEY = os.getenv("GEMINI_API_KEY")


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """
    Tests a Gemini API key with a minimal, cheap request.
    Returns (is_valid, message).
    """
    if not api_key or not api_key.strip():
        return False, "No key provided."

    try:
        client = genai.Client(api_key=api_key.strip())
        # Minimal test call — tiny token cost
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Reply with just the word: OK",
        )
        if response.text:
            return True, "Key is valid."
        return False, "Key did not return a response."
    except Exception as e:
        err = str(e).lower()
        if "api key not valid" in err or "invalid" in err:
            return False, "This API key is invalid."
        if "permission" in err:
            return False, "This key does not have permission to use Gemini."
        if "quota" in err or "resource_exhausted" in err:
            # Key is technically valid but out of quota
            return True, "Key is valid (quota may be limited)."
        return False, f"Could not validate key: {str(e)}"


def has_demo_key() -> bool:
    return bool(DEMO_API_KEY and DEMO_API_KEY.strip())
