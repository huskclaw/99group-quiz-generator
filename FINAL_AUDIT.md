# Final submission audit — Section 2, Option C

Audit date: 7 November 2026 (Asia/Bangkok). Scope: `project-c` only. No Section 3 or other internship content was inspected or changed. **Readiness: Ready after these steps** — commit the audited changes, publish this standalone repository, verify anonymous access, then replace placeholders and paste the handoff. The local deliverable passed; publication and a fresh dependency download remain unverified.

## Git: what would be published

- Git root: `D:/VSCode/others/Internship/assesment/project-c`; `.git/` is inside this folder. This is a standalone repo, not the parent Internship repo. No parent Git contents needed inspection.
- Branch: `main`. Committed HEAD at audit start: `8f2350cf4acc0ceeff91a41c3ea6fa62ab17c9cd` (`Simplify topic warning and keep setup interface English-only`). Five local commits existed at audit start.
- Remote destination: **none configured**. No remote-tracking refs or upstream. There is no verified public URL, remote branch or evidence these commits were published. A clean initial working tree did not imply GitHub was current.
- At audit start: 49 tracked files, no staged/unstaged modifications and no non-ignored untracked files. Ignored artifacts existed locally. The audit initially left changes unstaged and uncommitted; it did not configure a remote, push, change visibility, rewrite history or delete ambiguous files.
- Proposed submission: 54 explicitly selected files (49 tracked working files plus the five new evidence/audit files below). Only committing/pushing these makes them available to an evaluator. `.git`, ignored files and other workspace directories are excluded.

## Sensitive material and file classification

Checked every blob in all five commits and reflog-reachable history using `git rev-list --objects --all --reflog` and `git cat-file`, plus current project text outside the environment/runtime/cache folders. `git fsck --full --no-reflogs` reported no dangling/unreachable object findings. Pattern checks covered common provider tokens, private-key headers and assigned credential-like values; sensitive filenames were checked as well. No credential-pattern matches, committed `.env`/Streamlit secrets, private keys, weights, large binaries, unrelated documents or personal records were found. This is a targeted scan, not proof no possible secret exists. Largest historical blob was README.md, 18,960 bytes. Findings are path/metadata-only; no credentials were printed.

If a committed secret is discovered later, deleting its present file is insufficient: revoke/rotate it and address its historical exposure before publishing. No history rewrite was performed.

| Paths | Classification | Reason/action |
| --- | --- | --- |
| `app.py`, core Python modules, launchers, requirements, `.streamlit/config.toml`, `assets/style.css`, `prompts/`, `tests/` | keep | Referenced runtime, reproducible setup and regression checks. Streamlit config contains theme/server settings, not secrets. |
| `data/samples.json`, `data/sample_translations.json` | keep | Actual offline banks used by samples.py and tested by the app. |
| `examples/jakarta-briefing.txt`, `examples/long-training-briefing.txt` | keep | Synthetic notes referenced by live checks and docs. Long fixture intentionally pads to exactly 3,000 characters; .gitattributes preserves that boundary. |
| `examples/live-*.json` | keep | Provenanced historical English-only output; explicitly labelled historical in README/TEST_REPORT, not current bilingual results. |
| `examples/bilingual-*.json`, `examples/backend-verification.json`, `examples/context-probe.json` | keep | Current-update and backend evidence referenced in README/TEST_REPORT and verification scripts. Fun-topic evidence records explicitly consented off-topic behavior; not the headline property deliverable. |
| `scripts/probe_server.py`, `scripts/setup_cuda.py`, `scripts/verify*.py`, `live_check.py`, `scripts/build_submission_guide.py` | keep | Referenced reproducible probes, runtime installation, live checks and guide generator. Not disposable scratch scripts. |
| New `examples/final-audit-*.json`, `examples/FINAL_PROPERTY_RUNS.md`, `scripts/final_audit.py` | keep | Fresh property-topic output, readable provenance and repeatable real app/model audit. |
| `.venv/`, `.tools/` | ignore locally | Installed dependencies/runtime and downloaded binaries are intentionally unbundled. Preserve for local use. |
| `__pycache__/`, `scripts/__pycache__/`, `tests/__pycache__/`, `.pytest_cache/`, `*.log` | ignore locally | Disposable caches/logs already excluded from Git. Preserved locally; none was tracked. |
| `artifacts/` | ignore locally | Existing traces plus the explicit clean-copy manifest, isolated submission copies and audit installation cache. Never use a recursive folder upload. |
| Future `.env`, `.env.*`, `.streamlit/secrets.toml`, `local.settings.ps1`, `*.gguf` | ignore locally | Existing rules extended to cover environment variants. `.env.example` remains allowable if intentionally sanitized. |
| Ambiguous files | review before deletion | None required deletion. No file was judged unused solely because its filename looked temporary. |

