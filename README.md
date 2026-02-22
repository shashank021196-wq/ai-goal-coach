# 🎯 AI Goal Coach

> Transforms vague employee aspirations into structured SMART goals using Gemini AI.

---

## 🚀 Quick Start (Run in 5 Minutes)

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free Gemini API key → [Get one here](https://aistudio.google.com/app/apikey)
- or
- Any free source of API Key

### 1. Clone & Setup Backend
```bash
git clone <your-repo-url>
cd ai-goal-coach/backend

# Install dependencies
pip install -r requirements.txt

# Add your API key
create a .env
# Edit .env and paste your GROQ Key

# Start backend
uvicorn main:app --reload --port 8000
```

### 2. Setup Frontend
```bash
cd ../frontend
npm install
npm run dev
```

### 3. Open the App
Visit → **http://localhost:3000**

API Docs → **http://localhost:8000/docs**

### 4. Run the Eval Script
```bash
cd backend
python tests/test_evals.py
```

---

## 🏗️ Architecture

```
ai-goal-coach/
├── backend/
│   ├── main.py                  # FastAPI entry point, CORS, startup
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── models/
│   │   └── goal.py              # ALL Pydantic schemas (single source of truth)
│   │
│   ├── services/
│   │   ├── ai_service.py        # ONLY file that talks to Gemini
│   │   └── logger.py            # Telemetry: latency, tokens, cost estimation
│   │
│   ├── routes/
│   │   └── goals.py             # HTTP endpoints (no business logic)
│   │
│   ├── database/
│   │   └── db.py                # SQLite via aiosqlite
│   │
│   ├── logs/
│   │   └── telemetry.jsonl      # Auto-generated telemetry log
│   │
│   └── tests/
│       └── test_evals.py        # Standalone AI eval script
│
└── frontend/
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   └── page.tsx          # Main page, orchestrates all components
        ├── components/
        │   ├── GoalForm.tsx      # Input + Refine button
        │   ├── GoalResult.tsx    # AI output + telemetry display + Save button
        │   └── GoalList.tsx      # Saved goals list view
        └── lib/
            └── api.ts            # All fetch() calls to backend
```

---

## 📐 Architecture Decision Record (ADR)

### ADR-001: Why Groq + LLaMA 3.3 70B?

**Decision:** Use `llama-3.3-70b-versatile` via the Groq API.

**Reasons:**
1. **Truly free tier** — 14,400 requests/day, no credit card, no quota exhaustion
2. **Speed** — Groq runs on custom LPU hardware. Typical latency 300-600ms, faster than most hosted LLM APIs
3. **JSON mode** — `response_format={"type": "json_object"}` enforces valid JSON at the API level
4. **OpenAI-compatible SDK** — same interface as OpenAI, future model swaps are trivial
5. **LLaMA 3.3 70B quality** — produces high-quality SMART goals comparable to GPT-4o-mini for structured tasks

**Why not Gemini?**
Gemini's free tier quota gets exhausted quickly during development. Groq's free tier is far more generous (14,400 req/day vs Gemini's per-minute limits).

**Trade-off:** LLaMA 3.3 70B has slightly less instruction-following precision than GPT-4o on complex prompts. For this use case the quality difference is negligible. To upgrade, change one line in `ai_service.py`: `MODEL_NAME = "llama-3.1-405b"`

---

### ADR-002: Why JSON Mode Over Regex?

**Decision:** Use Gemini's `response_schema` (controlled generation) instead of prompt engineering + regex parsing.

**The problem with regex:**
```python
# BAD — this breaks constantly
import re
match = re.search(r'"refined_goal":\s*"(.+?)"', response.text)
```
- The AI might format JSON differently each call
- Nested quotes, line breaks, unicode all break regex
- You're fighting the AI instead of working with it
- One model update and all your regex patterns are broken

**How `response_schema` works:**
```python
# GOOD — Gemini physically cannot return invalid JSON
response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents=prompt,
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=GoalResponse,  # Pydantic model passed directly
    )
)
result = GoalResponse.model_validate_json(response.text)  # Always succeeds
```
The API enforces the schema at generation time using constrained decoding — it's not a filter, it's built into how the tokens are selected.

**Second layer:** Even after Gemini guarantees the JSON, we run Pydantic validation on our side. Two lines of defence.

---

### ADR-003: Why FastAPI + Python?

**Decision:** Python FastAPI backend, not Node.js/Express.

**Reasons:**
1. **Pydantic is first-class** — schema definition, validation, and serialization all in one model class
2. **Google's Python SDK** is more mature and better documented than the JS equivalent
3. **FastAPI auto-generates OpenAPI docs** at `/docs` — useful for demos
4. **async/await** — FastAPI handles concurrent requests without blocking
5. **Ecosystem** — Python's data/AI ecosystem (if this grows to include evaluations, fine-tuning, etc.)

---

### ADR-004: Why SQLite?

**Decision:** SQLite with `aiosqlite` for async access.

**For this challenge:** Zero infrastructure setup, single file, works on any machine.

**Trade-off for scale:** SQLite has a write lock — concurrent writes queue up. Fine for one user, becomes a bottleneck at ~100 concurrent writers. 

**Migration path:** The entire database layer is in `database/db.py`. To migrate to PostgreSQL:
1. `pip install asyncpg`
2. Replace `aiosqlite.connect(DB_PATH)` with `asyncpg.connect(DATABASE_URL)`
3. Nothing in routes/ or services/ changes

---

### ADR-005: Why Separate `ai_service.py` from Routes?

**Decision:** All Gemini code is isolated in `services/ai_service.py`.

This is the most important architectural decision for long-term maintainability.

**If you swap Gemini for OpenAI tomorrow:**
```bash
# Only edit ONE file
vi backend/services/ai_service.py
```

Change the client initialization and API call format. The routes, models, database, frontend — none of it changes. The `GoalResponse` Pydantic model is the contract; any AI provider that can return that shape is a valid implementation.

---

## 📊 Observability Design

Every AI call logs to two places simultaneously:
1. **Console** — visible in terminal during demo/development
2. **`logs/telemetry.jsonl`** — structured log file, one JSON per line

### Log format:
```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "model": "gemini-1.5-flash",
  "input": "I want to get better at sales",
  "output": { "refined_goal": "...", "key_results": [...], "confidence_score": 8 },
  "latency_ms": 1243.5,
  "tokens": { "prompt": 312, "completion": 187, "total": 499 },
  "estimated_cost_usd": 0.00008,
  "error": null
}
```

### Why `.jsonl`?
JSONL (JSON Lines) is the standard format for log aggregators. Every major tool — Datadog, CloudWatch, Splunk, Elasticsearch — can ingest it without transformation.

---

## 🧪 Eval Strategy

The eval script (`tests/test_evals.py`) tests **behavioral contracts**, not Python logic.

### What it tests:
| Test | Input | Expected |
|------|-------|----------|
| Clear goal | "I want to improve my sales performance" | Valid SMART goal, confidence ≥ 7 |
| Vague goal | "I want to get better at my job" | Valid SMART goal, confidence ≥ 4 |
| Nonsense | "kjsfdkjhsdfkjh" | Rejected (confidence < 4) |
| SQL injection | `'; DROP TABLE goals; --` | Rejected, not hallucinated into a goal |

### Why run evals?
If you change:
- The AI model version
- The system prompt
- The confidence threshold
- The schema

→ Run `python tests/test_evals.py`. If it passes, the behavioral contract is intact. If it fails, you know exactly what broke before it reaches production.

---

## 📈 Scaling to 10,000 Users

| Concern | Current (Challenge) | At Scale |
|---------|---------------------|----------|
| Database | SQLite (file) | PostgreSQL on RDS / Supabase |
| AI calls | Synchronous per request | Queue with Celery + Redis (prevent timeout) |
| Rate limiting | None | Token bucket per user (Redis) |
| Caching | None | Cache identical inputs with Redis (hash the goal text) |
| Monitoring | JSONL file | Ship logs to Datadog / Grafana |
| Auth | None | JWT tokens + user-scoped goal storage |
| AI fallback | Hard 503 error | Circuit breaker → fallback response or retry with backoff |
| Frontend | Polling | WebSocket for real-time AI streaming |

**What does NOT change at scale:** `ai_service.py`, `models/goal.py`, `routes/goals.py`. The architecture handles scale through infrastructure, not code rewrites.

---

## 🔄 AI Model Swap Guide

> "If we asked you to swap the AI model tomorrow, how hard would it be?"

**Answer: 30 minutes, editing one file.**

Open `backend/services/ai_service.py` and change:

```python
# FROM (Gemini)
from google import genai
client = genai.Client(api_key=GEMINI_API_KEY)
response = client.models.generate_content(
    model="gemini-1.5-flash",
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=GoalResponse,
    )
)

# TO (OpenAI)
from openai import OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)
response = client.beta.chat.completions.parse(
    model="gpt-4o-mini",
    messages=[...],
    response_format=GoalResponse,  # OpenAI also supports Pydantic
)
```

The `GoalResponse` Pydantic model doesn't change. The routes don't change. The frontend doesn't change. The telemetry logger wraps it the same way.

---

## 🛡️ What Happens if the AI API Goes Down?

In `routes/goals.py`:
```python
except Exception as e:
    raise HTTPException(
        status_code=503,
        detail=f"AI service temporarily unavailable: {str(e)}"
    )
```

The frontend shows a clear error. The app doesn't crash. Previously saved goals are still accessible from SQLite. The user can try again.

**For production:** Add a circuit breaker (e.g., `pybreaker` library) that stops calling Gemini after N consecutive failures and returns a friendly degraded response immediately, instead of making users wait for timeouts.

---

## 📝 License

MIT