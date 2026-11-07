# 99 Learn — local employee quiz generator

A Streamlit app for 99 Group employees: enter a property, employee or company topic in **English or Bahasa Indonesia**, generate a quiz with the installed **Gemma 4 12B QAT** model through **llama.cpp**, and review your score. Questions, all four choices and explanations display **English first, then Indonesian underneath**. Setup, status messages and warnings are English-only. Three bilingual sample topics work without a model or internet connection.

The whole application runs on your computer. No cloud model, API key, database, or external content service is required at runtime. This is an assessment prototype inspired by 99 Group, not an official company product.

## Run on this prepared computer: two terminals, two commands

Open two PowerShell terminals in **`assesment/project-c`**. The project environment and dependencies have already been installed here.

**Terminal 1 — start the installed model:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-llama.ps1
```

Wait until it prints `model loaded` and `listening on http://127.0.0.1:8080`.

**Terminal 2 — start the app:**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-web.ps1
```

Open **http://127.0.0.1:8501**. Keep both terminals running; **Ctrl+C** stops each server. Sample mode needs only Terminal 2. Port 8080 is the model server; port 8501 is the quiz app.

## First-time setup on another computer

Requirements: Windows PowerShell, Python 3.11 or newer, Git, and a recent llama.cpp build supporting the installed Gemma model, `--jinja`, `--reasoning off`, and JSON schema responses. Put `llama-server` on PATH. The model and llama.cpp are not bundled in this repository.

From the project directory, run this once:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
```

This creates a separate `.venv` and installs the pinned application and test dependencies. It uses `uv` when available, otherwise Python's venv and pip. If Python is not discoverable, pass `-PythonPath 'C:\path\to\python.exe'`. Internet is normally needed for dependency installation; it is not needed for subsequent quizzes.