Ignore corrections: `.env.*` with a sanitized `.env.example` exception, `venv/`, common Python analysis/coverage caches, and OS metadata. Tested actual ignore decisions for environment variants, secrets, logs, `.tools`, `.venv` and artifacts. Nothing already tracked was hidden by this change. No application behavior was changed.

## Fresh checks and actual deliverable

Implementation: Streamlit 1.67.0, httpx 0.28.1, pydantic 2.14.3; pytest 9.2.0 for development. Defaults resolved to `http://127.0.0.1:8080/v1`, alias `gemma-4-12b`, timeout 120 seconds. The model was initially offline. The audit started the existing project-local CUDA launcher with the installed `gemma-4-12B-it-qat-UD-Q4_K_XL.gguf`; it reported model loaded, one 8,192-token slot, and the expected alias through `/v1/models`. The actual generation endpoint is `POST /v1/chat/completions`. No cloud model, Gemini endpoint or API credential is used.

**77 offline tests passed** in 1.93 seconds in the project, covering scoring, samples, validation/review failures, current limits, token budgeting/busy slots, per-topic consent, instruction-like input rejection and Streamlit widget flows. Guard tests include English/Indonesian unrelated topics, consent reset on topic change, direct override phrases and repetition. Scope detection remains heuristic; explicit consent intentionally permits exploratory quizzes. No new design choice was imposed.

Fresh real-model tests used `python scripts/final_audit.py` and the actual Streamlit application, without stubbing generation:

| Case | Requested/returned | Inputs | Time | Scoring |
| --- | --- | --- | ---: | --- |
| Evergreen hypothetical property rental yield | 2/2 | 119-character topic, no notes | 14.89 s | 1/2; first answer deliberately wrong |
| Dated synthetic Jakarta property briefing | 5/5 | Exactly 160 topic characters and 3,000 note characters | 30.34 s | 4/5; first answer deliberately wrong |

Both flows checked that an incomplete attempt stayed open, generated content passed the app's review stage, notes were preserved exactly, bilingual explanations appeared on the results screen, and a results download was available. Output and exact input are in `examples/final-audit-evergreen.json`, `examples/final-audit-dated-notes.json` and the readable `examples/FINAL_PROPERTY_RUNS.md`. Results JSON normally omits notes; the dedicated audit evidence intentionally includes its public synthetic inputs. No employee data was used.

Manual content check of all seven fresh questions:

- Evergreen: 50,000,000 / 1,000,000,000 = 5%; 150,000,000 / 2,500,000,000 = 6%. Each keyed option is unique; explanations and Indonesian values agree.
- Dated notes: asking-price increase is 5%; campaign conversion is 20/80 = 25%; Unit P alone satisfies all three constraints; new listings declined by 20; a city-wide supply conclusion is unsupported. All follow from the exact supplied notes. No real market-news claim was established or implied. English/Indonesian keys and explanations agree.

Desktop browser check on the running local app: chose labelled Sample mode, took all five property-agent sample questions, intentionally answered the first wrongly and the other four correctly, submitted, and observed **4/5, 80%**, the selected/correct answer labels, bilingual explanations and download control. The rendered result layout was visually inspected. This was a local browser session, not a public/signed-out hosted-demo test. Physical phone and LAN access remain untested. Older TEST_REPORT browser limitations are historical; this desktop check supersedes that particular gap.

## Clean submission-copy verification

