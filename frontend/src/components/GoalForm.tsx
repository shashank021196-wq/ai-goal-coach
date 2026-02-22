/**
 * components/GoalForm.tsx
 * =======================
 * The input form: textarea + Refine button.
 * Handles loading state, error display, and emits result to parent.
 */

"use client";

import { useState } from "react";
import { refineGoal, RefineResponse } from "@/lib/api";

interface GoalFormProps {
  onResult: (result: RefineResponse, rawGoal: string) => void;
}

export default function GoalForm({ onResult }: GoalFormProps) {
  const [rawGoal, setRawGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRefine = async () => {
    if (!rawGoal.trim()) {
      setError("Please enter a goal first.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await refineGoal(rawGoal);

      if (!result.success) {
        setError(result.error || "Something went wrong.");
        // Still pass to parent so telemetry shows (if available)
        if (result.latency_ms) onResult(result, rawGoal);
      } else {
        onResult(result, rawGoal);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Network error — is the backend running?";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const exampleGoals = [
    "I want to get better at sales",
    "I want to improve my leadership skills",
    "I want to learn data analysis",
  ];

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-1">
        What do you want to achieve?
      </h2>
      <p className="text-sm text-gray-500 mb-4">
        Be as vague or specific as you want — the AI will help structure it.
      </p>

      <textarea
        value={rawGoal}
        onChange={(e) => {
          setRawGoal(e.target.value);
          setError(null);
        }}
        placeholder="e.g. I want to get better at presentations..."
        rows={4}
        className="w-full border border-gray-200 rounded-xl p-3 text-gray-800 placeholder-gray-400 
                   focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                   resize-none text-sm transition"
        disabled={loading}
      />

      {/* Example prompts */}
      <div className="mt-2 flex flex-wrap gap-2">
        {exampleGoals.map((eg) => (
          <button
            key={eg}
            onClick={() => { setRawGoal(eg); setError(null); }}
            className="text-xs text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full 
                       hover:bg-indigo-100 transition cursor-pointer"
          >
            {eg}
          </button>
        ))}
      </div>

      {error && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          ⚠️ {error}
        </div>
      )}

      <button
        onClick={handleRefine}
        disabled={loading || !rawGoal.trim()}
        className="mt-4 w-full bg-indigo-600 text-white font-medium py-2.5 px-6 rounded-xl
                   hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed
                   transition flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Refining with AI...
          </>
        ) : (
          <>✨ Refine My Goal</>
        )}
      </button>
    </div>
  );
}
