# 🤖 Codex Instructions – Attuario-Ai

Questi sono i commenti pronti da incollare nelle rispettive issue del repository per guidare Codex nello sviluppo.

---

## 🔹 Issue #2 / #3 – Testing e CI
```
@codex add pytest tests for parser.py, extraction.py and scoring.py.
Include simple input/output examples.
Also create a GitHub Actions workflow .github/workflows/tests.yml that runs pytest automatically on each push.
```

---

## 🔹 Issue #4 – Documentazione
```
@codex expand the README with explanations for the main modules (crawler, parser, extraction, scoring).
Also create a docs/USAGE.md with examples of how to run the pipeline on attuario.eu and sample output.
```

---

## 🔹 Issue #5 – Logging e Robustezza
```
@codex add Python logging to crawler.py and parser.py with INFO, WARNING and ERROR levels.
Log to both console and a file logs/pipeline.log.
Ensure that network errors (timeouts, unreachable pages) are caught with try/except and retries.
```

---

## 🔹 Issue #6 – Integrazione Machine Learning
```
@codex create an ml/ folder with a baseline script that trains a TF-IDF + Logistic Regression model on labels.json.
Add a CLI option --mode {heuristic|ml|hybrid} to pipeline.py to select the scoring method.
```

---

## 🔹 Issue #7 – Performance e Scalabilità
```
@codex optimize crawler.py to support parallel requests using asyncio or concurrent.futures.
Add caching with requests_cache to avoid repeated downloads.
Add a CLI option --depth to limit BFS crawling depth.
```

---

## 🔹 Issue #8 – Esempi e Benchmark
```
@codex create an examples/ folder with 2–3 static HTML pages and an expected_output.json file.
Update README with a Benchmark section showing sample results from the pipeline.
```

---

## 🔹 Issue #9 – CI/CD e Deployment
```
@codex add a Dockerfile with Python 3.10, install requirements, and set entrypoint to run pipeline.py.
Extend GitHub Actions workflow to run flake8 linting.
(Optional) add a simple FastAPI endpoint /score?url= that returns a JSON with the page score.
```

---

## 🔹 Issue #10 – Versioning e Release
```
@codex add a CHANGELOG.md with v0.1.0 initial release.
Add pyproject.toml so the project can be installed with pip.
Use semantic versioning in future releases.
```
