"""99 Learn: local employee quiz generation and practice."""
import html
from pathlib import Path
import uuid

import streamlit as st

from generator import GenerationError, check_server, generate_quiz
from quiz import results_json, score_quiz
from samples import TOPICS, sample_quiz
from settings import Settings

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="99 Learn · A little learning, every day", page_icon="🏡", layout="centered")
st.html("<style>" + (ROOT / "assets/style.css").read_text(encoding="utf-8") + "</style>")


@st.cache_data(ttl=15, show_spinner=False)
def model_status(settings):
    return check_server(settings)


def load_quiz(session):
    # A new widget namespace prevents answers carrying across different quizzes.
    old_id = st.session_state.get("quiz_id", "")
    for key in list(st.session_state):
        if old_id and key.startswith(f"answer_{old_id}_"):
            del st.session_state[key]
    st.session_state.update(quiz_session=session, quiz_id=uuid.uuid4().hex,
                            submitted_answers=None, page="quiz")


def steps(active):
    parts = []
    for i, label in enumerate(("Create", "Take quiz", "Review")):
        if i:
            parts.append('<span class="connector"></span>')
        parts.append(f'<span class="step {"active" if i == active else ""}"><b>{i + 1}</b>{label}</span>')
    st.html('<div class="steps">' + "".join(parts) + "</div>")


st.html('''<div class="brandbar"><div class="brand"><span class="brand-symbol">99</span>
<div><div class="brand-name">Learn</div><div class="brand-sub">A little learning, every day.</div></div></div>
<span class="internal">FOR 99 GROUP TEAMS</span></div>''')

page = st.session_state.get("page", "create")

if page == "create":
    st.html('''<div class="hero"><div class="eyebrow">Stay curious. Stay ahead.</div>
    <h1>Your next learning moment<br>starts with a question.</h1>
    <p>Turn a topic into a quick quiz. Sharpen your property knowledge,
    explore something new, and learn a little along the way.</p>
    <div class="hero-tags"><span>1–5 questions</span><span>Made for your team</span><span>Instant feedback</span></div></div>''')
    steps(0)
    try:
        settings = Settings.from_env()
        ready, status = model_status(settings)
    except ValueError as exc:
        settings, ready, status = None, False, "Check local model settings"
        st.warning(str(exc))
    with st.container(border=True):
        st.subheader("Make it your own")
        st.caption("Choose how you want to learn today.")
        mode = st.radio("Quiz mode", ["AI mode", "Sample mode"],
                        index=0 if ready else 1, horizontal=True, key="mode")
        st.html(f'<div class="status"><span class="dot {"" if ready else "off"}"></span>{html.escape(status)} · runs on your computer</div>')
        if st.button("Refresh model status", type="tertiary"):
            model_status.clear()
            st.rerun()
        if mode == "AI mode":
            topic = st.text_input("What would you like to learn?", max_chars=160,
                                  placeholder="e.g. Top skills of a property agent in 2026", key="topic")
            st.caption("Try agent skills, property marketing, or a topic of your own.")
            with st.expander("Add source notes (optional)"):
                notes = st.text_area("Reference notes", max_chars=6000, height=170,
                                     placeholder="Paste a dated market briefing or article excerpt here.", key="notes")
                st.caption("For current market updates, include dated facts here. URLs alone are not fetched. Notes stay in this session and go only to your local model.")
            st.caption("Without source notes, quizzes use general knowledge and hypothetical examples. This app has no live news feed.")
        else:
            topic_id = st.selectbox("Pick a topic", list(TOPICS),
                                    format_func=lambda key: TOPICS[key]["title"], key="sample_topic")
            st.caption(TOPICS[topic_id]["description"])
            st.info("Ready-made questions. No model or internet connection needed.", icon="⚡")
        count = st.select_slider("Number of questions", options=[1, 2, 3, 4, 5], value=5, key="count")
        st.caption("Four choices per question. One correct answer. About 2–4 minutes.")
        if mode == "AI mode" and not ready:
            st.warning("Start the local model with start-llama.ps1, then refresh its status. Sample mode is ready now.")
        if st.button("Generate quiz" if mode == "AI mode" else "Start sample quiz", type="primary",
                     width="stretch", disabled=mode == "AI mode" and not ready):
            try:
                if mode == "Sample mode":
                    session = sample_quiz(topic_id, count)
                else:
                    with st.spinner("Writing your quiz and checking every answer…"):
                        session = generate_quiz(topic, count, notes, settings)
                load_quiz(session)
                st.rerun()
            except (ValueError, GenerationError) as exc:
                st.error(str(exc))
        if st.session_state.get("quiz_session"):
            if st.button("Return to my quiz", width="stretch"):
                st.session_state.page = "results" if st.session_state.submitted_answers is not None else "quiz"
                st.rerun()
    st.html('''<div class="empty"><div class="empty-icon">✦</div><h3>Small quizzes. Useful discoveries.</h3>
    <p>Answer a few thoughtful questions, then see your score and the reason behind every answer.</p></div>''')

