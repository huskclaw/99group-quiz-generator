"""Repeat the final submission's real Streamlit flows; requires local llama-server."""
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


def run_case(name, topic, notes, count):
    started = time.monotonic()
    app = AppTest.from_file(str(ROOT / 'app.py'), default_timeout=600).run()
    app.radio(key='mode').set_value('AI mode').run()
    app.text_input(key='topic').set_value(topic).run()
    app.text_area(key='notes').set_value(notes).run()
    app.select_slider(key='count').set_value(count).run()
    button(app, 'Generate quiz').click().run()
    assert not app.exception, app.exception
    assert not app.error, [e.value for e in app.error]
    assert app.session_state.page == 'quiz'
    session = app.session_state.quiz_session
    assert len(session.quiz.questions) == count and session.reviewed
    assert session.source_notes == notes
    button(app, 'Submit answers').click().run()
    assert any('Answer every' in w.value for w in app.warning)
    answers = [q.correct_index if i else (q.correct_index + 1) % 4
               for i, q in enumerate(session.quiz.questions)]
    for radio, answer in zip(app.radio, answers):
        radio.set_value(answer)
    button(app, 'Submit answers').click().run()
    assert not app.exception and app.session_state.page == 'results'
    assert len(app.get('download_button')) == 1
    assert all(any(q.explanation_id in c.value for c in app.caption)
               for q in session.quiz.questions)
    payload = json.loads(results_json(session, answers))
    assert payload['score'] == count - 1
    payload['audit_input'] = {'topic': topic, 'reference_notes': notes, 'count': count}
    payload['verification'] = {
        'method': 'Fresh Streamlit AppTest; real local-model API, no mocks',
        'elapsed_seconds': round(time.monotonic() - started, 2),
        'topic_characters': len(topic), 'notes_characters': len(notes),
        'answer_selection': 'First answer deliberately wrong; remaining keys selected programmatically.',
        'visual_browser_verification': False,
    }
    output = ROOT / 'examples' / f'final-audit-{name}.json'
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'PASS {name}: {count} questions, score {count-1}/{count}, '
          f'{payload["verification"]["elapsed_seconds"]} seconds', flush=True)


if __name__ == '__main__':
    assert check_server(Settings.from_env())[0], 'Start start-llama.ps1 first.'
    run_case('evergreen', 'Calculating hypothetical property rental yield using an explicitly stated annual-rent divided by purchase-price formula', '', 2)
    topic = ('Reading a fictional Jakarta property briefing dated 7 November 2026: '
             'calculate changes, distinguish asking from sale prices, and respect the dataset scope')
    topic += ' ' + 'carefully'[:160 - len(topic) - 1]
    assert len(topic) == 160
    notes = (ROOT / 'examples/long-training-briefing.txt').read_text(encoding='utf-8')
    assert len(notes) == 3000
    run_case('dated-notes', topic, notes, 5)
