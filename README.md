# 🏆 AI-Powered Sports Quiz Generation Agent

An interactive, factually grounded Streamlit web app that generates multiple-choice
sports quizzes on demand, using **Retrieval-Augmented Generation (RAG)**: a
local **ChromaDB** vector database for historic facts, combined with **live
DuckDuckGo web search** for recent news, both fed to an LLM (OpenAI or
Anthropic Claude) to eliminate hallucinated facts.

## How It Works

```
User selects Sport + Difficulty
            │
            ▼
   ┌─────────────────────┐
   │   src/generator.py   │
   └─────────────────────┘
       │              │
       ▼              ▼
ChromaDB query   DuckDuckGo search
(historic facts) (live news 2026)
       │              │
       └──────┬───────┘
              ▼
   Merged grounded context
              │
              ▼
   LLM (OpenAI or Claude) generates
   strict-JSON quiz using ONLY that context
              │
              ▼
   Streamlit renders 5 MCQs with
   click-to-reveal answers + explanations
```

## Project Structure

```
sports-quiz-agent/
├── .env.example        # Template for your API keys -- copy to .env
├── .gitignore
├── requirements.txt
├── README.md
├── data/
│   └── sports_facts.json   # Offline historic facts (5 sports)
├── chroma_db/               # Auto-created by ChromaDB on first run
├── src/
│   ├── __init__.py
│   ├── config.py            # Env vars + provider selection
│   ├── database.py          # ChromaDB insert/query logic
│   ├── search.py             # DuckDuckGo live search logic
│   └── generator.py          # RAG orchestration + LLM call
└── app.py                    # Streamlit UI entry point
```

## Setup Instructions

### 1. Prerequisites

- Python **3.9, 3.10, or 3.11** (avoid 3.12+ — ChromaDB's dependencies are
  most reliable on these versions)
- An API key from **one** of: Google Gemini (has a genuine free tier, no
  credit card needed — recommended if you want zero cost), OpenAI, or
  Anthropic.

### 2. Clone / unzip and enter the project folder

```bash
cd sports-quiz-agent
```

### 3. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure your API key

```bash
cp .env.example .env      # macOS/Linux
copy .env.example .env    # Windows
```

Open `.env` and set:
- `LLM_PROVIDER` to `gemini`, `openai`, or `anthropic`
- The matching API key. For a **free, no-credit-card option**, get a Gemini
  key at https://aistudio.google.com/apikey — the Flash model gives roughly
  1,500 requests/day free, which is more than enough for this project.

### 6. Run the app

```bash
streamlit run app.py
```

Streamlit will open the dashboard in your browser (usually `http://localhost:8501`).

## Using the App

1. Pick a **Sport** and **Difficulty** in the sidebar.
2. Click **Generate Quiz** — the agent retrieves historic facts from
   ChromaDB and fresh news from the web, then asks the LLM to write 5
   grounded multiple-choice questions.
3. Click an answer for each question to instantly see if you're correct,
   plus a source-grounded explanation.
4. Click **Regenerate** for a fresh set on the same sport/difficulty — the
   agent is told to avoid repeating earlier questions from your session.
5. Expand **"Copy-paste plain text version"** to grab a social-media-ready
   version of the quiz.
6. Expand **"Inspect Ground Truth"** to audit exactly which facts (from
   ChromaDB and the web) were used to ground the quiz — useful for
   demonstrating that the agent isn't hallucinating.

## Design Notes

- **Three swappable LLM providers**: `LLM_PROVIDER=gemini`, `openai`, or
  `anthropic` in `.env` — no code changes needed to switch. Gemini is the
  only one with a genuine free tier (no credit card, ~1,500 req/day on
  Flash), so it's the fastest path to a zero-cost working demo.
- **Strict JSON output**: the LLM is instructed (and, for OpenAI, forced via
  `response_format={"type": "json_object"}`) to return structured JSON so
  the app never depends on fragile regex parsing of free-form text.
- **Metadata-filtered vector search**: ChromaDB queries are filtered with
  `where={"sport": sport}` so results never leak facts from the wrong sport.
- **Graceful degradation**: if the web search fails (rate limit, no
  internet), `search.py` returns a fallback string instead of crashing —
  the quiz can still be generated from ChromaDB facts alone.
- **Session state**: quiz results and per-question answer selections
  persist across Streamlit reruns so clicking one answer doesn't reset
  the others.

## Troubleshooting

| Problem | Fix |
|---|---|
| `sqlite3` version error from ChromaDB (Windows/Linux) | `pip install pysqlite3-binary`, then add these two lines to the very top of `src/database.py`: `__import__('pysqlite3'); import sys; sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')` |
| "API Key is missing" | Confirm `.env` exists (not just `.env.example`) and matches `LLM_PROVIDER` |
| Model returns broken JSON | The app raises a clear `ValueError` showing the raw output — check `src/generator.py`'s `_extract_json` |
| DuckDuckGo search returns nothing | Non-fatal — quiz still generates from ChromaDB facts; check console log for the actual error |

## Evaluation Checklist (per assignment spec)

- [x] Sport + difficulty selection
- [x] ChromaDB vector retrieval (metadata-filtered by sport)
- [x] Live DuckDuckGo web search integration
- [x] LLM-grounded generation avoiding hallucination
- [x] 4–5 MCQs per quiz with 4 options, correct answer, explanation
- [x] Regenerate button producing fresh, non-repeating questions
- [x] Clean modular code (`src/` separated by responsibility)
- [x] README with setup instructions and architecture overview