else:
    session = st.session_state.quiz_session
    quiz = session.quiz
    steps(1 if page == "quiz" else 2)
    st.title(quiz.title)
    st.caption(f"{session.source} · {len(quiz.questions)} questions · " +
               ("AI quality review passed" if session.reviewed else "Prepared sample"))
    if session.source.startswith("Sample"):
        sample = next(item for item in TOPICS.values() if item["title"] == session.topic)
        st.info(sample["briefing"], icon="📖")
    elif session.has_notes:
        with st.expander("Source notes for this quiz", expanded=True):
            st.text(session.source_notes)
    else:
        st.caption("General knowledge and hypothetical scenarios; no live market data was retrieved.")
    if page == "quiz":
        st.caption("Choose one answer for every question. Answers are revealed after you submit.")
        with st.form("quiz_answers"):
            answers = []
            for i, q in enumerate(quiz.questions):
                with st.container(border=True):
                    st.caption(f"QUESTION {i + 1} OF {len(quiz.questions)}")
                    st.write(q.question)
                    answers.append(st.radio(f"Answer for question {i + 1}", list(range(4)), index=None,
                        format_func=lambda n, options=q.options: f"{'ABCD'[n]}. {options[n]}",
                        key=f"answer_{st.session_state.quiz_id}_{i}", label_visibility="collapsed"))
            if st.form_submit_button("Submit answers", type="primary", width="stretch"):
                try:
                    score_quiz(quiz, answers)
                    st.session_state.submitted_answers = answers
                    st.session_state.page = "results"
                    st.rerun()
                except ValueError as exc:
                    st.warning(str(exc))
        if st.button("← Back to quiz setup"):
            st.session_state.page = "create"
            st.rerun()
    else:
        answers = st.session_state.submitted_answers
        score = score_quiz(quiz, answers)
        total = len(quiz.questions)
        message = "A perfect learning moment!" if score == total else "Every question is a chance to learn."
        st.html(f'<div class="scorecard"><div class="number">{score}<span style="font-size:1.7rem;color:#6f8cb4"> / {total}</span></div><h2>{message}</h2><p>{round(score / total * 100)}% correct · Your answer review is below</p></div>')
        for i, (q, selected) in enumerate(zip(quiz.questions, answers)):
            with st.container(border=True):
                st.caption(f"QUESTION {i + 1} · {'CORRECT' if selected == q.correct_index else 'KEEP LEARNING'}")
                st.write(q.question)
                for j, option in enumerate(q.options):
                    state = "correct" if j == q.correct_index else "wrong" if j == selected else ""
                    label = " · Correct answer" if j == q.correct_index else ""
                    label += " · Your answer" if j == selected else ""
                    st.html(f'<div class="result-option {state}">{"ABCD"[j]}. {html.escape(option)}<strong>{label}</strong></div>')
                st.write("**Why:** " + q.explanation)
        st.download_button("Download my results", results_json(session, answers),
                           file_name="99-learn-results.json", mime="application/json", width="stretch")
        if st.button("Create another quiz", type="primary", width="stretch"):
            st.session_state.page = "create"
            st.rerun()

st.html('''<div class="footer"><span>99 Learn · Local learning prototype</span>
<span>Inspired by 99 Group · Built for this assessment</span></div>''')
