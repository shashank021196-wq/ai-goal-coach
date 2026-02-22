"""
models/goal.py
==============
Single source of truth for all data shapes in the application.

- GoalResponse: What the AI must return (enforced via Gemini JSON mode)
- RefineRequest: What the frontend sends to POST /refine
- GoalSaveRequest: What the frontend sends to POST /goals
- GoalRecord: What the DB returns to GET /goals
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class GoalResponse(BaseModel):
    """
    Schema enforced on Gemini's output via response_schema.
    Gemini CANNOT return anything that doesn't match this shape.
    """
    refined_goal: str = Field(
        description="The SMART version of the user's vague goal"
    )
    key_results: List[str] = Field(
        description="3 to 5 measurable, actionable steps to achieve the goal"
    )
    confidence_score: int = Field(
        description="Integer 1-10: how confident the AI is that the input was actually a goal",
        ge=1,
        le=10
    )


class RefineRequest(BaseModel):
    """Incoming request body for POST /refine"""
    raw_goal: str = Field(description="The user's raw, unrefined goal text")


class GoalSaveRequest(BaseModel):
    """Incoming request body for POST /goals (save a refined goal)"""
    raw_goal: str
    refined_goal: str
    key_results: List[str]
    confidence_score: int


class GoalRecord(BaseModel):
    """What we return from the database for GET /goals"""
    id: int
    raw_goal: str
    refined_goal: str
    key_results: List[str]
    confidence_score: int
    created_at: str


class RefineResponse(BaseModel):
    """What POST /refine returns to the frontend"""
    success: bool
    data: Optional[GoalResponse] = None
    error: Optional[str] = None
    # Telemetry summary included in response for real-time demo
    latency_ms: Optional[float] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