The model launcher looks for your existing file named `gemma-4-12B-it-qat-UD-Q4_K_XL.gguf` in the Hugging Face cache. To use an installed GGUF elsewhere:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-llama.ps1 -ModelPath 'D:\models\gemma-4-12B-it-qat-UD-Q4_K_XL.gguf'
```

The launcher never downloads a model. It sets alias `gemma-4-12b`, loopback address `127.0.0.1`, port 8080, 8192 context tokens, one inference slot, GPU offload, and thinking disabled. **On this prepared NVIDIA computer it prefers the project-local official CUDA 12.4 runtime, release b12182**, at `.tools/llama-cuda/llama-server.exe`. That runtime uses the existing Gemma GGUF; the Winget installation, model weights, Windows PATH and graphics driver are unchanged. If the local runtime is absent, the launcher falls back to `llama-server` on PATH. `-ServerPath` selects another existing executable explicitly.

The original installed Vulkan build could report healthy while its single inference slot was frozen during prompt processing. Full SWA caching and smaller batches helped some long requests but **did not fully resolve the recurring Vulkan stalls**. Repeated mixed-length requests and bilingual generation were therefore checked on the separate CUDA runtime. The launcher retains `--swa-full`, batches of 256 / microbatches of 128 and disabled prompt caching/checkpoints. `GGML_VK_DISABLE_GRAPH_OPTIMIZE=1` remains scoped to the process for Vulkan fallback; CUDA does not use that Vulkan option. These are measured local results, not a claim that the original backend defect has been repaired.

For a fresh NVIDIA Windows checkout, install the same isolated runtime once, after Python setup:

```powershell
.\.venv\Scripts\python.exe scripts/setup_cuda.py
```

This downloads two pinned official GitHub release archives (about 680 MB combined), verifies their recorded SHA256 digests, and extracts them under ignored `.tools/`. It installs no model or driver and makes no global changes. Subsequent launches still use the same two normal commands. The source URL and checksums are in `scripts/setup_cuda.py`; the upstream build is [llama.cpp b12182](https://github.com/ggml-org/llama.cpp/releases/tag/b12182).

GPU support and speed depend on your llama.cpp build and hardware. A CPU fallback is available as `start-llama.ps1 -CpuOnly`; it can be slower and has not been benchmarked. The equivalent base command is:

```powershell
llama-server --model 'D:\models\your-model.gguf' --alias gemma-4-12b --host 127.0.0.1 --port 8080 --ctx-size 8192 --parallel 1 --gpu-layers 0 --device none --jinja --reasoning off --swa-full --no-cache-prompt --cache-ram 0 --ctx-checkpoints 0 --batch-size 256 --ubatch-size 128
```

macOS/Linux: create and activate a Python 3.11+ virtual environment, `python -m pip install -r requirements-dev.txt`, start an equivalent `llama-server` command, and run `python -m streamlit run app.py`. PowerShell launchers are Windows conveniences.

## Use the app

1. Choose **AI mode** or **Sample mode**. When the model is unavailable, Sample mode is the initial selection. You can choose it while the model is running too.
2. In AI mode, type a topic in English or Indonesian and optionally paste reference notes (up to **3,000 characters**). In Sample mode, select one of the three prepared topics.
3. Choose **1–5 questions**, then generate or start the sample.
4. Select one answer per question and submit. An incomplete form stays open and asks you to answer every question.
5. Review the score, correct options, your answers, and one- or two-sentence explanations. Download the review as JSON, or create another quiz.

The answer order is shuffled while preserving the answer key. A new quiz clears prior answer selections. Returning to setup preserves your existing quiz until a replacement succeeds. Submitted results stay fixed; scoring and downloads make no model calls.

### Topic coverage and input checks

Property, employee skills and company learning are the default scope in both languages. A keyword-based scope check warns about topics such as `give me cookie recipe` or `resep kue`. You can explicitly tick **Continue anyway**. Consent applies to that particular topic; changing the topic requires a fresh choice. Such quizzes are labelled outside work topics and are still subject to the bilingual and single-answer checks. The scope check is a heuristic, so a relevant topic without a recognized keyword may also receive this warning.

Obvious repeated/unbroken character spam and direct override requests such as `forget previous instructions` or `abaikan instruksi sebelumnya` are rejected locally. The topic-scope override does not bypass those input checks. The LLM still receives topic and notes as data, not as replacement system instructions.

### The three sample topics

| Topic | Questions available | Content |
| --- | ---: | --- |
| Property agent skills | 5 | Qualification, conversion rates, verification, communication, AI fact checking |
| Reading a Jakarta market briefing | 5 | Percentage changes, enquiry ratios, data coverage, asking vs sale prices |
| Property numbers & playful puzzles | 5 | Area, viewing schedules, hypothetical rental yield, matching requirements, listing views |

The Jakarta sample uses a **clearly labelled fictional briefing** displayed above the questions. It is not a real market report. All 15 questions, choices, keys, explanations, and briefings are readable in [data/samples.json](data/samples.json).

### Topics about current market updates

The local model has **no browsing, retrieval, or live data feed**. For `property market updates in Jakarta`, paste a dated, reliable briefing into **Add source notes**. English and Indonesian notes are accepted. URLs alone are not opened. The quiz retains those notes so the learner can read them alongside the questions. Character limits do not replace token accounting: every model request also checks the actual rendered prompt with llama.cpp's tokenizer, reserves output space and a safety margin, and rejects oversized input before inference. Notes are never silently truncated.

Without notes, the prompts require general concepts and explicitly hypothetical scenarios. A year in a topic does not turn the model into a current-news source. Supplied notes are assumed accurate; the app does not independently verify them. [examples/jakarta-briefing.txt](examples/jakarta-briefing.txt) provides a synthetic demonstration you can paste without misrepresenting it as news.

## How generation works

```mermaid
flowchart TD
    A[Choose mode, topic and 1–5 questions] --> B{Mode}
    B -->|Sample| C[Load prepared question bank]
    B -->|AI| D[Check local model readiness]
    D --> E[Build prompt with optional reference notes]
    E --> O{Token budget fits and inference slot free?}
    O -->|Yes| F[llama.cpp chat completions with bilingual JSON schema]
    O -->|No| K
    F --> G[Validate schema, count and distinct choices]
    G --> H[Review answers and translations in batches of up to two]
    H -->|Pass| I[Shuffle English and Indonesian answer pairs]
    H -->|Fail| J{Revision available?}
    G -->|Invalid output| J
    J -->|Once| F
    J -->|No| K[Display error and offer Sample mode]
    C --> I
    I --> L[Answer quiz in Streamlit]
    L --> M[Python scoring and explanations]
    M --> N[Optional JSON results download]