The clean copy was built from `git ls-files` plus an explicit five-file allowlist for new evidence, using the working versions of tracked files. It did not use a recursive workspace copy or blindly include untracked files. The ignored manifest is `artifacts/clean-copy.json`; it records the selected paths and isolated location. It excludes `.git`, credentials, `.env`, Streamlit secrets, model weights, local model runtime, local settings, logs, caches and the prepared `.venv`.

The documented `setup.ps1 -PythonPath <existing Python>` successfully created a fresh Python 3.11.16 environment, but dependency installation failed because the execution environment denied network connections to PyPI. A network-enabled retry could not access the newly created isolated copy in its separate execution context. No automatic approval rejection occurred. Therefore **fresh dependency download/installation is not verified**; do not interpret the following smoke tests as a clean install result.

As the environment permitted, ran the full suite against only the clean copied source with the already installed project interpreter/dependencies: **77 passed in 2.17 seconds**. This exercised samples, prompts, stylesheet loading, app flows and path resolution without relying on omitted source assets or secrets. The final document refresh is rechecked against the same explicit manifest. The model/llama.cpp are documented external prerequisites rather than missing repo files. No model download was attempted.

Remaining setup check on an internet-connected machine: clone the public repo into an empty directory, run `powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1`, then `.\.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_cache/tmp` and `powershell -NoProfile -ExecutionPolicy Bypass -File .\start-web.ps1`. Complete a Sample-mode quiz. For AI mode, follow README's compatible model/runtime setup and run `.\.venv\Scripts\python.exe scripts/final_audit.py`. The fresh local live-generation audit itself has no outstanding case.

## Public access and assessment handoff

- Public repository: **https://github.com/YOUR_USERNAME/YOUR_REPO [PENDING]**. None is configured, so anonymous access is unverified and no remote revision can be compared.
- Public demo: **[PENDING — no deployment URL found]**. `127.0.0.1:8501` works only on this PC. No hosted saved-quiz or live-generation access was tested.
- A minimal hosted demo can serve Sample mode without a model; public live generation needs a compatible model on the same host because model URLs are restricted to loopback. Do not promise cloud generation from an app-only deployment.
- Public GitHub source plus pasted text are evaluator-readable per the supplied instructions. There is no published point breakdown, and no claim is made that a public hosted demo is mandatory.
- `SUBMISSION_GUIDE.md` now supplies all actual form fields, exact runtime system/user/reviewer prompts, a filled-in prompt, corrective-message construction, actual model rationale, AI coding assistance, compact real output and an editable reflection. Important evidence stays in pasted text and the repo. Optional fields add no unrelated material.

## Exactly what remains to commit and publish

The audit changed four existing files: `.gitignore`, `README.md`, `SUBMISSION_GUIDE.md`, `scripts/build_submission_guide.py`. It added five files: `FINAL_AUDIT.md`, `scripts/final_audit.py`, `examples/final-audit-evergreen.json`, `examples/final-audit-dated-notes.json`, `examples/FINAL_PROPERTY_RUNS.md`. Existing app, tests, runtime prompts and historical fixtures were preserved.

From inside project-c, review and stage only these paths:

```powershell
git add -- .gitignore README.md SUBMISSION_GUIDE.md FINAL_AUDIT.md scripts/build_submission_guide.py scripts/final_audit.py examples/final-audit-evergreen.json examples/final-audit-dated-notes.json examples/FINAL_PROPERTY_RUNS.md
git diff --cached --stat
git diff --cached
git commit -m "Audit Option C submission and preserve real property quiz evidence"
```

After creating your empty public repository, replace the URL and publish:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Then open the real GitHub repo signed out, confirm the pushed commit and required files, and try the clean setup above. Replace all placeholders in the guide/form only with verified links. Edit the reflection into your own words and paste the six requested form sections. Keep the demo visibly pending/local-only unless you deploy and verify it; if deployed, say whether visitors can take samples, generate quizzes, or both.

## Submission commit follow-up

All nine audited paths were selected for the submission commit. Added `pytest.ini` to limit discovery to `tests/`, because ignored audit copies under `artifacts/` otherwise cause duplicate-module collection errors. Local environments, runtime binaries, model weights, logs, caches and audit scratch copies remain ignored. Publication is still managed by the repository owner.
