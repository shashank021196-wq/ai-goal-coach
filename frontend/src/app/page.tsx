/**
 * app/page.tsx
 * ============
 * Main page — orchestrates the three panels:
 * 1. GoalForm    → user inputs their vague goal
 * 2. GoalResult  → AI's structured output appears here
 * 3. GoalList    → all saved goals from the database
 * 
 * State management is intentionally simple (useState).
 * For 10,000 users we'd add React Query for caching/refetching.
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import GoalForm from "@/components/GoalForm";
import GoalResult from "@/components/GoalResult";
import GoalList from "@/components/GoalList";
import { RefineResponse, GoalRecord, fetchGoals } from "@/lib/api";

export default function Home() {
  const [currentResult, setCurrentResult] = useState<RefineResponse | null>(null);
  const [currentRawGoal, setCurrentRawGoal] = useState<string>("");
  const [goals, setGoals] = useState<GoalRecord[]>([]);
  const [goalsLoading, setGoalsLoading] = useState(true);

  const loadGoals = useCallback(async () => {
    try {
      const data = await fetchGoals();
      setGoals(data);
    } catch (err) {
      console.error("Failed to load goals:", err);
    } finally {
      setGoalsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadGoals();
  }, [loadGoals]);

  const handleResult = (result: RefineResponse, rawGoal: string) => {
    setCurrentResult(result);
    setCurrentRawGoal(rawGoal);
    // Scroll to result
    setTimeout(() => {
      document.getElementById("result-section")?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  };

  const handleSaved = () => {
    loadGoals(); // Refresh the list after saving
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">
              🎯 AI Goal Coach
            </h1>
            <p className="text-xs text-gray-400 mt-0.5">
              Powered by Gemini 1.5 Flash · Structured JSON mode
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-50 px-3 py-1.5 rounded-full border border-gray-200">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            API Connected
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* Left column */}
          <div className="space-y-6">
            {/* Intro */}
            <div className="bg-indigo-600 text-white rounded-2xl p-6">
              <h2 className="text-xl font-bold mb-2">
                Turn vague aspirations into action plans
              </h2>
              <p className="text-indigo-100 text-sm leading-relaxed">
                Type any goal — even a rough, messy one. The AI will transform it 
                into a SMART goal with measurable key results.
              </p>
            </div>

            {/* Goal input form */}
            <GoalForm onResult={handleResult} />

            {/* AI Result */}
            {currentResult && currentResult.success && (
              <div id="result-section">
                <GoalResult
                  result={currentResult}
                  rawGoal={currentRawGoal}
                  onSaved={handleSaved}
                />
              </div>
            )}
          </div>

          {/* Right column — saved goals */}
          <div>
            <GoalList goals={goals} loading={goalsLoading} />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-xs text-gray-400">
          AI Goal Coach · Built with FastAPI + Next.js + Gemini AI · 
          Telemetry logged to <code className="bg-gray-100 px-1 py-0.5 rounded">backend/logs/telemetry.jsonl</code>
        </footer>
      </div>
    </main>
  );
}
