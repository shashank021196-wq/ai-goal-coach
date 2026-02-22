"""
services/logger.py
==================
Telemetry abstraction layer.

Every AI call gets wrapped here. This logs:
  - Timestamp
  - Input (raw goal)
  - Output (AI response)
  - Latency in milliseconds
  - Prompt token count
  - Completion token count
  - Estimated cost (rough, based on Gemini Flash pricing)

Logs are written to logs/telemetry.jsonl (one JSON object per line).
This format is easy to pipe into any log aggregator (Datadog, CloudWatch, etc.)
without changing this file.

To swap to a proper APM tool later (e.g., OpenTelemetry), 
you only need to change this one file.
"""

import json
import time
import os
from datetime import datetime, timezone
from pathlib import Path


# Ensure logs directory exists
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "telemetry.jsonl"

# Gemini Flash pricing (as of 2025, free tier - used for cost estimation only)
# Even on free tier, understanding token cost is good engineering practice
COST_PER_1K_PROMPT_TOKENS = 0.000075   # $0.075 per 1M input tokens
COST_PER_1K_COMPLETION_TOKENS = 0.0003  # $0.30 per 1M output tokens


def log_ai_call(
    raw_input: str,
    output: dict,
    latency_ms: float,
    prompt_tokens: int,
    completion_tokens: int,
    model: str = "gemini-1.5-flash",
    error: str = None
) -> None:
    """
    Write one telemetry record to logs/telemetry.jsonl.
    Called after every AI request, success or failure.
    """
    estimated_cost_usd = (
        (prompt_tokens / 1000) * COST_PER_1K_PROMPT_TOKENS +
        (completion_tokens / 1000) * COST_PER_1K_COMPLETION_TOKENS
    )

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "input": raw_input,
        "output": output,
        "latency_ms": round(latency_ms, 2),
        "tokens": {
            "prompt": prompt_tokens,
            "completion": completion_tokens,
            "total": prompt_tokens + completion_tokens
        },
        "estimated_cost_usd": round(estimated_cost_usd, 8),
        "error": error
    }

    # Print to console (visible in terminal during demo)
    print("\n" + "="*60)
    print("📊 TELEMETRY LOG")
    print("="*60)
    print(f"  Timestamp  : {record['timestamp']}")
    print(f"  Model      : {model}")
    print(f"  Input      : {raw_input[:80]}{'...' if len(raw_input) > 80 else ''}")
    print(f"  Latency    : {record['latency_ms']} ms")
    print(f"  Tokens     : {prompt_tokens} prompt + {completion_tokens} completion = {prompt_tokens + completion_tokens} total")
    print(f"  Est. Cost  : ${estimated_cost_usd:.8f} USD")
    if error:
        print(f"  ❌ Error   : {error}")
    else:
        print(f"  Confidence : {output.get('confidence_score', 'N/A')}/10")
    print("="*60 + "\n")

    # Write to file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


class Timer:
    """
    Simple context manager to time a block of code.
    
    Usage:
        with Timer() as t:
            result = call_something()
        print(t.elapsed_ms)
    """
    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000
