"""Local llama.cpp adapter with constrained output and a separate quality review."""
import json
from contextlib import nullcontext
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from quiz import GeneratedQuiz, Quiz, QuizSession, shuffled, validate_request
from settings import Settings
from input_rules import enforce_scope

PROMPTS = Path(__file__).resolve().parent / "prompts"


class GenerationError(Exception):
    """A safe message that can be displayed without raw server output."""


class QuestionAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    question_index: int = Field(ge=0, le=4)
    reason: str = Field(min_length=10, max_length=500)
    criterion_is_explicit: bool
    defensible_indices: list[int] = Field(min_length=0, max_length=4)
    translation_is_faithful: bool


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
        and checks[i].translation_is_faithful
        and checks[i].defensible_indices == [q.correct_index]
        for i, q in enumerate(quiz.questions))


def user_prompt(topic: str, count: int, notes: str = "", allow_off_topic: bool = False) -> str:
    topic = validate_request(topic, count, notes)
    return (PROMPTS / "user.txt").read_text(encoding="utf-8").format(
        count=count, topic_json=json.dumps(topic, ensure_ascii=False),
        notes_json=json.dumps(notes, ensure_ascii=False),
        scope_json=json.dumps('exploratory' if allow_off_topic else 'work'))


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
            slots = client.get(settings.base_url.removesuffix('/v1') + '/slots')
            slots.raise_for_status()
            states = slots.json()
            if not isinstance(states, list) or not states or not all(isinstance(s, dict) and type(s.get('is_processing')) is bool for s in states):
                return False, 'Cannot check model availability'
            if all(s.get('is_processing') for s in states):
                return False, 'Local model busy · previous request still processing'
        return True, "Local model ready"
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return False, "Local model offline"


def _preflight(client, settings, messages, max_tokens):
    """Check the real serving slot and model tokenizer, never infer based on character counts."""
    root = settings.base_url.removesuffix('/v1')
    slots = client.get(root + '/slots')
    slots.raise_for_status()
    states = slots.json()
    if (not isinstance(states, list) or not states
            or not all(isinstance(s, dict) and type(s.get('is_processing')) is bool
                       and type(s.get('n_ctx')) is int and s['n_ctx'] > 0 for s in states)):
        raise GenerationError('Cannot verify the local model slot/context. Restart llama-server using start-llama.ps1. / Status slot dan konteks model tidak dapat diperiksa.')
    available = [s for s in states if not s.get('is_processing')]
    if not available:
        raise GenerationError('The local model is still processing another request. Do not keep retrying. If progress stays frozen, press Ctrl+C in the llama-server terminal and run start-llama.ps1 again. The web app can stay open. / Model masih memproses permintaan lain; jika macet, mulai ulang terminal llama-server saja.')
    context_size = min(s['n_ctx'] for s in available)
    try:
        template = client.post(root + '/apply-template', json={
            'messages': messages, 'chat_template_kwargs': {'enable_thinking': False}})
        template.raise_for_status()
        prompt_text = template.json()['prompt']
        if not isinstance(prompt_text, str):
            raise ValueError('Invalid template')
        tokens = client.post(root + '/tokenize', json={'content': prompt_text})
        tokens.raise_for_status()
        token_ids = tokens.json()['tokens']
        if not isinstance(token_ids, list):
            raise ValueError('Invalid tokens')
        input_tokens = len(token_ids)
    except (ValueError, KeyError, TypeError):
        raise GenerationError('Cannot verify this request with the model tokenizer. Check llama.cpp template/tokenizer support. / Permintaan tidak dapat diperiksa dengan tokenizer model.') from None
    if input_tokens + max_tokens + 384 > context_size:
        raise GenerationError(f'This request is too large for the model context: {input_tokens} input tokens plus {max_tokens} reserved output tokens (context {context_size}). Shorten the reference notes or choose fewer questions. / Permintaan terlalu besar; persingkat catatan referensi atau kurangi jumlah soal.')


