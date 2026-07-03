from tools.pdf_reader import extract_text
from agents.notes_agent import generate_notes
from agents.quiz_agent import generate_questions
from agents.planner_agent import generate_study_plan

import os

pdf_path = "sample.pdf"

print("Reading PDF...")
text = extract_text(pdf_path)

print("Generating Notes...")
notes = generate_notes(text)

print("Generating Questions...")
questions = generate_questions(notes)

print("Generating Study Plan...")
study_plan = generate_study_plan(
    notes,
    "2026-07-20",
    3
)

os.makedirs("data/processed", exist_ok=True)

with open("data/processed/notes.txt", "w", encoding="utf-8") as f:
    f.write(notes)

with open("data/processed/questions.txt", "w", encoding="utf-8") as f:
    f.write(questions)

with open("data/processed/study_plan.txt", "w", encoding="utf-8") as f:
    f.write(study_plan)

print("✅ Notes generated")
print("✅ Questions generated")
print("✅ Study plan generated")