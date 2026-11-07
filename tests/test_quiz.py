import json

import pytest
from pydantic import ValidationError

from quiz import GeneratedQuestion, Question, Quiz, results_json, score_quiz, shuffled, validate_request
from samples import TOPICS, sample_quiz
from settings import Settings


@pytest.mark.parametrize("topic_id", list(TOPICS))
@pytest.mark.parametrize("count", [1, 2, 3, 4, 5])
def test_samples_and_scoring(topic_id, count):
    session = sample_quiz(topic_id, count)
    assert len(session.quiz.questions) == count
    correct = [q.correct_index for q in session.quiz.questions]
    assert score_quiz(session.quiz, correct) == count
    assert score_quiz(session.quiz, [(a + 1) % 4 for a in correct]) == 0
    payload = json.loads(results_json(session, correct))
    assert payload["percentage"] == 100
    assert payload["source"].startswith("Sample")
    assert not payload["ai_quality_review"]
    assert "source_notes" not in payload


def test_shuffle_preserves_answer_text():
    quiz = sample_quiz("agent-skills", 5).quiz
    mixed = shuffled(quiz)
    for old, new in zip(quiz.questions, mixed.questions):
        assert old.options[old.correct_index] == new.options[new.correct_index]
        assert old.explanation == new.explanation


@pytest.mark.parametrize("answers", [[None] * 5, [0], [True] * 5, [-1] * 5, [4] * 5])
def test_incomplete_and_invalid_answers(answers):
    with pytest.raises(ValueError, match="Answer every"):
        score_quiz(sample_quiz("agent-skills", 5).quiz, answers)


def test_duplicate_choices_and_questions_rejected():
    q = TOPICS["agent-skills"]["questions"][0].copy()
    q["options"] = ["Hello!", " hello ", "Third", "Fourth"]
    with pytest.raises(ValidationError):
        Question.model_validate(q)
    q = TOPICS["agent-skills"]["questions"][0]
    with pytest.raises(ValidationError):
        Quiz.model_validate({"title": "Repeated", "questions": [q, q]})


def test_generated_answer_text_must_match_an_option():
    q = TOPICS["agent-skills"]["questions"][0]
    data = {k: v for k, v in q.items() if k != "correct_index"}
    generated = GeneratedQuestion(**data, correct_answer=q["options"][q["correct_index"]])
    assert generated.to_question().correct_index == q["correct_index"]
    with pytest.raises(ValueError, match="exactly match"):
        GeneratedQuestion(**data, correct_answer="An answer that is not among the options").to_question()


@pytest.mark.parametrize("topic,count,notes", [("", 5, ""), ("ab", 3, ""), ("Topic", 0, ""),
    ("Topic", 6, ""), ("Topic", True, ""), ("Topic", 3, "x" * 6001)])
def test_invalid_request(topic, count, notes):
    with pytest.raises(ValueError):
        validate_request(topic, count, notes)


@pytest.mark.parametrize("url", ["https://example.com/v1", "http://192.168.1.2/v1",
    "http://localhost/v1?x=1", "http://user:pass@localhost/v1", "http://localhost/other"])
def test_only_local_model_endpoints(url):
    with pytest.raises(ValueError):
        Settings(base_url=url)
