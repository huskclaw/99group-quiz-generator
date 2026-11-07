"""Optional integration evidence: real local API calls, never part of pytest."""
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import httpx
from generator import check_server, generate_quiz
from quiz import results_json
from settings import Settings

cases = [
    ("Top skills of a property agent in 2026", 5, "", "live-agent-skills.json"),
    ("Property market updates in Jakarta: interpret the supplied fictional briefing", 5,
     (ROOT / "examples/jakarta-briefing.txt").read_text(encoding="utf-8"), "live-jakarta.json"),
    ("A fun property floor-area puzzle using hypothetical dimensions", 1, "", "live-property-puzzle.json"),
]

settings = Settings.from_env()
ready, status = check_server(settings)
if not ready:
    raise SystemExit(status + ". Wait for llama-server to finish loading.")

for topic, count, notes, filename in cases:
    trace = []
    def record(response):
        response.read()
        body = response.json()
        entry = {"http_status": response.status_code}
        if body.get("choices"):
            choice = body["choices"][0]
            entry.update(finish_reason=choice.get("finish_reason"), content=choice["message"].get("content"))
        trace.append(entry)
        print(f"API response {len(trace)}: HTTP {entry['http_status']}; {entry.get('finish_reason')}", flush=True)
    started = time.monotonic()
    print(f"Checking {count} questions: {topic}", flush=True)
    try:
        with httpx.Client(timeout=httpx.Timeout(settings.timeout, connect=3), trust_env=False,
                          event_hooks={"response": [record]}) as client:
            session = generate_quiz(topic, count, notes, settings, client=client)
        payload = json.loads(results_json(session, [q.correct_index for q in session.quiz.questions]))
        payload["verification"] = {"elapsed_seconds": round(time.monotonic() - started, 2),
            "api_requests": len(trace), "reference_notes": notes,
            "quality_review": json.loads(trace[-1]["content"]),
            "answer_selection": "Correct keys selected programmatically to verify scoring; not an employee attempt."}
        (ROOT / "examples" / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"PASS: {filename}, {payload['verification']['elapsed_seconds']} seconds", flush=True)
    finally:
        trace_path = ROOT / "artifacts" / (filename.removesuffix(".json") + "-trace.json")
        trace_path.parent.mkdir(exist_ok=True)
        trace_path.write_text(json.dumps(trace, ensure_ascii=False, indent=2), encoding="utf-8")