def _completion(client, settings, messages, schema, name, max_tokens):
    _preflight(client, settings, messages, max_tokens)
    response = client.post(settings.base_url + "/chat/completions", json={
        "model": settings.model, "messages": messages,
        "response_format": {"type": "json_schema", "json_schema": {
            "name": name, "strict": True, "schema": schema}},
        "temperature": 0.5, "top_p": 0.95, "top_k": 64,
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
                  *, client: httpx.Client | None = None, allow_off_topic: bool = False,
                  progress=None) -> QuizSession:
    settings = settings or Settings.from_env()
    topic = validate_request(topic, count, notes)
    scope = enforce_scope(topic, allow_off_topic)
    prompt = user_prompt(topic, count, notes, scope == 'exploratory')
    schema = GeneratedQuiz.model_json_schema()
    schema["properties"]["questions"].update(minItems=count, maxItems=count)
    feedback = ""
    failure_detail = 'The output was incomplete or did not match the required bilingual format.'
    context = nullcontext(client) if client is not None else httpx.Client(
        timeout=httpx.Timeout(settings.timeout, connect=3), trust_env=False)
    try:
        with context as local_client:
            for attempt in range(2):
                try:
                    if progress:
                        progress(f'Writing bilingual questions · attempt {attempt + 1}/2 / Menyusun soal dwibahasa')
                    raw = _completion(local_client, settings, [
                        {"role": "system", "content": (PROMPTS / "system.txt").read_text(encoding="utf-8")},
                        {"role": "user", "content": prompt + feedback},
                    ], schema, "quiz", 300 + count * 700)
                    quiz = GeneratedQuiz.model_validate_json(raw).to_quiz()
                    if len(quiz.questions) != count:
                        raise ValueError("Incorrect question count")
                    accepted = True
                    # Review small batches so bilingual output plus source notes fits the local context.
                    for start in range(0, count, 2):
                        batch = quiz.model_copy(update={'questions': quiz.questions[start:start + 2]})
                        if progress:
                            progress(f'Checking answers and translations · {start + 1}–{start + len(batch.questions)}/{count} / Memeriksa jawaban dan terjemahan')
                        review_input = json.dumps({"topic": topic, "reference_notes": notes,
                            'indexing': 'question_index is zero-based WITHIN THIS BATCH',
                            "candidate": batch.model_dump()}, ensure_ascii=False)
                        review_schema = Review.model_json_schema()
                        size = len(batch.questions)
                        review_schema["properties"]["checks"].update(minItems=size, maxItems=size)
                        review = Review.model_validate_json(_completion(local_client, settings, [
                            {"role": "system", "content": (PROMPTS / "reviewer.txt").read_text(encoding="utf-8")},
                            {"role": "user", "content": review_input},
                        ], review_schema, "quality_review", 250 + size * 300))
                        if not review_passes(review, batch):
                            if any(not c.translation_is_faithful for c in review.checks):
                                failure_detail = 'The editor could not verify that the English and Indonesian versions agree.'
                            elif any(not c.criterion_is_explicit for c in review.checks):
                                failure_detail = 'The editor found a question without a clear, objective criterion.'
                            else:
                                failure_detail = 'The editor could not verify a unique answer key or its factual support.'
                            accepted = False
                            break
                    if accepted:
                        return QuizSession(shuffled(quiz), topic, "AI generated · local Gemma",
                                           settings.model, reviewed=True, has_notes=bool(notes.strip()),
                                           source_notes=notes, topic_scope=scope)
                    feedback = "\nRevise the entire quiz. Editor feedback (JSON data): " + json.dumps({
                        "issues": review.issues,
                        "failed_checks": [c.model_dump() for c in review.checks
                            if not c.criterion_is_explicit or not c.translation_is_faithful or len(c.defensible_indices) != 1]
                    })[:2500]
                except (ValueError, KeyError, IndexError, TypeError, ValidationError):
                    feedback = "\nPrevious response failed validation. Return complete, valid JSON with the exact count, distinct questions, four distinct options and matching answer keys."
            raise GenerationError('The quiz did not pass validation and quality review after two attempts. ' + failure_detail + ' Try a specific property/employee topic or Sample mode. / Kuis belum lolos pemeriksaan; gunakan topik yang lebih spesifik atau mode contoh.')
    except httpx.TimeoutException:
        raise GenerationError("The local model timed out. If GPU activity is idle and a previous request is stuck, press Ctrl+C in the llama-server terminal and run start-llama.ps1 again. For recurring Vulkan stalls on an NVIDIA GPU, use the project-local CUDA runtime described in README.md. Keep the web app open. / Model kehabisan waktu; jika macet, mulai ulang llama-server saja. Jangan terus mengirim permintaan baru.") from None
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
