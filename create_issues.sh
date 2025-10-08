#!/bin/bash

# Script per aprire tutte le issue su pietroscik/Attuario-Ai-

gh issue create --title "Testing e CI" \
  --body "Obiettivo: introdurre test automatici per garantire stabilità del codice.
Azioni da fare:
- Creare cartella tests/ con pytest.
- Scrivere test unitari per parser.py, extraction.py, scoring.py.
- Integrare un workflow GitHub Actions (.github/workflows/tests.yml) che lanci i test ad ogni push." \
  --label "enhancement" --label "testing"

gh issue create --title "Documentazione" \
  --body "Obiettivo: rendere il progetto comprensibile anche a chi non lo conosce.
Azioni da fare:
- Aggiungere docstring a funzioni e classi (Google style).
- Ampliare README con spiegazioni su moduli principali.
- Creare docs/USAGE.md con esempi reali di input/output." \
  --label "documentation"

gh issue create --title "Logging e Robustezza" \
  --body "Obiettivo: aumentare affidabilità e tracciabilità della pipeline.
Azioni da fare:
- Introdurre sistema logging (livelli INFO, WARNING, ERROR).
- Gestire errori di rete nel crawler.py con try/except e retry.
- Salvare log in logs/pipeline.log." \
  --label "enhancement"

gh issue create --title "Integrazione Machine Learning" \
  --body "Obiettivo: superare i limiti delle regole euristiche.
Azioni da fare:
- Creare cartella ml/ con script baseline (TF-IDF o embeddings).
- Allineare modello supervisionato su labels.json.
- Integrare opzione CLI --mode {heuristic|ml|hybrid}." \
  --label "enhancement" --label "machine-learning"

gh issue create --title "Performance e Scalabilità" \
  --body "Obiettivo: rendere il crawler più veloce e utilizzabile su dataset grandi.
Azioni da fare:
- Parallelizzare il crawler con asyncio o concurrent.futures.
- Aggiungere caching con requests_cache.
- Parametro CLI --depth per controllare la profondità BFS." \
  --label "enhancement" --label "performance"

gh issue create --title "Esempi e Benchmark" \
  --body "Obiettivo: dimostrare l’efficacia del sistema.
Azioni da fare:
- Aggiungere cartella examples/ con HTML statici e output atteso.
- Documentare nel README una sezione Benchmark con risultati." \
  --label "documentation" --label "example"

gh issue create --title "CI/CD e Deployment" \
  --body "Obiettivo: facilitare l’utilizzo e il rilascio.
Azioni da fare:
- Workflow GitHub Actions con flake8 + pytest.
- Creare Dockerfile con ambiente pronto.
- (Opzionale) endpoint FastAPI /score?url= che restituisce JSON." \
  --label "enhancement" --label "ci/cd"

gh issue create --title "Versioning e Release" \
  --body "Obiettivo: preparare il progetto per distribuzione pubblica.
Azioni da fare:
- Aggiungere CHANGELOG.md.
- Usare tag semantici (v0.1.0, v0.2.0).
- Preparare pyproject.toml o setup.py per installazione via pip." \
  --label "enhancement" --label "release"
