"""Exercise the same local generation path as Streamlit; save inspectable evidence."""
import argparse
import json
from pathlib import Path
import time

from generator import GenerationError, check_server, generate_quiz
from quiz import results_json
from settings import Settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topic", default="Top skills of a property agent in 2026")
    parser.add_argument("--count", type=int, choices=range(1, 6), default=5)
    parser.add_argument("--notes-file", type=Path)
    parser.add_argument('--allow-off-topic', action='store_true', help='Explicitly allow an exploratory fun topic.')
    parser.add_argument("--output", type=Path, default=Path("examples/live-quiz.json"))
    args = parser.parse_args()
    settings = Settings.from_env()
    ready, status = check_server(settings)
    if not ready:
        parser.exit(1, status + ". Start start-llama.ps1 first.\n")
    notes = args.notes_file.read_text(encoding="utf-8") if args.notes_file else ""
    started = time.monotonic()
    try:
        session = generate_quiz(args.topic, args.count, notes, settings,
            allow_off_topic=args.allow_off_topic, progress=lambda label: print(label, flush=True))
    except (GenerationError, ValueError) as exc:
        parser.exit(1, str(exc) + "\n")
    payload = json.loads(results_json(session, [q.correct_index for q in session.quiz.questions]))
    payload["verification"] = {"elapsed_seconds": round(time.monotonic() - started, 2),
        "answer_selection": "Correct keys selected programmatically to verify scoring; not an employee attempt."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(session.quiz.questions)} questions, AI review passed; evidence: {args.output}")


if __name__ == "__main__":
    main()
