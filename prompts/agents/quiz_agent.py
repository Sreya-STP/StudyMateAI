import re
from agents.llm_provider import generate_text


def _force_qa_linebreaks(text: str) -> str:
    """
    Safety net: Forces a line break before any Answer marker, catching variations like:
    **A:**, **A1:**, **Answer:**, or even slightly misformatted bolding.
    """
    text = re.sub(r'(?<!\n)(\*\*(?:A\d*|Answer\d*).*?\*\*)', r'\n\n\1', text)
    return text


def _generate_essay_and_marks(notes: str, api_key: str) -> str:
    prompt = f"""You are an expert university exam coach.
Analyze the study notes below and create the FIRST HALF of an exam question bank.

CRITICAL FORMATTING RULES:
1. The question and its answer must ALWAYS be separated by a blank line. Never put Q and A on the same line.
2. Format every question as **Q1:** (or Q2, Q3) and every answer as **A1:** (or A2, A3).
3. Do NOT include any introduction, preamble, or motivational text. Go straight into the first heading.

Generate EXACTLY these three sections in this order, using these exact markdown headings:

# ❓ Top 5 Important Exam Questions
Generate 5 critical exam questions. For each question, the answer MUST be a FULL ESSAY. Write multiple thorough paragraphs covering definitions, explanations, examples, and limitations. Do not shorten these answers.

# 📄 5-Mark Questions & Answers
Generate 8 questions. The answer for each must be a concise 2-3 sentence paragraph.

# ✏️ 2-Mark Questions & Answers
Generate 10 questions. The answer for each must be exactly 1 sentence.

Study Notes:
{notes}
"""
    return generate_text(prompt, api_key=api_key, temperature=0.5, max_tokens=7000)


def _generate_mcq_and_viva(notes: str, api_key: str) -> str:
    prompt = f"""You are an expert university exam coach.
Analyze the study notes below and create the SECOND HALF of an exam question bank.

CRITICAL FORMATTING RULES:
1. The question and its answer must ALWAYS be separated by a blank line. Never put Q and A on the same line.
2. Format every question as **Q1:** (or Q2, Q3) and every answer as **A1:** (or A2, A3).
3. Do NOT include any introduction, preamble, or motivational text. Go straight into the first heading.

Generate EXACTLY these four sections in this order, using these exact markdown headings:

# 📊 Multiple Choice Questions — MCQs
Generate 10 multiple choice questions. Format exactly like this:
**Q1:** Question text?
A) option
B) option
C) option
D) option
**Correct Answer:** [Letter]

# 🎤 Viva Questions & Answers
Generate 5 viva questions. The answer for each must be exactly 1 sentence.

# 🔥 Frequently Asked Topics
Generate 5-8 short bullet points of key topics.

# 💡 Topics Most Likely to Appear in Exam
Generate 5-8 short bullet points of expected exam topics.

Study Notes:
{notes}
"""
    return generate_text(prompt, api_key=api_key, temperature=0.5, max_tokens=3500)


def generate_questions(notes: str, api_key: str = None) -> str:
    if not notes or not notes.strip():
        raise ValueError("Cannot generate questions: notes are empty.")

    part1 = _generate_essay_and_marks(notes, api_key)
    if not part1 or not part1.strip():
        raise ValueError("Quiz Agent returned empty (part 1). Check your API key and quota.")
    part1 = _force_qa_linebreaks(part1)

    part2 = _generate_mcq_and_viva(notes, api_key)
    if not part2 or not part2.strip():
        raise ValueError("Quiz Agent returned empty (part 2). Check your API key and quota.")
    part2 = _force_qa_linebreaks(part2)

    return part1.strip() + "\n\n---\n\n" + part2.strip()