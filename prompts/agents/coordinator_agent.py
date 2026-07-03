# agents/coordinator_agent.py

from tools.pdf_reader import extract_text
from tools.ppt_reader import extract_ppt_text
from tools.docx_reader import extract_docx_text
from tools.pii_scrubber import scrub_pii


def get_document_text(file) -> str:
    """
    FIX: gr.File(type="filepath") passes a plain string path, NOT a file object.
    The old code called file.name which threw AttributeError on a string,
    causing silent failure and empty notes downstream.
    We now accept both a string path and a file-like object for safety.
    """
    # Resolve the path whether we got a string or a file object
    path = file if isinstance(file, str) else file.name

    if path.endswith(".pdf"):
        text = extract_text(path)
    elif path.endswith(".pptx"):
        text = extract_ppt_text(path)
    elif path.endswith(".docx"):
        text = extract_docx_text(path)
    else:
        raise ValueError(f"Unsupported file type: {path}")

    if not text or not text.strip():
        raise ValueError("Document appears to be empty or could not be read.")

    text = scrub_pii(text)
    return text
    