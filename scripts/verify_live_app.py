"""Run a real local-model quiz through Streamlit's interaction test harness."""
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streamlit.testing.v1 import AppTest
from generator import check_server
from quiz import results_json
from settings import Settings


def button(app, label):
    return next(b for b in app.button if b.label == label)


if not check_server(Settings.from_env())[0]:
    raise SystemExit("Start llama-server and wait for readiness first.")

started = time.monotonic()
app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()
assert not app.exception
app.radio(key="mode").set_value("AI mode").run()
app.text_input(key="topic").set_value(
    "Interpreting a fictional property campaign: viewing conversion and matching listings to explicit buyer constraints").run()
app.select_slider(key="count").set_value(2).run()
button(app, "Generate quiz").click().run()
assert not app.exception
assert not app.error, [error.value for error in app.error]
assert app.session_state.page == "quiz"
session = app.session_state.quiz_session
assert session.reviewed
assert all(q.question_id and q.options_id and q.explanation_id for q in session.quiz.questions)
assert session.quiz.title_id
assert any(session.quiz.questions[0].question_id in c.value for c in app.caption)
answers = [q.correct_index if i == 0 else (q.correct_index + 1) % 4
           for i, q in enumerate(session.quiz.questions)]
for radio, answer in zip(app.radio, answers):
    radio.set_value(answer)
button(app, "Submit answers").click().run()
assert not app.exception
assert app.session_state.page == "results"
assert any(session.quiz.questions[0].explanation_id in c.value for c in app.caption)
assert len(app.get("download_button")) == 1
payload = json.loads(results_json(session, app.session_state.submitted_answers))
assert payload["score"] == 1 and payload["total"] == 2
payload["verification"] = {
    "method": "Streamlit AppTest with real local-model API calls; no model stub",
    "elapsed_seconds": round(time.monotonic() - started, 2),
    "answer_selection": "One correct and one deliberately wrong answer selected programmatically.",
    "visual_browser_verification": False,
}
(ROOT / "examples/bilingual-app-check.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("PASS: real bilingual AI generation, English/Indonesian display, 1/2 scoring and results download.")
