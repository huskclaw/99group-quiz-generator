"""Rebuild the paste-ready guide from the exact runtime prompts."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generator import user_prompt

intro = '''# Assessment submission guide

You manage the public GitHub URL and form submission. Replace every `YOUR_USERNAME/YOUR_REPO` below with your actual public repo. Check it while signed out. Do not submit a localhost address as an accessible demo, and do not rely on a Drive/Docs/Dropbox link. The evaluator needs readable source and pasted text.

## Field 1 — Submit your output

Suggested text to adapt:

> I built 99 Learn, a local Streamlit quiz generator for 99 Group employees. AI mode takes a free-text topic and generates 1–5 four-choice questions through the installed Gemma 4 12B QAT model on llama.cpp. Sample mode provides three prepared topics with five questions each. Users submit one answer per question, then see their score, correct answers, and short explanations. They can also download the results as JSON.
>
> This is a local prototype. There is no hosted public demo. The runnable code, actual prompts, prepared question bank and generated examples are in my public repository: https://github.com/YOUR_USERNAME/YOUR_REPO
>
> To reproduce: follow README.md, start the model and web app in two terminals, and open http://127.0.0.1:8501 on the same computer. The examples directory contains actual local-model output with provenance. Its perfect scores were obtained by selecting the generated answer keys programmatically to test scoring; they are not employee scores.

Paste a readable output example too (this one is from the curated sample bank):

```text
Topic: Reading a Jakarta market briefing
Source: Curated offline sample; fictional training figures, not real Jakarta data.
Question: According to the fictional briefing, by what percentage did District A's median advertised price rise from Rp2.0 billion to Rp2.1 billion?
A. 2%
B. 5%
C. 10%
D. 20%
Correct answer: B. 5%
Why: The increase is Rp0.1 billion divided by the initial Rp2.0 billion, which equals 5%.
```

For an AI-generated example, copy a question, choices, answer and explanation from `examples/live-agent-skills.json` after reviewing that file. Do not label a curated sample as AI-generated. You can include the public GitHub link to the example alongside its pasted contents.

## Field 2 — Submit your repo/workflow

```text
https://github.com/YOUR_USERNAME/YOUR_REPO — public

The repo contains the complete local Streamlit app, llama.cpp adapter, offline bank, actual prompts, automated tests, generated examples, architecture diagram, run guide and verification report. The workflow is Python code, so there is no separate n8n/Flowise canvas required.
```

## Field 3 — Key prompts and descriptions of AI usage

Paste the actual prompt text below directly into the form, then the explanation. These blocks are assembled from the same files the app reads at runtime.

### Actual generation system prompt

'''

example_path = ROOT / "examples/live-app-check.json"
if example_path.exists():
    example = json.loads(example_path.read_text(encoding="utf-8"))
    question = example["questions"][0]
    choices = "\n".join(f"{'ABCD'[i]}. {option}" for i, option in enumerate(question["options"]))
    actual_output = ("### Actual local-model output example\n\n```text\n"
        + "Source: AI generated locally with Gemma 4 12B QAT; accepted after per-question review.\n"
        + "Question: " + question["question"] + "\n" + choices + "\n"
        + "Correct answer: " + "ABCD"[question["correct_index"]] + ". "
        + question["options"][question["correct_index"]] + "\nWhy: " + question["explanation"]
        + "\n```\n\nThe app verification selected one correct and one wrong answer across two questions and recorded a 1/2 score. That is a programmatic test attempt, not an employee result.\n\n")
    intro = intro.replace("## Field 2 — Submit your repo/workflow", actual_output + "## Field 2 — Submit your repo/workflow")
parts = [intro]
parts.append("```text\n" + (ROOT / "prompts/system.txt").read_text(encoding="utf-8").strip() + "\n```\n")
parts.append("\n### Actual user prompt for a five-question example\n\n```text\n" +
             user_prompt("Top skills of a property agent in 2026", 5).strip() + "\n```\n")
parts.append("\nFor other requests, the same template substitutes the requested count, JSON-encoded topic and JSON-encoded reference notes. The template itself is:\n\n```text\n" +
             (ROOT / "prompts/user.txt").read_text(encoding="utf-8").strip() + "\n```\n")
parts.append("\n### Actual reviewer system prompt\n\n```text\n" +
             (ROOT / "prompts/reviewer.txt").read_text(encoding="utf-8").strip() + "\n```\n")
parts.append('''
The review user message is a JSON object containing `topic`, `reference_notes` and the complete `candidate` quiz. It varies with the generated quiz. Both stages use schema-constrained API responses. The generation schema requires a title and 1–5 questions; each question has exactly four options, a `correct_answer` string that exactly matches one option, and an explanation. Python derives the answer index from that string before review. The reviewer returns per-question checks (`question_index`, a short `reason`, `criterion_is_explicit`, and `defensible_indices`), plus `approved` and a list of `issues`. Python requires an audit for every question, an explicit criterion, and exactly one defensible index matching the original key. See `quiz.py` and `generator.py` for the exact contracts.

The actual revision suffix is one of:

```text
Revise the entire quiz. Editor feedback (JSON data): [a JSON object containing issues and failed_checks]
```

```text
Previous response failed validation. Return complete, valid JSON with the exact count, distinct questions, four distinct options and matching answer keys.
```

### Explain the model and workflow

Suggested text to adapt:

> I used Gemma 4 12B QAT because it was already installed and the task required a local llama-server API. The quantized model keeps inference local without a paid cloud API or runtime internet dependency. I did not train or fine-tune it. The app calls llama.cpp's OpenAI-compatible chat completions endpoint with JSON-schema output.
>
> AI writes questions, choices, answer keys and short explanations. A separate completion reviews whether the keyed answer is uniquely defensible and whether current claims are supported by supplied notes. Python independently validates structure, exact question count, distinct options and answer-index range. It then shuffles choices and scores answers locally. One revision is allowed; a quiz that still fails review is rejected. API failures show an actionable error and leave Sample mode available. Samples are explicitly labelled and never silently substituted for failed AI output.
>
> The model has no live market feed. For current market topics I supply dated notes; otherwise the app asks for stable concepts and hypothetical scenarios. The synthetic Jakarta briefing is labelled fictional. Model review is a useful filter, not proof of factual correctness, so formal employee assessment would still need human content approval.
>
> I used AI coding assistance to implement and check the prototype. The actual runtime quiz prompts are pasted above. I would describe my own review, changes and testing here before submitting.

## Field 4 — Any repo (optional)

Use the same repo, an additional relevant public repo, or leave blank. Do not add unrelated work just to fill the field.

## Field 5 — Other documents (optional)

```text
README.md in the public repo: two-terminal startup, setup, optional phone access, configuration, architecture and limitations.
TEST_REPORT.md: actual test evidence, build issues and verification limits.
examples/: generated quizzes and the synthetic source briefing used for the market-reading demo.
prompts/: complete runtime system, user and reviewer prompts.
```

These files will be publicly readable after you push. Link to their actual public GitHub pages if useful, and summarize the material in the text box too.

## Reflection — write this in your own words

Use the concrete observations in TEST_REPORT.md. Useful points to explain:

- A structurally valid JSON quiz can still contain subjective or ambiguous questions. That is why there is a separate review stage and why the prompt asks for explicit constraints.
- Initial live outputs included subjective “most critical skill” questions. The prompts were revised to ask for applied scenarios and plausible near-misses.
- Some drafts explained the right answer but selected the wrong numbered option. The generator now returns exact answer text and Python derives the index.
- Real model verification exposed an installed-server/graphics-driver crash during successive requests. Describe only the workaround and successful checks actually recorded in TEST_REPORT.md.
- The evaluator cannot open a localhost demo, so the public repo, readable output examples and pasted prompts are essential evidence.
- A next version would add approved dated source retrieval, independent human content approval, saved quiz versions, authentication, a results store and queued generation for multiple employees.
- Desktop and phone layouts need a final manual browser check; automated Streamlit tests do not verify visual appearance.

Do not claim that the app is deployed, that real employees used it, that the output is guaranteed correct, or that phone testing happened unless you actually perform and document those steps.
''')

(ROOT / "SUBMISSION_GUIDE.md").write_text("".join(parts), encoding="utf-8")
print("Updated SUBMISSION_GUIDE.md from actual runtime prompt files.")
