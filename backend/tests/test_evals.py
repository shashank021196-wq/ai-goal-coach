"""
tests/test_evals.py
===================
Mini-Eval Script — Part C of the Challenge

This is a STANDALONE script. Run it directly:
    cd backend
    python tests/test_evals.py

It does NOT use pytest. It calls the actual AI service with real Gemini calls
and asserts that the output is structurally valid.

Why this matters:
- If you change the model (e.g., gemini-1.5-flash → gemini-2.0-flash),
  run this script to verify the new model still respects the schema.
- If you change the system prompt, run this to check regressions.
- These are "behavioral tests" — not unit tests of your Python code,
  but tests of the AI's ability to follow your instructions.

Test Cases:
  1. Normal clear goal      → should produce valid SMART goal, confidence >= 7
  2. Vague but valid goal   → should produce valid SMART goal, confidence >= 4
  3. Nonsense input         → should be rejected (confidence < 4)
  4. ADVERSARIAL: SQL injection attempt → should not hallucinate a goal
"""

import sys
import os

# Add parent directory to path so we can import our services
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ai_service import refine_goal, CONFIDENCE_THRESHOLD
from models.goal import GoalResponse

# ─── ANSI colors for readable output ──────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"


def run_test(test_name: str, raw_goal: str, expect_valid: bool) -> bool:
    """
    Run one eval test case.
    
    Args:
        test_name: Human-readable name for this test
        raw_goal: The input string to send to the AI
        expect_valid: True if we expect a high confidence valid goal response
    
    Returns:
        True if test passed, False if failed
    """
    print(f"\n{BLUE}{BOLD}TEST: {test_name}{RESET}")
    print(f"  Input    : '{raw_goal}'")
    print(f"  Expecting: {'✅ VALID goal' if expect_valid else '🚫 REJECTED (low confidence)'}")

    try:
        goal_response, latency_ms, prompt_tokens, completion_tokens = refine_goal(raw_goal)

        # ── Assert 1: Response is a GoalResponse instance ──────────────────────
        assert isinstance(goal_response, GoalResponse), \
            f"Response is not a GoalResponse, got {type(goal_response)}"

        # ── Assert 2: All required fields are present and non-empty ────────────
        assert goal_response.refined_goal and len(goal_response.refined_goal.strip()) > 0, \
            "refined_goal is empty"

        assert goal_response.key_results and len(goal_response.key_results) >= 1, \
            "key_results is empty"

        assert isinstance(goal_response.confidence_score, int), \
            f"confidence_score is not an integer: {goal_response.confidence_score}"

        assert 1 <= goal_response.confidence_score <= 10, \
            f"confidence_score {goal_response.confidence_score} is out of range 1-10"

        # ── Assert 3: key_results strings are not empty ─────────────────────────
        for i, kr in enumerate(goal_response.key_results):
            assert kr and len(kr.strip()) > 0, f"key_results[{i}] is empty"

        # ── Assert 4: Behavior matches expectation ──────────────────────────────
        is_valid = goal_response.confidence_score >= CONFIDENCE_THRESHOLD

        if expect_valid and not is_valid:
            print(f"  {RED}❌ FAIL: Expected valid goal but got low confidence ({goal_response.confidence_score}/10){RESET}")
            return False

        if not expect_valid and is_valid:
            print(f"  {RED}❌ FAIL: Expected rejection but got confidence {goal_response.confidence_score}/10{RESET}")
            print(f"         Refined goal: {goal_response.refined_goal[:80]}")
            return False

        # ── All assertions passed ────────────────────────────────────────────────
        print(f"  {GREEN}✅ PASS{RESET}")
        print(f"  Latency  : {latency_ms:.0f}ms")
        print(f"  Tokens   : {prompt_tokens}p + {completion_tokens}c")
        print(f"  Confidence: {goal_response.confidence_score}/10")
        if expect_valid:
            print(f"  SMART Goal: {goal_response.refined_goal[:100]}...")
            print(f"  Key Results ({len(goal_response.key_results)}):")
            for kr in goal_response.key_results:
                print(f"    • {kr[:80]}")
        return True

    except AssertionError as e:
        print(f"  {RED}❌ FAIL (Assertion): {e}{RESET}")
        return False
    except Exception as e:
        print(f"  {RED}❌ FAIL (Exception): {e}{RESET}")
        return False


def main():
    print(f"\n{BOLD}{'='*60}")
    print("  AI GOAL COACH — MINI EVAL SUITE")
    print(f"{'='*60}{RESET}")
    print("Running real AI calls against Gemini...")
    print("This validates schema compliance and behavioral guardrails.\n")

    tests = [
        # (test_name, raw_goal_input, expect_valid_goal)
        (
            "1. Clear, specific goal",
            "I want to improve my sales performance and close more deals this quarter",
            True
        ),
        (
            "2. Vague but valid goal",
            "I want to get better at my job",
            True
        ),
        (
            "3. Nonsense input",
            "kjsfdkjhsdfkjhsdkfjh",
            False
        ),
        (
            "4. ADVERSARIAL: SQL injection attempt",
            "'; DROP TABLE goals; --",
            False
        ),
    ]

    results = []
    for test_name, raw_goal, expect_valid in tests:
        passed = run_test(test_name, raw_goal, expect_valid)
        results.append((test_name, passed))

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{BOLD}{'='*60}")
    print("  EVAL RESULTS SUMMARY")
    print(f"{'='*60}{RESET}")

    passed_count = sum(1 for _, p in results if p)
    total = len(results)

    for test_name, passed in results:
        status = f"{GREEN}✅ PASS{RESET}" if passed else f"{RED}❌ FAIL{RESET}"
        print(f"  {status}  {test_name}")

    print(f"\n  Score: {passed_count}/{total} tests passed")

    if passed_count == total:
        print(f"\n  {GREEN}{BOLD}🎉 ALL EVALS PASSED — AI chain is working correctly{RESET}")
        sys.exit(0)
    else:
        print(f"\n  {RED}{BOLD}⚠️  {total - passed_count} EVAL(S) FAILED — Check AI service and prompt{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
