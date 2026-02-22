# AI Goal Coach

> Transforms vague employee aspirations into structured SMART goals using Groq AI.

---

## Quick Start (Run in 5 Minutes)

### Prerequisites
- Python 3.11+
- Node.js 18+
- A free Groq API key → [Get one here](https://console.groq.com/keys)

### 1. Clone & Setup Backend
```bash
git clone <your-repo-url>
cd ai-goal-coach/backend
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --reload --port 8000
```

### 2. Setup Frontend
```bash
cd ../frontend
npm install
npm run dev
```

### 3. Open the App
Visit → **http://localhost:3000**

### 4. Run the Eval Script
```bash
cd backend
source .venv/bin/activate
python tests/test_evals.py
```
