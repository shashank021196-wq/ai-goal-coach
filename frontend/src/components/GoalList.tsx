/**
 * components/GoalList.tsx
 * =======================
 * Displays all saved goals from the database.
 * Receives goals as a prop from the parent page component.
 */

"use client";

import { GoalRecord } from "@/lib/api";

interface GoalListProps {
  goals: GoalRecord[];
  loading: boolean;
}

export default function GoalList({ goals, loading }: GoalListProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Saved Goals</h2>
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="h-20 bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  if (goals.length === 0) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Saved Goals</h2>
        <p className="text-sm text-gray-400 text-center py-6">
          No goals saved yet. Refine and save your first goal above!
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">
        Saved Goals
        <span className="ml-2 text-sm font-normal text-gray-400">
          ({goals.length})
        </span>
      </h2>

      <div className="space-y-4">
        {goals.map((goal) => (
          <div
            key={goal.id}
            className="border border-gray-100 rounded-xl p-4 hover:border-indigo-200 transition"
          >
            {/* Original input */}
            <p className="text-xs text-gray-400 mb-1">
              Original: &quot;{goal.raw_goal}&quot;
            </p>

            {/* Refined goal */}
            <p className="text-sm font-medium text-gray-900 mb-2">
              {goal.refined_goal}
            </p>

            {/* Key results — collapsed to 2 for list view */}
            <ul className="space-y-1 mb-3">
              {goal.key_results.slice(0, 2).map((kr, i) => (
                <li key={i} className="text-xs text-gray-600 flex gap-1.5">
                  <span className="text-indigo-400">→</span>
                  {kr}
                </li>
              ))}
              {goal.key_results.length > 2 && (
                <li className="text-xs text-gray-400">
                  +{goal.key_results.length - 2} more key results
                </li>
              )}
            </ul>

            {/* Meta */}
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-400">
                {new Date(goal.created_at).toLocaleDateString("en-IN", {
                  day: "numeric",
                  month: "short",
                  year: "numeric"
                })}
              </span>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                goal.confidence_score >= 8 ? "bg-green-100 text-green-700" :
                goal.confidence_score >= 5 ? "bg-yellow-100 text-yellow-700" :
                "bg-red-100 text-red-700"
              }`}>
                {goal.confidence_score}/10
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
