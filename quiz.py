"""Quiz contracts, deterministic scoring, answer shuffling and exports."""
import json
import re
import secrets
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from input_rules import MAX_NOTES_CHARS, MAX_TOPIC_CHARS, readable_text

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=700)]
Option = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


def normalized(value: str) -> str:
    return re.sub(r"[\W_]+", " ", unicodedata.normalize("NFKC", value).casefold()).strip()


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question: Text
    options: list[Option] = Field(min_length=4, max_length=4)
    correct_index: int = Field(ge=0, le=3)
    explanation: Text
    question_id: Text | None = None
    options_id: list[Option] | None = Field(default=None, min_length=4, max_length=4)
    explanation_id: Text | None = None

    @model_validator(mode="after")
    def distinct_options(self):
        choices = [normalized(option) for option in self.options]
        if len(set(choices)) != 4 or not all(choices):
            raise ValueError("Four distinct, nonempty options are required.")
        banned = {"all of the above", "none of the above", "all answers", "semua benar", "semua jawaban benar"}
        if any(choice in banned for choice in choices):
            raise ValueError("Each option must stand on its own.")
        translations = (self.question_id, self.options_id, self.explanation_id)
        if any(value is not None for value in translations):
            if not all(value is not None for value in translations):
                raise ValueError('All Indonesian question, option and explanation fields are required together.')
            if len(set(normalized(option) for option in self.options_id)) != 4:
                raise ValueError('Indonesian options must also be distinct.')
        return self


class Quiz(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: Title
    questions: list[Question] = Field(min_length=1, max_length=5)
    title_id: Title | None = None

    @model_validator(mode="after")
    def distinct_questions(self):
        stems = [normalized(q.question) for q in self.questions]
        if len(set(stems)) != len(stems):
            raise ValueError("Repeated questions are not allowed.")
        return self


class GeneratedQuestion(BaseModel):
    """Ask the model for answer text; derive indices in Python to avoid indexing mistakes."""
    model_config = ConfigDict(extra="forbid", strict=True)
    question: Text
    options: list[Option] = Field(min_length=4, max_length=4)
    correct_answer: Option
    explanation: Text
    question_id: Text
    options_id: list[Option] = Field(min_length=4, max_length=4)
    explanation_id: Text

    def to_question(self) -> Question:
        if self.options.count(self.correct_answer) != 1:
            raise ValueError("The correct answer must exactly match one option.")
        return Question(question=self.question, options=self.options,
                        correct_index=self.options.index(self.correct_answer), explanation=self.explanation,
                        question_id=self.question_id, options_id=self.options_id, explanation_id=self.explanation_id)


class GeneratedQuiz(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    title: Title
    questions: list[GeneratedQuestion] = Field(min_length=1, max_length=5)
    title_id: Title

    def to_quiz(self) -> Quiz:
        return Quiz(title=self.title, title_id=self.title_id, questions=[q.to_question() for q in self.questions])


@dataclass(frozen=True)
class QuizSession:
    quiz: Quiz
    topic: str
    source: str
    model: str = ""
    reviewed: bool = False
    has_notes: bool = False
    created_at: str = ""
    source_notes: str = ""
    topic_scope: str = "work"

    def __post_init__(self):
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))


def validate_request(topic: str, count: int, notes: str = "") -> str:
    topic = " ".join(topic.split())
    if not 3 <= len(topic) <= MAX_TOPIC_CHARS:
        raise ValueError("Enter a topic between 3 and 160 characters.")
    if type(count) is not int or not 1 <= count <= 5:
        raise ValueError("Choose between 1 and 5 questions.")
    if len(notes) > MAX_NOTES_CHARS:
        raise ValueError("Keep source notes within 3,000 characters. / Batasi catatan referensi hingga 3.000 karakter.")
    readable_text(topic, 'Topic / Topik')
    readable_text(notes, 'Reference notes / Catatan referensi')
    return topic


def shuffled(quiz: Quiz) -> Quiz:
    """Keep the answer attached to its option when changing positions."""
    questions = []
    for q in quiz.questions:
        order = list(range(4))
        secrets.SystemRandom().shuffle(order)
        questions.append(q.model_copy(update={"options": [q.options[i] for i in order],
            "options_id": [q.options_id[i] for i in order] if q.options_id is not None else None,
            "correct_index": order.index(q.correct_index)}))
    return quiz.model_copy(update={"questions": questions})


def score_quiz(quiz: Quiz, answers: list[int | None]) -> int:
    if len(answers) != len(quiz.questions) or any(type(a) is not int or not 0 <= a <= 3 for a in answers):
        raise ValueError("Answer every question before submitting.")
    return sum(answer == q.correct_index for q, answer in zip(quiz.questions, answers))


def results_json(session: QuizSession, answers: list[int]) -> str:
    score = score_quiz(session.quiz, answers)
    return json.dumps({
        "title": session.quiz.title, "title_id": getattr(session.quiz, 'title_id', None), "topic": session.topic,
        "topic_scope": getattr(session, 'topic_scope', 'work'),
        "languages": ["en", "id"] if all(getattr(q, 'question_id', None) for q in session.quiz.questions) else ["en"],
        "source": session.source, "model": session.model,
        "ai_quality_review": session.reviewed, "source_notes_provided": session.has_notes,
        "created_at": session.created_at, "score": score,
        "total": len(answers), "percentage": round(score / len(answers) * 100),
        "questions": [{**q.model_dump(), "selected_index": a, "is_correct": a == q.correct_index}
                      for q, a in zip(session.quiz.questions, answers)],
    }, ensure_ascii=False, indent=2)