```

- `GET /health`, `GET /v1/models` and `GET /slots` establish readiness, the configured alias and an available inference slot. A healthy but occupied server is shown as busy. Status is cached for 15 seconds; **Refresh model status** checks again. Generation checks again immediately before every request, rather than queuing behind a busy slot.
- `POST /apply-template` and `POST /tokenize` measure each actual prompt against its serving context. Input tokens + reserved output + a 384-token margin must fit. These endpoints do not run inference.
- `POST /v1/chat/completions` uses a JSON schema with the exact requested count, English fields and required Indonesian `_id` translations, four paired options, a `correct_answer` string matching one English option, and explanations in both languages. Python derives the integer answer key (0–3); both language versions are shuffled together.
- Python rejects duplicate questions, duplicate/empty choices, invalid indices, extra fields, wrong counts, and incomplete responses.
- Separate completions audit batches of **at most two questions**, checking unique correctness, grounding, arithmetic, and translation fidelity (including numbers, negations and thresholds). Python requires one audit for every question, a faithful translation and exactly one defensible index matching the key. A global approval alone is insufficient. Hypothetical constraints and arithmetic do not need source notes; claims about actual current facts do. One full revision is allowed, for at most two generations plus six batch reviews (eight inference completions for five questions).
- Connection, timeout, and HTTP failures display safe, actionable messages. They do not silently substitute sample questions. The user chooses Sample mode explicitly after a failure.
- AI review reduces ambiguity but **cannot prove factual correctness or unique correctness**. A domain expert should review AI questions before using them for formal assessment. The prepared sample bank provides an inspectable alternative.

## Configuration

Defaults work without any configuration file. Optional environment variables must be set in the app's terminal **before** starting Streamlit:

```powershell
$env:LLAMA_BASE_URL = 'http://127.0.0.1:8080/v1'
$env:LLAMA_MODEL = 'gemma-4-12b'
$env:LLAMA_TIMEOUT = '120'
```

Only loopback HTTP model URLs ending in `/v1` are accepted. Model requests bypass proxy environment settings. The connection timeout is 3 seconds and read timeout defaults to 120 seconds **per request**, configurable from 5 to 300. A revision can therefore take longer than one timeout window.

If ports are occupied, use `start-web.ps1 -Port 8504` or `start-llama.ps1 -Port 8081`; for the latter also set `LLAMA_BASE_URL` to `http://127.0.0.1:8081/v1` in the app terminal.

If requests time out while GPU activity stays low, **do not repeatedly click Generate**. A stalled inference may still occupy the single slot even though `/health` says OK. Press Ctrl+C in the **model terminal only**, rerun `start-llama.ps1`, wait for readiness and refresh model status. The web app can stay running. Check the printed **Server runtime** path: on this NVIDIA computer it should point into `.tools/llama-cuda`, not the Winget Vulkan binary. Existing quizzes from the English-only version can still be scored; create a new quiz to get both languages.

### Open on a phone on the same Wi-Fi

The layout uses responsive widths and a single-column quiz flow. Start the web app with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\start-web.ps1 -Lan
```

Find the PC's local IPv4 address with `ipconfig`, then open `http://YOUR_PC_IP:8501` on your phone. Both devices must be on the same network; Windows Firewall may need to allow the Python app on the private network. The LLM remains on the PC's loopback interface. LAN mode has no login and is for a trusted local demo. Default startup stays local to the PC. The app is not a deployment for 99 simultaneous users; inference is configured for one slot.

## Verify

