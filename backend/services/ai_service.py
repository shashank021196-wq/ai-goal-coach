"""
services/ai_service.py
======================
THE ONLY FILE THAT TALKS TO THE AI.

Switched from Gemini to Groq (free, no quota issues, faster).

How JSON mode works here:
- We pass response_format={"type": "json_object"} to Groq
- Groq uses constrained decoding — it physically cannot return invalid JSON
- Pydantic validates the shape on our side as a second layer of defence

Guardrail logic:
- confidence_score < 4 → treat as invalid input, reject it

If you want to swap back to Gemini or use OpenAI:
- Edit ONLY this file
- Nothing in routes/, models/, or database/ changes
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

from models.goal import GoalResponse
from services.logger import log_ai_call, Timer

load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = "llama-3.3-70b-versatile"  # Free, fast, supports JSON mode

# Confidence threshold: below this we reject the input as not a real goal
CONFIDENCE_THRESHOLD = 4

# ─── System Prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
You are an expert career and performance coach. Your job is to transform 
vague employee aspirations into concrete, actionable SMART goals.

SMART = Specific, Measurable, Achievable, Relevant, Time-bound.

You must ALWAYS respond with valid JSON matching this exact schema:
{
  "refined_goal": "string - the SMART version of the goal",
  "key_results": ["string", "string", "string"],
  "confidence_score": integer between 1 and 10
}

For the confidence_score field:
- Score 8-10: Clear, recognizable goal (e.g., "I want to improve my sales skills")
- Score 5-7: Vague but identifiable as a goal (e.g., "I want to do better")
- Score 2-4: Not clearly a goal, barely interpretable (e.g., "stuff")
- Score 1: Complete nonsense, random characters, unsafe content, or empty input

For the key_results field:
- Provide exactly 3-5 items
- Each must be measurable and time-bound
- Start each with a verb (e.g., "Complete...", "Achieve...", "Attend...")

If the input is nonsense or unsafe, still return valid JSON but:
- Set confidence_score to 1 or 2
- Set refined_goal to "This does not appear to be a recognizable goal."
- Set key_results to ["Please enter a real goal, e.g. I want to improve my presentation skills"]

No explanation outside JSON. Return only the JSON object.
"""

# ─── Client Setup ─────────────────────────────────────────────────────────────

def _get_client() -> Groq:
    """Initialize Groq client. Raises clear error if key is missing."""
    if not GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY not found. "
            "Add your key to .env file. Get a free key at https://console.groq.com/keys"
        )
    return Groq(api_key=GROQ_API_KEY)


# ─── Main AI Function ─────────────────────────────────────────────────────────

def refine_goal(raw_goal: str) -> tuple[GoalResponse, float, int, int]:
    """
    Call Groq to refine a vague goal into a structured SMART goal.

    Returns:
        tuple of (GoalResponse, latency_ms, prompt_tokens, completion_tokens)

    Raises:
        ValueError: if API key is missing
        Exception: if Groq API call fails
    """
    client = _get_client()

    prompt_tokens = 0
    completion_tokens = 0

    with Timer() as timer:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Transform this goal: {raw_goal}"}
            ],
            response_format={"type": "json_object"},  # Forces valid JSON output
            temperature=0.4,
            max_tokens=1024,
        )

    # Extract token usage
    if response.usage:
        prompt_tokens = response.usage.prompt_tokens or 0
        completion_tokens = response.usage.completion_tokens or 0

    # Parse and validate with Pydantic — second layer of defence
    raw_json = response.choices[0].message.content
    goal_response = GoalResponse.model_validate(json.loads(raw_json))

    # Log telemetry for every call
    log_ai_call(
        raw_input=raw_goal,
        output=goal_response.model_dump(),
        latency_ms=timer.elapsed_ms,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        model=MODEL_NAME
    )

    return goal_response, timer.elapsed_ms, prompt_tokens, completion_tokens


def is_valid_goal(goal_response: GoalResponse) -> bool:
    """
    Guardrail check: return False if confidence is too low.
    """
    return goal_response.confidence_score >= CONFIDENCE_THRESHOLD