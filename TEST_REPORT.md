# Verification report

Date: **7 November 2026 (Asia/Bangkok)**. These results describe this local build, not a production deployment or an employee trial.

## Current update: input resilience and bilingual quizzes

**77 offline tests pass** after this update. Python compilation and the updated PowerShell launcher parser check also pass. The additional tests cover English/Indonesian work-topic recognition, explicit topic-specific fun-mode consent, rejected instruction overrides and repetition, the 3,000-character notes limit, tokenizer-based context rejection before inference, busy-slot refusal, malformed slot responses, paired-language shuffling/display, and rejection of unfaithful translations even when the reviewer says approved.

### Reproduced user-reported stall

The existing process answered `/health` with OK, but repeated `/slots` snapshots showed its only slot stuck at **1,536 / 1,705 prompt tokens processed, with zero generated tokens**. Its input was well below the 8,192-token context. Shorter requests could therefore time out behind the occupied slot; reducing notes again would not recover that process. The running executable was the installed Vulkan build, with the documented original flags.

The model process was restarted without stopping the user's web server. Adding `--swa-full` initially passed 1,447-, 2,847- and 4,247-token synthetic probes and bilingual source-note tests. However, a later app run stalled again during prompt processing. **Full SWA caching was not a sufficient fix for the installed Vulkan build.** The failed app check returned an actionable timeout; it was not recorded as a pass.

The final tested runtime is a separate **official llama.cpp b12182 CUDA 12.4** installation under ignored `.tools/llama-cuda/`, using the same existing Gemma GGUF. Official release-asset SHA256 digests were checked before extraction/execution. No model weights, system installation, PATH, graphics driver or Windows settings were changed. `start-llama.ps1` now prefers that local runtime; the reproducible setup helper and checksums are in `scripts/setup_cuda.py`. CUDA device discovery identified the RTX 4070 Ti SUPER, and an active inference observation showed **95% GPU utilization**.

### Final CUDA evidence

| Check | Questions | Inference completions | Observed time | Evidence |
| --- | ---: | ---: | ---: | --- |
| Indonesian topic, bilingual output | 2 | 2 | 13.42 s | [bilingual-indonesian.json](examples/bilingual-indonesian.json) |
| English topic, bilingual output | 2 | 2 | 17.55 s | [bilingual-english.json](examples/bilingual-english.json) |
| 3,000-character synthetic Indonesian briefing | 5 | 4 | 27.31 s | [bilingual-long-notes.json](examples/bilingual-long-notes.json) |
| Explicitly allowed cookie-topic fun quiz | 1 | 2 | 6.64 s | [bilingual-fun.json](examples/bilingual-fun.json) |
| Real-model Streamlit flow, mixed 1/2 score | 2 | 2 | 14.23 s | [bilingual-app-check.json](examples/bilingual-app-check.json) |

Nine additional synthetic requests cycled through 1,447, 2,847 and 4,247 input tokens three times without a stall; see [context-probe.json](examples/context-probe.json). The mixed verification sequence on CUDA completed 23 inference requests, including the initial matrix, repeated probes, another Indonesian-topic run and the app check. These observations support the selected local configuration; they do not guarantee indefinite stability or prove the underlying Vulkan defect's cause.

The exact 3,000-character briefing fixture contains 2,742 prose characters plus 258 intentional padding spaces to exercise the character-limit boundary. The separate tokenizer probes exercise substantive prompts up to 4,247 tokens; character padding is not presented as an equivalent token stress test.

Quizzes were inspected for both-language presence, paired correct choices and explanation agreement. The app check confirms English question text, Indonesian text beneath it, bilingual answer options, both explanations after submission, and results-download availability through Streamlit AppTest. This remains headless functional verification; it does not replace browser/phone visual inspection.

### Review and scope corrections

An early Indonesian-topic run was rejected because the reviewer incorrectly required source notes for self-contained hypothetical constraints. The instructions now explicitly allow hypothetical arithmetic and buyer requirements without notes; only real current claims require source support. Rate questions must identify the success count and denominator, rather than assuming a 100% conversion from vague wording.

Current generation returns both languages together. Each review handles at most two questions and must confirm translation fidelity as well as a uniquely defensible answer. Python shuffles English/Indonesian options as pairs. Obvious spam and direct override phrases are rejected locally; off-topic prose gets a heuristic warning and requires explicit per-topic exploratory consent. Notes are capped at 3,000 characters, and every inference request is checked using the real chat template/tokenizer against its context with reserved output and a safety margin. Oversized text is rejected, not silently truncated. Neither the scope heuristic nor model review is a formal guarantee of semantic correctness.

## Historical first-version evidence

The sections below record the original English-only build, its 55-test result and its earlier failures. Current `bilingual-*.json` files and the section above describe the revised behavior.

## Automated regression checks

Command:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp
```

Observed result: **55 passed** in approximately one second with the prepared environment. Tests make no real inference calls.

Coverage includes:

- All three sample topics at every permitted length, 1–5 questions: 15 complete quiz variants.
- Perfect and zero scores, percentage/export metadata, invalid and missing answers, and boolean values rejected as answer indices.
- Answer shuffling preserves the correct option and explanation.
- Duplicate choices/questions, invalid topic lengths/counts/notes, and non-local model endpoints are rejected.
- Model answer text must exactly match one choice; Python derives the numeric key.
- Exact-count JSON schema requests, truncated output, wrong question counts, HTTP errors, and timeouts.
- A rejected review triggers one bounded revision; two failures return an error rather than a bad quiz.
- An overall approval cannot override a per-question audit identifying multiple defensible choices. Missing question audits also fail.
- Readiness requires both a healthy server and the configured model alias. Loading, unknown aliases, and malformed status responses are handled.
- Streamlit AppTest: offline defaults to Sample mode, inactive AI generation is disabled, unanswered submission is blocked, a complete quiz reaches results, results download exists, a new quiz clears previous answers, and failed generation preserves an existing quiz.

Python source compilation also passed. All three PowerShell scripts passed PowerShell parser checks. The running web server returned HTTP 200 with `ok` from `/_stcore/health`.

## Real local-model integration

The installed model file was `gemma-4-12B-it-qat-UD-Q4_K_XL.gguf`, loaded directly from the existing Hugging Face cache. The server reported version **0.8.0-dev, build 12019, commit 1052f7e1d**, with the Vulkan backend. The app calls its configured alias `gemma-4-12b` at `http://127.0.0.1:8080/v1`. The alias is not an independent weight-version verification.

