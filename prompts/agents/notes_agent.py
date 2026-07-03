# agents/notes_agent.py

from agents.llm_provider import generate_text

def generate_notes(text: str, api_key: str = None) -> str:
    if not text or not text.strip():
        raise ValueError("Cannot generate notes: document text is empty.")

    prompt = f"""You are an expert university professor creating highly structured, topic-wise exam revision notes.

Requirements:
1. Extract and cover every distinct topic and subtopic from the material.
2. Provide a brief but complete explanation for each concept (roughly 3-4 sentences). It should be enough to actually understand the theory, but not a long-winded essay.
3. Include key definitions, formulas, and terminology where relevant.
4. Use clear headings (## Topic Name) to organise the content by individual topics.
5. After the 3-4 sentence explanation, use short bullet points for details, steps, characteristics, or examples.
6. Include short comparison tables wherever they help quick revision.
7. Clearly mark important / frequently-asked exam topics with a 🎯 next to the heading.
8. Mention advantages, disadvantages, or limitations using quick bullet points.
9. Do NOT include question breakdowns (e.g., 2-mark, 5-mark).
10. Do NOT pad with generic filler, introductions, or conclusions. Go straight into the notes.
11. The notes must be detailed enough to learn from, but structured for rapid memorisation.
12. The notes must be highly skimmable. Keep the first two sections ("📚 Topic-wise Study Notes" and "🎯 High-Yield Exam Topics") focused and brief so you have enough output space to fully generate the "⚡ Quick Revision Cheat Sheet" at the end.

Output Format (use these exact section headings):
# 📚 Topic-wise Study Notes
# 🎯 High-Yield Exam Topics
# ⚡ Quick Revision Cheat Sheet

Within "📚 Topic-wise Study Notes", use ## subheadings for every individual topic. Under each topic heading, provide the brief explanation, immediately followed by bulleted key points.

Study Material:
{text}
"""

    # Hit the maximum output token threshold for comprehensive notes
    result = generate_text(prompt, api_key=api_key, temperature=0.3, max_tokens=8192)

    # Self-healing agent fallback: if the model dropped its pen before finishing, recover the missing block
    if "⚡ Quick Revision Cheat Sheet" not in result:
        extra_content = generate_text(
            prompt + "\n\nCRITICAL: The previous generation was incomplete. "
            "Output ONLY the content for the '⚡ Quick Revision Cheat Sheet' section. "
            "Do not repeat previous sections.", 
            api_key=api_key, 
            temperature=0.3, 
            max_tokens=2000
        )
        result += "\n\n" + extra_content

    return result
