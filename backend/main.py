"""
main.py
=======
FastAPI application entry point.

Responsibilities:
- Create the FastAPI app
- Register routers
- Initialize DB on startup
- Configure CORS (allows Next.js dev server to call the API)
- Health check endpoint

Run with:
    uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes.goals import router as goals_router
from database.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on startup: initialize the SQLite database."""
    print("🚀 Starting AI Goal Coach API...")
    await init_db()
    print("✅ Database initialized")
    print("📋 API docs available at: http://localhost:8000/docs")
    yield
    print("👋 Shutting down AI Goal Coach API")


app = FastAPI(
    title="AI Goal Coach API",
    description="Transforms vague employee aspirations into structured SMART goals using Gemini AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS: Allow requests from Next.js dev server (port 3000)
# In production, replace with your actual frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes — all endpoints are prefixed with /api
app.include_router(goals_router, prefix="/api")


@app.get("/health")
async def health_check():
    """
    Quick health check endpoint.
    In production, you'd also check DB connectivity and AI API reachability here.
    """
    return {
        "status": "healthy",
        "service": "AI Goal Coach API",
        "version": "1.0.0"
    }
