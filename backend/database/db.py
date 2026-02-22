"""
database/db.py
==============
SQLite database layer using aiosqlite for async access.

Why SQLite for this challenge?
- Zero infrastructure — single file, no server needed
- Perfect for demo/development
- In production at scale, swap this file for PostgreSQL + asyncpg
  and nothing in routes/ or services/ changes

The DB file is created automatically on first run at backend/goals.db
"""

import aiosqlite
import json
from pathlib import Path
from models.goal import GoalRecord

DB_PATH = Path(__file__).parent.parent / "goals.db"


async def init_db() -> None:
    """
    Create tables if they don't exist.
    Called once on app startup from main.py.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_goal        TEXT NOT NULL,
                refined_goal    TEXT NOT NULL,
                key_results     TEXT NOT NULL,   -- stored as JSON string
                confidence_score INTEGER NOT NULL,
                created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def save_goal(
    raw_goal: str,
    refined_goal: str,
    key_results: list[str],
    confidence_score: int
) -> int:
    """
    Insert a new goal record. Returns the new row ID.
    key_results is stored as a JSON string in the TEXT column.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            INSERT INTO goals (raw_goal, refined_goal, key_results, confidence_score)
            VALUES (?, ?, ?, ?)
            """,
            (raw_goal, refined_goal, json.dumps(key_results), confidence_score)
        )
        await db.commit()
        return cursor.lastrowid


async def get_all_goals() -> list[GoalRecord]:
    """
    Fetch all saved goals, newest first.
    Deserializes key_results back from JSON string to list.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM goals ORDER BY created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()

    return [
        GoalRecord(
            id=row["id"],
            raw_goal=row["raw_goal"],
            refined_goal=row["refined_goal"],
            key_results=json.loads(row["key_results"]),
            confidence_score=row["confidence_score"],
            created_at=str(row["created_at"])
        )
        for row in rows
    ]


async def get_goal_by_id(goal_id: int) -> GoalRecord | None:
    """Fetch a single goal by ID. Returns None if not found."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM goals WHERE id = ?", (goal_id,)
        ) as cursor:
            row = await cursor.fetchone()

    if not row:
        return None

    return GoalRecord(
        id=row["id"],
        raw_goal=row["raw_goal"],
        refined_goal=row["refined_goal"],
        key_results=json.loads(row["key_results"]),
        confidence_score=row["confidence_score"],
        created_at=str(row["created_at"])
    )
