/**
 * lib/api.ts
 * ==========
 * All HTTP calls to the backend live here.
 * 
 * Why isolate this?
 * - If the backend URL changes, edit ONE file
 * - If we add auth headers later, add them HERE, not in every component
 * - Components stay clean — they call functions, not raw fetch()
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ─── Types (mirroring backend Pydantic models) ────────────────────────────────

export interface GoalResponse {
  refined_goal: string;
  key_results: string[];
  confidence_score: number;
}

export interface RefineResponse {
  success: boolean;
  data?: GoalResponse;
  error?: string;
  latency_ms?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
}

export interface GoalRecord {
  id: number;
  raw_goal: string;
  refined_goal: string;
  key_results: string[];
  confidence_score: number;
  created_at: string;
}

// ─── API Functions ─────────────────────────────────────────────────────────────

/**
 * Send a raw goal to the AI for refinement.
 * Does NOT save to DB — user must confirm first.
 */
export async function refineGoal(rawGoal: string): Promise<RefineResponse> {
  const res = await fetch(`${API_BASE}/api/refine`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw_goal: rawGoal }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }

  return res.json();
}

/**
 * Save a confirmed refined goal to the database.
 */
export async function saveGoal(
  rawGoal: string,
  goalResponse: GoalResponse
): Promise<{ success: boolean; id: number }> {
  const res = await fetch(`${API_BASE}/api/goals`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      raw_goal: rawGoal,
      refined_goal: goalResponse.refined_goal,
      key_results: goalResponse.key_results,
      confidence_score: goalResponse.confidence_score,
    }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }

  return res.json();
}

/**
 * Fetch all saved goals from the database.
 */
export async function fetchGoals(): Promise<GoalRecord[]> {
  const res = await fetch(`${API_BASE}/api/goals`, {
    cache: "no-store", // Always get fresh data
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch goals: ${res.status}`);
  }

  return res.json();
}
