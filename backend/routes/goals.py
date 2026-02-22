"""
routes/goals.py
===============
HTTP endpoints only. No business logic lives here.

Rules for this file:
- Receive request → call service/db → return response
- Never import Gemini directly
- Never write SQL directly
- If a function is getting long, the logic belongs in services/ instead

Endpoints:
  POST /refine   → call AI, return structured goal (does NOT save)
  POST /goals    → save a confirmed goal to DB
  GET  /goals    → return all saved goals
  GET  /goals/{id} → return one goal
"""

from fastapi import APIRouter, HTTPException
from models.goal import (
    RefineRequest,
    GoalSaveRequest,
    GoalRecord,
    RefineResponse
)
from services.ai_service import refine_goal, is_valid_goal
from database.db import save_goal, get_all_goals, get_goal_by_id

router = APIRouter()


@router.post("/refine", response_model=RefineResponse)
async def refine_goal_endpoint(request: RefineRequest):
    """
    Call AI to refine a vague goal into a SMART goal.
    
    Does NOT save to database — user confirms before saving.
    Returns the AI result + telemetry summary.
    
    Guardrail: if confidence_score < 4, returns success=False with explanation.
    """
    # Basic input validation before even calling the AI
    raw = request.raw_goal.strip()
    if not raw:
        return RefineResponse(
            success=False,
            error="Please enter a goal before clicking Refine."
        )

    if len(raw) < 3:
        return RefineResponse(
            success=False,
            error="Your input is too short to be a goal. Try something like 'I want to improve my presentation skills'."
        )

    try:
        goal_response, latency_ms, prompt_tokens, completion_tokens = refine_goal(raw)

        # Guardrail: low confidence = not a real goal
        if not is_valid_goal(goal_response):
            return RefineResponse(
                success=False,
                error=f"This doesn't look like a recognizable goal (confidence: {goal_response.confidence_score}/10). "
                      f"Try something like 'I want to improve my public speaking skills'.",
                latency_ms=latency_ms,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens
            )

        return RefineResponse(
            success=True,
            data=goal_response,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )

    except ValueError as e:
        # Missing API key or config error
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        # Gemini API error, network error, etc.
        raise HTTPException(
            status_code=503,
            detail=f"AI service temporarily unavailable: {str(e)}"
        )


@router.post("/goals", response_model=dict)
async def save_goal_endpoint(request: GoalSaveRequest):
    """
    Save a confirmed refined goal to the database.
    Called when user clicks "Save" after reviewing the AI output.
    """
    try:
        goal_id = await save_goal(
            raw_goal=request.raw_goal,
            refined_goal=request.refined_goal,
            key_results=request.key_results,
            confidence_score=request.confidence_score
        )
        return {"success": True, "id": goal_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save goal: {str(e)}")


@router.get("/goals", response_model=list[GoalRecord])
async def get_goals_endpoint():
    """Return all saved goals, newest first."""
    try:
        return await get_all_goals()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch goals: {str(e)}")


@router.get("/goals/{goal_id}", response_model=GoalRecord)
async def get_goal_endpoint(goal_id: int):
    """Return a single goal by ID."""
    goal = await get_goal_by_id(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")
    return goal