Offline automated checks:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
```

One real local-model check, after starting llama-server:

```powershell
.\.venv\Scripts\python.exe live_check.py --topic 'Top skills of a property agent in 2026' --count 5
```

It saves `examples/live-quiz.json` on success. To supply notes, use `--notes-file examples/long-training-briefing.txt`. Use `--allow-off-topic` only when you explicitly want an exploratory topic. For current bilingual integration cases, run `.\.venv\Scripts\python.exe scripts/verify_live.py`; this invokes the Indonesian, English, long-note and explicit fun-mode checks sequentially. Individual cases use `scripts/verify_bilingual.py --case indonesian` (or `english`, `long-notes`, `fun`). Traces stay in ignored `artifacts/`; only public synthetic fixture data is used.

See [TEST_REPORT.md](TEST_REPORT.md) for actual verification and limits. Programmatic perfect-score examples check scoring against the model's answer key; they are not employee attempts or an independent factual accuracy measurement.

The bilingual update passed **77 offline tests**. Real local-model examples include [Indonesian topic input](examples/bilingual-indonesian.json) and [five questions from 3,000-character notes](examples/bilingual-long-notes.json). [context-probe.json](examples/context-probe.json) records successful synthetic requests up to 4,247 input tokens. `scripts/verify_live_app.py` checks real bilingual generation, both-language display, a deliberately mixed **1/2 score** and the results download. Older `live-*.json` files document the English-only first version; `bilingual-*.json` files document this update. Browser and physical-phone visual checks remain separate from headless interaction tests.

## Project map

```text
app.py                 Streamlit screens and session state
quiz.py                Validated data contract, shuffling, scoring, export
generator.py           Local API calls, bounded revision, quality review
settings.py            Local-only environment configuration
input_rules.py         English/Indonesian scope and readable-input checks
samples.py             Offline bank loader
data/samples.json      3 topics × 5 questions
data/sample_translations.json  Prepared Indonesian sample translations
prompts/               Actual system, user and reviewer prompt text
assets/style.css       Responsive visual styling
start-web.ps1          Web launcher (optional LAN access)
start-llama.ps1        Existing GGUF launcher
setup.ps1              One-time environment installation
tests/                 Domain, model adapter and Streamlit interaction tests
examples/              Briefing and inspectable output evidence
scripts/verify_live.py Repeatable live integration check
SUBMISSION_GUIDE.md    Assessment fields and actual prompts to paste
```

Quizzes and answers live in the browser's Streamlit session; a page reload or server restart can reset them. There is no employee tracking, account system, central results store, or quiz publishing. Reference notes are not included in ordinary results downloads. No model files, secrets, environment, or logs are committed.

## Design and technical references

99 Group's [official company page](https://www.99.co/about-us/indonesia) and [99.co Indonesia website](https://www.99.co/id) were accessible during research. Their property focus and emphasis on ease of use informed a blue-and-white learning interface with rounded panels, clear labels, and generous spacing. It is an original assessment interface, not a reproduction of a formal brand guide. Attempts to open [99 Indonesia on Instagram](https://www.instagram.com/99indonesia/) and [99 Group on Instagram](https://www.instagram.com/99group/) were unsuccessful; no Instagram assets were copied. No remote fonts or images are required.

The implementation follows the official [llama.cpp server API](https://github.com/ggml-org/llama.cpp/tree/master/tools/server), [Streamlit radio-widget API](https://docs.streamlit.io/develop/api-reference/widgets/st.radio), and [Streamlit app-testing API](https://docs.streamlit.io/develop/api-reference/app-testing). The model is the user's installed [Gemma 4 12B QAT GGUF](https://huggingface.co/unsloth/gemma-4-12B-it-qat-GGUF); the repository does not redistribute it.

## Git and submission

This folder is a self-contained local Git repository. You manage the public GitHub repository and submission. Publish **this folder's contents**, not the wider Internship workspace, which contains unrelated personal material. Do not upload `.venv`, model weights, logs, or secrets.

After creating your empty public GitHub repo, use your own URL:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Check the repository while signed out. The evaluator cannot open `localhost`; a local URL is a run instruction, not a public demo link. The public repo must contain the source, prompts, sample output, run instructions, and test report. [SUBMISSION_GUIDE.md](SUBMISSION_GUIDE.md) contains copyable field text and the actual prompts, so you can paste them directly into the assessment form. Edit the reflection into your own words and include only claims you can demonstrate.
