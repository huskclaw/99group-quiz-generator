"""99 Learn: local employee quiz generation and practice."""
import html
import hashlib
from pathlib import Path
import uuid

import streamlit as st

from generator import GenerationError, check_server, generate_quiz
from quiz import results_json, score_quiz
from samples import TOPICS, sample_quiz
from settings import Settings
from input_rules import MAX_NOTES_CHARS, MAX_TOPIC_CHARS, OUTSIDE_TOPIC_WARNING, check_topic

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


def show_question(question):
    st.write(question.question)
    if getattr(question, 'question_id', None):
        st.caption(question.question_id)


def option_label(n, question):
    english = f"{'ABCD'[n]}. {question.options[n]}"
    localized = getattr(question, 'options_id', None)
    return english + ('  \n' + localized[n] if localized else '')


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
            topic = st.text_input("What would you like to learn?", max_chars=MAX_TOPIC_CHARS,
                                  placeholder="e.g. Top skills of a property agent in 2026", key="topic")
            st.caption("Property, employee skills and company learning. English or Bahasa Indonesia input; every quiz displays both languages.")
            input_error, allow_off_topic = None, False
            if len(topic.strip()) >= 3:
                try:
                    if check_topic(topic) == 'outside':
                        st.warning(OUTSIDE_TOPIC_WARNING)
                        consent_key = hashlib.sha256(topic.casefold().encode()).hexdigest()[:12]
                        allow_off_topic = st.checkbox('Continue anyway', key='fun_' + consent_key)
                        if not allow_off_topic:
                            input_error = 'Choose a relevant topic or tick Continue anyway.'
                except ValueError as exc:
                    input_error = str(exc)
                    st.error(input_error)
            with st.expander("Add source notes (optional)"):
                notes = st.text_area("Reference notes", max_chars=MAX_NOTES_CHARS, height=170,
                                     placeholder="Paste a dated market briefing or article excerpt here.", key="notes")
                st.caption("For current market updates, include dated facts here. URLs alone are not fetched. Notes stay in this session and go only to your local model.")
                st.caption('Up to 3,000 characters, with a model-token budget check before every request.')
            st.caption("Without source notes, quizzes use general knowledge and hypothetical examples. This app has no live news feed.")
        else:
            topic_id = st.selectbox("Pick a topic", list(TOPICS),
                                    format_func=lambda key: TOPICS[key]["title"], key="sample_topic")
            st.caption(TOPICS[topic_id]["description"])
            st.info("Ready-made questions. No model or internet connection needed.", icon="⚡")
        count = st.select_slider("Number of questions", options=[1, 2, 3, 4, 5], value=5, key="count")
        st.caption("Four choices per question. One correct answer. About 2–4 minutes.")
        if mode == "AI mode" and not ready:
            st.warning('The local model is unavailable or busy. Refresh its status when the current request finishes. If it is frozen, restart only llama-server; Sample mode remains available.')
        if st.button("Generate quiz" if mode == "AI mode" else "Start sample quiz", type="primary",
                     width="stretch", disabled=mode == "AI mode" and (not ready or bool(input_error))):
            try:
                if mode == "Sample mode":
                    session = sample_quiz(topic_id, count)
                else:
                    with st.status('Preparing bilingual quiz', expanded=False) as generation_status:
                        session = generate_quiz(topic, count, notes, settings,
                            allow_off_topic=allow_off_topic, progress=lambda label: generation_status.update(label=label))
                        generation_status.update(label='Quiz ready', state='complete')
                load_quiz(session)
                st.rerun()
            except (ValueError, GenerationError) as exc:
                if isinstance(exc, GenerationError):
                    model_status.clear()
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
    if not all(getattr(q, 'question_id', None) for q in quiz.questions):
        st.info('This quiz was created before the bilingual update. Create a new quiz to see English and Indonesian together.')
    st.caption(f"{session.source} · {len(quiz.questions)} questions · " +
               ("AI quality review passed" if session.reviewed else "Prepared sample"))
    if getattr(session, 'topic_scope', 'work') == 'exploratory':
        st.info('Outside work topics · continued by your choice.')
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
                    show_question(q)
                    answers.append(st.radio(f"Answer for question {i + 1}", list(range(4)), index=None,
                        format_func=lambda n, question=q: option_label(n, question),
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
                show_question(q)
                for j, option in enumerate(q.options):
                    state = "correct" if j == q.correct_index else "wrong" if j == selected else ""
                    label = " · Correct answer / Jawaban benar" if j == q.correct_index else ""
                    label += " · Your answer / Jawaban Anda" if j == selected else ""
                    localized = getattr(q, 'options_id', None)
                    translation = f'<div class="translation" lang="id">{html.escape(localized[j])}</div>' if localized else ''
                    st.html(f'<div class="result-option {state}"><span lang="en">{"ABCD"[j]}. {html.escape(option)}</span>{translation}<strong>{label}</strong></div>')
                st.write("**Why:** " + q.explanation)
                if getattr(q, 'explanation_id', None):
                    st.caption('Alasan: ' + q.explanation_id)
        st.download_button("Download my results", results_json(session, answers),
                           file_name="99-learn-results.json", mime="application/json", width="stretch")
        if st.button("Create another quiz", type="primary", width="stretch"):
            st.session_state.page = "create"
            st.rerun()

st.html('''<div class="footer"><span>99 Learn · Local learning prototype</span>
<span>Inspired by 99 Group · Built for this assessment</span></div>''')
