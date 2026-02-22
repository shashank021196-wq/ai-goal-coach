/**
 * components/GoalResult.tsx
 * =========================
 * Displays the AI's structured response:
 * - SMART refined goal
 * - Key results list
 * - Confidence score badge
 * - Telemetry summary (latency + tokens)
 * - Save button
 */

"use client";

import { useState } from "react";
import { RefineResponse, saveGoal } from "@/lib/api";

interface GoalResultProps {
  result: RefineResponse;
  rawGoal: string;
  onSaved: () => void;
}

export default function GoalResult({ result, rawGoal, onSaved }: GoalResultProps) {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  if (!result.data) return null;

  const { refined_goal, key_results, confidence_score } = result.data;

  const confidenceColor =
    confidence_score >= 8 ? "bg-green-100 text-green-800" :
    confidence_score >= 5 ? "bg-yellow-100 text-yellow-800" :
    "bg-red-100 text-red-800";

  const confidenceLabel =
    confidence_score >= 8 ? "High confidence" :
    confidence_score >= 5 ? "Moderate confidence" :
    "Low confidence";

  const handleSave = async () => {
    setSaving(true);
    setSaveError(null);
    try {
      await saveGoal(rawGoal, result.data!);
      setSaved(true);
      onSaved(); // trigger parent to refresh goals list
    } catch (err: unknown) {
      setSaveError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">✅ Refined Goal</h2>
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${confidenceColor}`}>
          {confidenceLabel} ({confidence_score}/10)
        </span>
      </div>

      {/* SMART Goal */}
      <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4">
        <p className="text-indigo-900 font-medium leading-relaxed">{refined_goal}</p>
      </div>

      {/* Key Results */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
          Key Results
        </h3>
        <ul className="space-y-2">
          {key_results.map((kr, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="mt-0.5 flex-shrink-0 w-6 h-6 rounded-full bg-indigo-100 
                             text-indigo-700 text-xs font-bold flex items-center justify-center">
                {i + 1}
              </span>
              <span className="text-sm text-gray-700 leading-relaxed">{kr}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Telemetry panel — this is the observability demo */}
      {(result.latency_ms || result.prompt_tokens) && (
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-3">
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
            📊 Telemetry (also logged to backend console)
          </p>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-lg font-bold text-gray-800">
                {result.latency_ms ? `${Math.round(result.latency_ms)}ms` : "—"}
              </p>
              <p className="text-xs text-gray-500">Latency</p>
            </div>
            <div>
              <p className="text-lg font-bold text-gray-800">
                {result.prompt_tokens ?? "—"}
              </p>
              <p className="text-xs text-gray-500">Prompt Tokens</p>
            </div>
            <div>
              <p className="text-lg font-bold text-gray-800">
                {result.completion_tokens ?? "—"}
              </p>
              <p className="text-xs text-gray-500">Completion Tokens</p>
            </div>
          </div>
        </div>
      )}

      {/* Save button */}
      {saveError && (
        <p className="text-sm text-red-600">⚠️ {saveError}</p>
      )}

      <button
        onClick={handleSave}
        disabled={saving || saved}
        className="w-full py-2.5 px-6 rounded-xl font-medium transition
                   bg-green-600 text-white hover:bg-green-700
                   disabled:opacity-50 disabled:cursor-not-allowed
                   flex items-center justify-center gap-2"
      >
        {saved ? "✅ Saved!" : saving ? "Saving..." : "💾 Save This Goal"}
      </button>
    </div>
  );
}