Command:

```powershell
.\.venv\Scripts\python.exe scripts/verify_live.py
```

All three final cases completed with the strengthened per-question review enabled:

| Case | Questions | API completions | Observed time | Evidence |
| --- | ---: | ---: | ---: | --- |
| Top skills of a property agent in 2026 | 5 | 4 | 55.56 s | [live-agent-skills.json](examples/live-agent-skills.json) |
| Jakarta market briefing interpretation | 5 | 3 | 28.55 s | [live-jakarta.json](examples/live-jakarta.json) |
| Playful hypothetical floor-area puzzle | 1 | 2 | 5.97 s | [live-property-puzzle.json](examples/live-property-puzzle.json) |

Each saved case includes the accepted quiz, answer key, explanations, model/source metadata, creation time, measured duration, and final per-question quality audit. The audit indices refer to the saved `reviewed_candidate` before answer shuffling; the top-level quiz uses its final shuffled positions. The Jakarta case includes the exact **fictional** briefing used. The model did not browse for real Jakarta market updates.

These runs selected the accepted answer keys programmatically and verified full-score exports. That checks the scoring implementation against the keys; it is **not** a factual accuracy benchmark or a real learner's score. Timings are individual observations, not guaranteed performance. The four-call agent-skills case used its revision budget. The three-call market case needed a second generation after an invalid response before its final successful review.

The final agent-skills draft was inspected for its stated constraints and answer/explanation agreement. It contains constraint matching, a numerical negotiation threshold, yield arithmetic, a supplied-document-status scenario, and qualified-lead conversion. No actual employee records were used.

### Real model through the app

`.\.venv\Scripts\python.exe scripts/verify_live_app.py` also passed in **10.97 seconds**. This used Streamlit AppTest with real llama.cpp calls and no model stub: selected AI mode, entered a topic, generated two questions, answered one correctly and one deliberately incorrectly, submitted, reached the results screen, verified a **1/2 score**, and checked that the results download was available. [live-app-check.json](examples/live-app-check.json) records that test attempt. This is functional app evidence, not a visual browser or employee test.

## What went wrong and what changed

### Installed server crashed on successive requests

Initial real generation/review runs terminated llama-server during subsequent requests. Windows Application Error entries named **`nvoglv64.dll`**, exception **`0xc0000005`**, as the faulting module. This was a reproducible process crash, not a quiz JSON exception.

Disabling prompt caching/checkpoints alone did not fix it. Reducing batches to 256 / microbatches to 128 also did not fix it alone. With **`GGML_VK_DISABLE_GRAPH_OPTIMIZE=1`** added to that configuration, successive generation/review/revision requests completed, including all three final cases. The launcher now sets that variable only for its process and restores its previous value on exit. No driver was upgraded, downloaded, or reconfigured.

This identifies a working local configuration; it does not prove the underlying driver or backend defect has been fixed. The flag is used in [upstream Vulkan experimentation](https://github.com/ggml-org/llama.cpp/discussions/21043). Separate [Gemma cache issue reports](https://github.com/ggml-org/llama.cpp/issues/24265) informed the initial cache experiment, but they are not evidence that this crash had the same root cause. `-CpuOnly` is available as a fallback and has not been benchmarked here.

### Valid JSON still contained weak questions

Early drafts asked which skill was “most critical” or which market metric justified buying. Those questions depended on unstated preferences or goals. The first, simple reviewer also approved one insufficiently constrained draft.

The prompts were strengthened to require formulas, explicit matching constraints, defined concepts, or supplied source facts. The reviewer now audits each question's criterion and lists all defensible options. Python requires a complete set of audits and exactly one defensible index matching each key. A global approval flag is insufficient. Live review rejected vague proximity criteria, ambiguous negotiation actions, and preference-based communication questions before a successful revision.

### The model sometimes returned the wrong option index

Some early drafts explained the right calculation but pointed to the wrong numbered choice. Generation now returns the **exact correct answer text**. Python checks that it matches exactly one option and derives the index, then shuffles choices while preserving the key. The independent review still checks whether that selected answer is actually defensible.

## Verification limits and manual checks

The in-app browser access host was unavailable. Native browser inspection then stopped because the computer-use environment did not support URL-policy enforcement for the installed Windows browser. No browser actions were continued after that stop. Consequently:

- Desktop visual appearance and screenshots were **not verified** through a browser.
- Physical-phone rendering and LAN access were **not tested**.
- Responsive CSS and single-column form behavior are implemented, but AppTest is a headless functional harness rather than a visual browser test.
- No claims are made about concurrent employee load, authentication, persistence, or production availability.
- No public GitHub repository or hosted quiz URL was created; the user handles publication and submission.

Before submitting, open the app on a desktop and phone, check text wrapping and option selection, submit a sample quiz, and inspect the score review. For a current-market demo, paste dated source material you have checked. AI quality review reduces risk but cannot guarantee correctness; formal assessment needs a human content review.
