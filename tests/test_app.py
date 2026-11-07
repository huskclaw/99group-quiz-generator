from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import generator
from quiz import QuizSession
from samples import sample_quiz

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def button(app, label):
    return next(b for b in app.button if b.label == label)


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(generator, "check_server", lambda settings: (False, "Local model offline"))
    from streamlit import cache_data
    cache_data.clear()
    instance = AppTest.from_file(APP, default_timeout=15).run()
    assert not instance.exception
    return instance


def test_offline_defaults_to_samples_and_blocks_ai(app):
    assert app.radio(key="mode").value == "Sample mode"
    app.radio(key="mode").set_value("AI mode").run()
    assert button(app, "Generate quiz").disabled


def test_sample_full_flow_and_reset(app):
    button(app, "Start sample quiz").click().run()
    assert not app.exception
    assert len(app.radio) == 5
    assert all(r.value is None for r in app.radio)
    button(app, "Submit answers").click().run()
    assert any("Answer every" in warning.value for warning in app.warning)
    quiz = app.session_state.quiz_session.quiz
    for radio, q in zip(app.radio, quiz.questions):
        radio.set_value(q.correct_index)
    button(app, "Submit answers").click().run()
    assert not app.exception
    assert app.session_state.page == "results"
    assert len(app.get("download_button")) == 1
    button(app, "Create another quiz").click().run()
    app.selectbox(key="sample_topic").set_value("jakarta-market").run()
    app.select_slider(key="count").set_value(1).run()
    button(app, "Start sample quiz").click().run()
    assert len(app.radio) == 1
    assert app.radio[0].value is None
    assert "FICTIONAL" in app.info[0].value


def test_ai_flow_and_preserves_old_quiz_on_failure(app, monkeypatch):
    monkeypatch.setattr(generator, "check_server", lambda settings: (True, "Local model ready"))
    button(app, "Refresh model status").click().run()
    app.radio(key="mode").set_value("AI mode").run()
    app.text_input(key="topic").set_value("Agent skills").run()
    candidate = sample_quiz("agent-skills", 5)
    session = QuizSession(candidate.quiz, "Agent skills", "AI generated · local Gemma", "gemma-4-12b", True)
    monkeypatch.setattr(generator, "generate_quiz", lambda *args: session)
    button(app, "Generate quiz").click().run()
    assert not app.exception
    assert app.session_state.quiz_session.reviewed
    button(app, "← Back to quiz setup").click().run()
    def fail(*args):
        raise generator.GenerationError("Model unavailable; use Sample mode.")
    monkeypatch.setattr(generator, "generate_quiz", fail)
    button(app, "Generate quiz").click().run()
    assert app.error
    assert app.session_state.quiz_session == session
    button(app, "Return to my quiz").click().run()
    assert app.session_state.page == "quiz"
