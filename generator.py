"""Local llama.cpp adapter with constrained output and a separate quality review."""
import json
from contextlib import nullcontext
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from quiz import GeneratedQuiz, Quiz, QuizSession, shuffled, validate_request
from settings import Settings

PROMPTS = Path(__file__).resolve().parent / "prompts"


class GenerationError(Exception):
    """A safe message that can be displayed without raw server output."""


class QuestionAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question_index: int = Field(ge=0, le=4)
    reason: str = Field(min_length=10, max_length=500)
    criterion_is_explicit: bool
    defensible_indices: list[int] = Field(min_length=0, max_length=4)


class Review(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    checks: list[QuestionAudit] = Field(min_length=1, max_length=5)
    approved: bool
    issues: list[str] = Field(max_length=5)


def review_passes(review: Review, quiz: Quiz) -> bool:
    checks = {check.question_index: check for check in review.checks}
    if len(checks) != len(quiz.questions) or len(review.checks) != len(quiz.questions):
        return False
    return review.approved and not review.issues and all(
        i in checks and checks[i].criterion_is_explicit
        and checks[i].defensible_indices == [q.correct_index]
        for i, q in enumerate(quiz.questions))


def user_prompt(topic: str, count: int, notes: str = "") -> str:
    topic = validate_request(topic, count, notes)
    return (PROMPTS / "user.txt").read_text(encoding="utf-8").format(
        count=count, topic_json=json.dumps(topic, ensure_ascii=False),
        notes_json=json.dumps(notes, ensure_ascii=False))


def check_server(settings: Settings) -> tuple[bool, str]:
    try:
        with httpx.Client(timeout=2, trust_env=False) as client:
            health = client.get(settings.base_url.removesuffix("/v1") + "/health")
            if health.status_code == 503:
                return False, "Model is loading"
            health.raise_for_status()
            models = client.get(settings.base_url + "/models")
            models.raise_for_status()
            if settings.model not in [m["id"] for m in models.json()["data"]]:
                return False, "Configured model is not loaded"
        return True, "Local model ready"
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return False, "Local model offline"


def _completion(client, settings, messages, schema, name, max_tokens):
    response = client.post(settings.base_url + "/chat/completions", json={
        "model": settings.model, "messages": messages,
        "response_format": {"type": "json_schema", "json_schema": {
            "name": name, "strict": True, "schema": schema}},
        "temperature": 0.7, "top_p": 0.95, "top_k": 64,
        "max_tokens": max_tokens, "stream": False, "cache_prompt": False,
        "chat_template_kwargs": {"enable_thinking": False},
    })
    response.raise_for_status()
    choice = response.json()["choices"][0]
    if choice.get("finish_reason") != "stop":
        raise ValueError("Incomplete response")
    content = choice["message"]["content"]
    if not isinstance(content, str):
        raise ValueError("Missing JSON text")
    return content


def generate_quiz(topic: str, count: int, notes: str = "", settings: Settings | None = None,
                  *, client: httpx.Client | None = None) -> QuizSession:
    settings = settings or Settings.from_env()
    topic = validate_request(topic, count, notes)
    prompt = user_prompt(topic, count, notes)
    schema = GeneratedQuiz.model_json_schema()
    schema["properties"]["questions"].update(minItems=count, maxItems=count)
    feedback = ""
    context = nullcontext(client) if client is not None else httpx.Client(
        timeout=httpx.Timeout(settings.timeout, connect=3), trust_env=False)
    try:
        with context as local_client:
            for attempt in range(2):
                try:
                    raw = _completion(local_client, settings, [
                        {"role": "system", "content": (PROMPTS / "system.txt").read_text(encoding="utf-8")},
                        {"role": "user", "content": prompt + feedback},
                    ], schema, "quiz", 2600)
                    quiz = GeneratedQuiz.model_validate_json(raw).to_quiz()
                    if len(quiz.questions) != count:
                        raise ValueError("Incorrect question count")
                    review_input = json.dumps({"topic": topic, "reference_notes": notes,
                                               "candidate": quiz.model_dump()}, ensure_ascii=False)
                    review_schema = Review.model_json_schema()
                    review_schema["properties"]["checks"].update(minItems=count, maxItems=count)
                    review = Review.model_validate_json(_completion(local_client, settings, [
                        {"role": "system", "content": (PROMPTS / "reviewer.txt").read_text(encoding="utf-8")},
                        {"role": "user", "content": review_input},
                    ], review_schema, "quality_review", 1900))
                    if review_passes(review, quiz):
                        return QuizSession(shuffled(quiz), topic, "AI generated · local Gemma",
                                           settings.model, reviewed=True, has_notes=bool(notes.strip()),
                                           source_notes=notes)
                    feedback = "\nRevise the entire quiz. Editor feedback (JSON data): " + json.dumps({
                        "issues": review.issues,
                        "failed_checks": [c.model_dump() for c in review.checks
                            if not c.criterion_is_explicit or len(c.defensible_indices) != 1]
                    })[:2500]
                except (ValueError, KeyError, IndexError, TypeError, ValidationError):
                    feedback = "\nPrevious response failed validation. Return complete, valid JSON with the exact count, distinct questions, four distinct options and matching answer keys."
            raise GenerationError("The quiz did not pass validation and quality review after two attempts. Try a more specific topic, add source notes, or choose Sample mode.")
    except httpx.TimeoutException:
        raise GenerationError("The local model timed out. Check the llama-server terminal, try fewer questions, or use Sample mode.") from None
    except httpx.ConnectError:
        raise GenerationError("Cannot connect to the local model. Run start-llama.ps1 and wait for it to load, or choose Sample mode.") from None
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 503:
            message = "The model is loading or busy. Wait for llama-server to be ready, then try again."
        elif exc.response.status_code == 400:
            message = "The server rejected the request. Check context size (8192 recommended) and JSON-schema support."
        else:
            message = f"The local server returned HTTP {exc.response.status_code}. Check its terminal and model alias, or use Sample mode."
        raise GenerationError(message) from None
    except httpx.HTTPError:
        raise GenerationError("The local connection was interrupted. Check llama-server and try again, or choose Sample mode.") from None
