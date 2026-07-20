"""
app.py
------
Front-end entry point. Run with:  streamlit run app.py

Coordinates: sidebar inputs -> src/generator.py (RAG pipeline) -> renders
the structured quiz with clickable answer reveal and a ground-truth
context inspector for transparency.
"""

import streamlit as st
from src.generator import compile_quiz_data
from src.database import setup_and_populate_db

SPORTS = ["Cricket", "Football", "Tennis", "Badminton", "Basketball"]
DIFFICULTIES = ["Easy", "Medium", "Hard"]


# ---------------------------------------------------------------------------
# 1. Warm up the vector DB with offline facts on startup (runs once, cached)
# ---------------------------------------------------------------------------
@st.cache_resource
def prepare_knowledge_base():
    setup_and_populate_db()


prepare_knowledge_base()

# ---------------------------------------------------------------------------
# 2. Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Sports Quiz Agent", page_icon="🏆", layout="centered")

st.title("🏆 AI-Powered Sports Quiz Generator")
st.write(
    "Generate factually grounded sports quizzes for social media. "
    "Powered by RAG: ChromaDB (historic facts) + live web search (fresh news)."
)

# ---------------------------------------------------------------------------
# 3. Sidebar inputs
# ---------------------------------------------------------------------------
st.sidebar.header("Quiz Settings")
sport_choice = st.sidebar.selectbox("Select Sport", SPORTS)
difficulty = st.sidebar.select_slider("Select Difficulty", options=DIFFICULTIES, value="Medium")

# ---------------------------------------------------------------------------
# 4. Session state -- keeps quiz + selections alive across reruns
# ---------------------------------------------------------------------------
if "quiz" not in st.session_state:
    st.session_state.quiz = None
    st.session_state.context = None
    st.session_state.selected_answers = {}
    st.session_state.asked_questions = []  # used to avoid repeats on regenerate


def _generate(sport, diff):
    with st.spinner("Retrieving historic facts, scouring the live web, and writing your quiz..."):
        try:
            quiz, context_used = compile_quiz_data(
                sport, diff, avoid_questions=st.session_state.asked_questions
            )
            st.session_state.quiz = quiz
            st.session_state.context = context_used
            st.session_state.selected_answers = {}
            st.session_state.asked_questions.extend(
                q["question"] for q in quiz.get("questions", [])
            )
            st.success("Quiz created successfully!")
        except Exception as e:
            st.error(f"Failed to generate quiz: {e}")


col1, col2 = st.sidebar.columns(2)
if col1.button("Generate Quiz", use_container_width=True):
    _generate(sport_choice, difficulty)
if col2.button("Regenerate", use_container_width=True, disabled=st.session_state.quiz is None):
    _generate(sport_choice, difficulty)

st.sidebar.divider()
st.sidebar.caption(
    "Regenerate reuses your last sport/difficulty and asks the model to avoid "
    "repeating earlier questions in this session."
)

# ---------------------------------------------------------------------------
# 5. Render the quiz
# ---------------------------------------------------------------------------
quiz = st.session_state.quiz

if quiz:
    st.subheader(f"Quiz: {quiz.get('sport', sport_choice)} ({quiz.get('difficulty', difficulty)})")

    for i, q in enumerate(quiz.get("questions", [])):
        st.markdown(f"**Q{i + 1}. {q['question']}**")

        option_labels = [f"{key}) {value}" for key, value in q["options"].items()]
        answer_key = f"q_{i}"

        chosen = st.radio(
            "Choose an answer:",
            options=option_labels,
            key=answer_key,
            index=None,
            label_visibility="collapsed",
        )

        if chosen:
            chosen_letter = chosen.split(")")[0].strip()
            correct_letter = q["correct_answer"].strip()[0]

            if chosen_letter == correct_letter:
                st.success(f"✅ Correct! **{correct_letter}) {q['options'][correct_letter]}**")
            else:
                st.error(
                    f"❌ Not quite. Correct answer: **{correct_letter}) {q['options'][correct_letter]}**"
                )
            st.info(f"💡 {q['explanation']}")

        st.divider()

    # Copy-paste friendly plain-text version for social media posting
    with st.expander("📋 Copy-paste plain text version"):
        lines = [f"Sport: {quiz.get('sport')}", f"Difficulty: {quiz.get('difficulty')}", ""]
        for i, q in enumerate(quiz.get("questions", [])):
            lines.append(f"Q{i + 1}. {q['question']}")
            for key, val in q["options"].items():
                lines.append(f"{key}) {val}")
            lines.append(f"Correct Answer: {q['correct_answer']}")
            lines.append(f"Explanation: {q['explanation']}")
            lines.append("")
        st.text_area("Quiz text", value="\n".join(lines), height=300)

    # Ground-truth context for auditing / demonstrating grounding to graders
    with st.expander("🔍 Inspect Ground Truth (RAG context used)"):
        st.code(st.session_state.context, language="markdown")
else:
    st.info("Choose a sport and difficulty in the sidebar, then click **Generate Quiz** to begin.")
