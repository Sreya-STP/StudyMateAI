
# tools/pii_scrubber.py
import re


def scrub_pii(text: str) -> str:
    """
    Remove genuine PII from document text before passing to AI agents.

    FIX: The old student-ID regex  r'\b[A-Za-z]{2,}\d{3,}\b'  was far too
    broad — it matched technical terms like Figure1234, IPv4, HTTP200, NaCl3,
    RAM256, Module101, etc., wiping out large portions of study material and
    causing the 'document appears empty' error.

    The new regex only matches patterns that look like real student/roll IDs:
      • Uppercase-only prefix of 2–4 letters + 6–12 digits  e.g. CS220456789
      • Or a common university roll-number format             e.g. 20CS1A0512
    Lowercase-heavy words (normal English / technical terms) are left alone.
    """

    # Email addresses
    text = re.sub(r'\b[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}\b', '[EMAIL]', text)

    # Phone numbers — 10-digit standalone numbers
    text = re.sub(r'(?<!\d)\d{10}(?!\d)', '[PHONE]', text)

    # Student / Roll IDs — STRICT pattern only:
    #   Option A: 2-4 uppercase letters immediately followed by 6-12 digits
    #             e.g. CS220456789, EE123456
    #   Option B: digits + 2-4 uppercase letters + digits (roll number style)
    #             e.g. 20CS1A0512, 21EC3B0045
    text = re.sub(r'\b[A-Z]{2,4}\d{6,12}\b', '[STUDENT_ID]', text)
    text = re.sub(r'\b\d{2}[A-Z]{2,4}\d[A-Z]\d{4}\b', '[STUDENT_ID]', text)

    return text