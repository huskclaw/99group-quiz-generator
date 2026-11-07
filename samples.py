"""Three reviewed sample quizzes; no network or model is needed."""
import json
from pathlib import Path

from quiz import Quiz, QuizSession, shuffled, validate_request

DATA = json.loads((Path(__file__).resolve().parent / "data" / "samples.json").read_text(encoding="utf-8"))
TOPICS = {item["id"]: item for item in DATA}


def sample_quiz(topic_id: str, count: int) -> QuizSession:
    item = TOPICS[topic_id]
    validate_request(item["title"], count)
    quiz = Quiz.model_validate({"title": item["title"], "questions": item["questions"][:count]})
    return QuizSession(shuffled(quiz), item["title"], "Sample · curated offline quiz")
