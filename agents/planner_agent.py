# agents/planner_agent.py

from datetime import date, datetime
from agents.llm_provider import generate_text


def generate_study_plan(text: str, exam_date: str, hours_per_day: float, api_key: str = None) -> str:
    if not text or not text.strip():
        raise ValueError("Cannot generate study plan: document text is empty.")

    today = date.today()

    days_remaining = 30
    exam_date_display = "Not specified"
    if exam_date:
        try:
            exam_d = datetime.strptime(exam_date, "%Y-%m-%d").date()
            days_remaining = max(1, (exam_d - today).days)
            exam_date_display = exam_date
        except Exception:
            pass

    if days_remaining <= 10:
        granularity = "one row per DAY"
        max_rows = min(days_remaining, 12)
    elif days_remaining <= 30:
        granularity = "one row per 2-3 day block"
        max_rows = 12
    else:
        granularity = "one row per WEEK"
        max_rows = 12

    # FIX: Use a real, descriptive label for the "Period" column instead of
    # a meaningless row number (1, 2, 3...). Also switched from <br>- to
    # standard markdown line breaks (two trailing spaces + newline is not
    # reliable in tables, so instead we use a semicolon-separated list with
    # explicit "•" bullets typed directly — this renders correctly in BOTH
    # the on-screen gr.Markdown preview AND gets parsed correctly by the
    # DOCX table exporter, since python-docx receives the same raw text).
    prompt = f"""You are an expert study planner for university students.

Today's Date: {today}
Exam Date: {exam_date_display}
Exact Days Remaining Until Exam: {days_remaining} days
Available Study Hours Per Day: {hours_per_day}

Study Material:
{text}

Create a precise, structured exam-oriented study timetable covering ALL
{days_remaining} days between today and the exam date. Do not stop early —
the table must span the entire {days_remaining}-day period.

Rules:
1. Use this granularity: {granularity}.
2. The table must have around {max_rows} rows (or fewer), grouping multiple
   days/weeks per row as needed to stay within this limit while still
   covering the full {days_remaining}-day span.
3. You MUST format the table header exactly like this, including the separator line:
| Period | Date Range | Topics | Hours/Day |
|---|---|---|---|
4. The "Period" column must be a DESCRIPTIVE label, never a bare number.
   Examples: "Day 1", "Days 2-3", "Week 1", "Final Revision".
5. In the "Topics" column, if a period covers more than one topic, separate
   them using a semicolon, e.g.: "Thermodynamics basics; Heat engines;
   Revision: Module 1" — do NOT use bullet characters, dashes, or line
   breaks inside the cell. Keep it as one flowing line separated by
   semicolons so it renders cleanly everywhere.
6. Keep each topic label to 3-5 words — short labels, not sentences.
7. Prioritise high-weightage and difficult topics by giving them more time
   within their row's Hours/Day, not extra commentary.
8. The LAST row(s) must cover the final 2-3 days before the exam as
   dedicated revision time.
9. After the table, add a "Final Revision" section with exactly 3 bullet
   points covering the last 1-2 days before the exam.
10. Do NOT include motivational advice, generic study tips, introductions,
    explanations, or conclusions of any kind.
11. Do NOT repeat these rules or restate the exam date outside the table.

Output ONLY the table and the Final Revision section. Nothing else.
"""
    



    result = generate_text(prompt, api_key=api_key, temperature=0.3, max_tokens=3200)

    if not result.strip():
        raise ValueError("Planner Agent returned empty. Check your API key and quota.")

    return result
