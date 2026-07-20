"""
generator.py
------------
The RAG "brain" of the agent. Responsibilities:

1. Pull historic facts from ChromaDB (offline knowledge).
2. Pull fresh facts from DuckDuckGo (live knowledge).
3. Merge both into a single grounded context block.
4. Send that context + instructions to an LLM (OpenAI, Anthropic, or Gemini,
   chosen via LLM_PROVIDER in .env) and demand a strict JSON response
   so the UI layer can parse it reliably -- no regex guessing required.

Output contract (always a Python dict shaped like this):
{
  "sport": "Badminton",
  "difficulty": "Medium",
  "questions": [
    {
      "question": "...",
      "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
      "correct_answer": "B",
      "explanation": "..."
    },
    ...
  ]
}
"""

import json
import re

from src.config import (
    LLM_PROVIDER,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    ANTHROPIC_API_KEY,
    ANTHROPIC_MODEL,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    validate_config,
)
from src.database import query_historic_facts
from src.search import get_live_news_context

QUESTION_COUNT = 5  # Assignment asks for 4-5 questions per quiz


def _build_context(sport: str) -> str:
    """Gathers and merges historic (ChromaDB) + live (web) context."""
    db_query = f"{sport} history championships records rules famous players"
    db_matches = query_historic_facts(sport=sport, query_text=db_query, n_results=3)
    db_context = "\n".join(f"- {fact}" for fact in db_matches) if db_matches else "No offline historic data recorded for this sport."

    web_context = get_live_news_context(sport)

    return (
        f"=== HISTORICAL FACTS (ChromaDB) ===\n{db_context}\n\n"
        f"=== LIVE INTERNET NEWS (DuckDuckGo) ===\n{web_context}"
    )


def _build_prompts(sport: str, difficulty: str, unified_context: str, avoid_questions=None):
    """Builds the system instruction and user prompt shared by both providers."""
    avoid_clause = ""
    if avoid_questions:
        joined = "; ".join(avoid_questions[:10])
        avoid_clause = (
            f"\n\nDo NOT repeat or closely rephrase any of these previously used "
            f"questions: {joined}"
        )

    system_instruction = (
        "You are an expert sports quiz creator. Write multiple-choice quiz "
        "questions relying STRICTLY on the provided context. Never invent facts "
        "that are not supported by the context. If the context is scarce, work "
        "with what is available, but keep every detail accurate to the source "
        "text. Always respond with valid JSON only -- no markdown, no commentary, "
        "no code fences.\n\n"
        f"CONTEXT:\n{unified_context}"
    )

    user_prompt = (
        f"Generate exactly {QUESTION_COUNT} unique multiple-choice questions for "
        f"the sport: {sport}.\n"
        f"Difficulty target: {difficulty}.\n"
        "Each question must have exactly 4 options (A-D), one correct answer, "
        "and a short explanation grounded in the context above."
        f"{avoid_clause}\n\n"
        "Respond with ONLY a JSON object in exactly this shape:\n"
        "{\n"
        '  "sport": "<sport name>",\n'
        '  "difficulty": "<difficulty>",\n'
        '  "questions": [\n'
        "    {\n"
        '      "question": "<question text>",\n'
        '      "options": {"A": "<option>", "B": "<option>", "C": "<option>", "D": "<option>"},\n'
        '      "correct_answer": "<A, B, C, or D>",\n'
        '      "explanation": "<short grounded explanation>"\n'
        "    }\n"
        "  ]\n"
        "}"
    )
    return system_instruction, user_prompt


def _extract_json(raw_text: str) -> dict:
    """Defensive JSON extraction -- strips markdown code fences if the model
    adds them despite instructions, then parses. Raises ValueError with a
    helpful message on failure so the UI can show it cleanly."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON. Raw output:\n{raw_text}") from e


def _call_openai(system_instruction: str, user_prompt: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


def _call_anthropic(system_instruction: str, user_prompt: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2000,
        temperature=0.7,
        system=system_instruction,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def _call_gemini(system_instruction: str, user_prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            response_mime_type="application/json",
        ),
    )
    return response.text


def compile_quiz_data(sport: str, difficulty: str, avoid_questions=None):
    """
    Main entry point used by the Streamlit UI.

    Returns a tuple: (quiz_dict, unified_context_string)
    - quiz_dict: parsed structured quiz, ready to render.
    - unified_context_string: the raw grounding context, shown in the UI's
      "Inspect Ground Truth" panel for transparency/auditing.
    """
    validate_config()

    unified_context = _build_context(sport)
    system_instruction, user_prompt = _build_prompts(
        sport, difficulty, unified_context, avoid_questions
    )

    if LLM_PROVIDER == "anthropic":
        raw_output = _call_anthropic(system_instruction, user_prompt)
    elif LLM_PROVIDER == "gemini":
        raw_output = _call_gemini(system_instruction, user_prompt)
    else:
        raw_output = _call_openai(system_instruction, user_prompt)

    quiz_dict = _extract_json(raw_output)
    return quiz_dict, unified_context
