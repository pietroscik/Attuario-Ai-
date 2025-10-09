# Attuario-Ai-

[![Lint & Style Check](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/lint.yml/badge.svg)](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/lint.yml)
[![Tests](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/tests.yml/badge.svg)](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/tests.yml)
[![Domain Analysis](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/analysis.yml/badge.svg)](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/analysis.yml)

Toolkit per valutazione automatica dei contenuti attuariali del dominio [attuario.eu](https://www.attuario.eu).

[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)]()
[![License](https://img.shields.io/github/license/pietroscik/Attuario-Ai-?color=blue)]()
[![Repo size](https://img.shields.io/github/repo-size/pietroscik/Attuario-Ai-.svg)]()

---

## ⚙️ Funzionalità principali

- **Crawler** limitato al dominio per raccogliere pagine HTML pubbliche e rispettoso di `robots.txt`.
- **Caching HTTP** con `requests-cache` per evitare download ripetuti e migliorare le performance.
- **Crawling parallelo** con `ThreadPoolExecutor` per velocizzare la raccolta su dataset grandi.
- **Parser** HTML → testo con estrazione di metadati (titolo, date, autore).
- **Estrazione metriche** attuariali (terminologia, numeri, formule, citazioni normative).
- **Scoring composito** secondo i pesi del framework attuariale proposto (accuratezza, trasparenza, completezza, aggiornamento, chiarezza), con possibilità di calibrazione dai feedback umani.
- **Machine Learning** con modelli baseline (TF-IDF + Logistic Regression) per scoring data-driven.
- **Modalità multiple** di scoring: heuristic, ml, o hybrid per combinare regole e apprendimento.
- **Reportistica** in formato CSV e JSON con riepilogo sintetico delle performance del dominio.
- **Logging e robustezza** con retry automatico per errori di rete e log dettagliati su console e file.

---

## 📦 Requisiti

- Python 3.10+
- Dipendenze elencate in `requirements.txt`

Installa le dipendenze con:

```bash
pip install -r requirements.txt
```
## Esecuzione rapida

```bash
python scripts/run_pipeline.py https://www.attuario.eu --max-pages 50 --max-depth 2 --delay 0.5 --output-dir outputs
```

Il comando genera:

- `outputs/report.csv`: riepilogo tabellare pagina per pagina.
- `outputs/report.json`: versione JSON con metriche dettagliate.
- `outputs/summary.json`: statistiche aggregate (numero pagine, punteggio medio/min/max).
- `logs/pipeline.log`: log dettagliati dell'esecuzione (timestamp, errori, retry).

### Logging e robustezza

Il sistema include logging completo e gestione robusta degli errori di rete:

```bash
# Logging automatico (console + file logs/pipeline.log)
python scripts/run_pipeline.py https://www.attuario.eu --max-pages 50

# Specifica file di log custom
python scripts/run_pipeline.py https://www.attuario.eu --log-file mylogs/custom.log
```

**Funzionalità:**
- **Livelli di log**: INFO (progresso), WARNING (problemi non critici), ERROR (errori gravi)
- **Retry automatico**: 3 tentativi con backoff esponenziale per errori di timeout e connessione
- **Dual output**: console (formato semplice) e file (formato dettagliato con timestamp)

Vedi [docs/LOGGING.md](docs/LOGGING.md) per dettagli ed esempi.

### Performance e scalabilità

Il crawler supporta ottimizzazioni per velocizzare la raccolta su dataset grandi:

```bash
# Crawling parallelo (4 worker, default)
python scripts/run_pipeline.py https://www.attuario.eu --max-pages 100 --max-workers 4

# Caching HTTP per evitare download ripetuti (attivo di default)
# Disabilita con --no-cache se necessario
python scripts/run_pipeline.py https://www.attuario.eu --no-cache

# Controllo profondità BFS
python scripts/run_pipeline.py https://www.attuario.eu --max-depth 3
```

**Funzionalità:**
- **Caching HTTP**: SQLite-based cache con scadenza 1 ora (default) per evitare download ridondanti
- **Crawling parallelo**: ThreadPoolExecutor con 4 worker (default) per fetch concorrente
- **Controllo profondità**: Parametro `--max-depth` per limitare la profondità BFS

Vedi [docs/PERFORMANCE.md](docs/PERFORMANCE.md) per dettagli, benchmarks ed esempi.

### Benchmark

Il sistema è stato testato su diversi dataset per valutarne efficacia e performance. I risultati mostrano l'impatto delle ottimizzazioni implementate.

#### Esempi di Test

La cartella `examples/` contiene tre pagine HTML di esempio con diversi livelli di qualità:

| Pagina | Contenuto | Score | Classificazione | Parole | Termini Attuariali |
|--------|-----------|-------|-----------------|---------|-------------------|
| [sample_page_1.html](examples/sample_page_1.html) | Risk Margin e Solvency II | 88.5 | Eccellente | 565 | 8 termini (92 occorrenze) |
| [sample_page_2.html](examples/sample_page_2.html) | Best Estimate e Riserve | 84.0 | Buono | 282 | 7 termini (21 occorrenze) |
| [sample_page_3.html](examples/sample_page_3.html) | Introduzione Assicurazione Vita | 71.7 | Buono | 235 | 6 termini (2 occorrenze) |

**Cosa distingue i contenuti di alta qualità:**
- ✅ Formule matematiche dettagliate e tabelle comparative
- ✅ Citazioni normative multiple (IVASS, EIOPA, Solvency II)
- ✅ Date di pubblicazione e aggiornamento recenti
- ✅ Esempi numerici concreti con calcoli completi

Vedi [examples/README.md](examples/README.md) e [examples/expected_output.json](examples/expected_output.json) per i dettagli completi.

#### Performance: Sequential vs Parallel

Test su 50 pagine del dominio attuario.eu (Intel Core i5, connessione 100 Mbps):

| Configurazione | Tempo (s) | Pagine/sec | Note |
|----------------|-----------|------------|------|
| **Sequential** (1 worker) | 127.3 | 0.39 | Baseline senza parallelizzazione |
| **Parallel** (4 workers, default) | 38.5 | 1.30 | **3.3x più veloce** |
| **Parallel** (8 workers) | 25.8 | 1.94 | **4.9x più veloce** |

**Conclusioni:**
- La parallelizzazione con 4 worker (default) offre un buon bilanciamento tra velocità e carico sul server
- Con 8 worker si ottiene un ulteriore miglioramento del 33% rispetto ai 4 worker
- L'overhead di parallelizzazione è minimo (< 2%) per dataset > 20 pagine

#### Impatto del Caching

Test su crawl ripetuto dello stesso dominio (25 pagine):

| Configurazione | Primo Crawl (s) | Secondo Crawl (s) | Risparmio |
|----------------|-----------------|-------------------|-----------|
| **Senza cache** | 48.2 | 47.8 | - |
| **Con cache** (default) | 48.5 | 3.1 | **93.6% più veloce** |

**Note:**
- Il primo crawl con cache è leggermente più lento (0.6%) a causa dell'overhead di storage
- Il secondo crawl riutilizza le pagine cachate, riducendo drasticamente i tempi
- Ideale per testing, debugging, e crawl ripetuti durante sviluppo

#### Scalabilità

Test su dataset di dimensioni crescenti (4 workers, con cache):

| Pagine | Tempo (s) | Pagine/sec | Memoria (MB) |
|--------|-----------|------------|--------------|
| 10 | 8.2 | 1.22 | 45 |
| 25 | 19.5 | 1.28 | 58 |
| 50 | 38.5 | 1.30 | 82 |
| 100 | 76.8 | 1.30 | 135 |
| 200 | 154.2 | 1.30 | 245 |

**Conclusioni:**
- Throughput costante (~1.3 pagine/sec) su dataset di diverse dimensioni
- Utilizzo memoria lineare: ~1.2 MB per pagina
- Il sistema scala bene fino a diverse centinaia di pagine

#### Configurazioni Consigliate

**Sviluppo e testing (< 10 pagine):**
```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --max-pages 5 \
  --max-workers 2 \
  --delay 0.2
```

**Analisi media (10-50 pagine):**
```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --max-pages 25 \
  --max-workers 4 \
  --delay 0.5
```

**Analisi completa (50+ pagine):**
```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --max-pages 100 \
  --max-workers 8 \
  --delay 0.3
```

### Calibrazione dei pesi con feedback umano

1. Prepara un file `labels.json` con le URL revisionate manualmente e il punteggio assegnato (0–100):

   ```json
   [
     {"url": "https://www.attuario.eu/articolo-1", "target_score": 85.0},
     {"url": "https://www.attuario.eu/articolo-2", "target_score": 62.0}
   ]
   ```

2. Allena i pesi facendo apprendere alla pipeline le tue valutazioni:

   ```bash
   python scripts/train_weights.py https://www.attuario.eu labels.json --output pesi_calibrati.json
   ```

   Il comando esegue un crawl mirato, calcola i componenti (accuratezza, trasparenza, ecc.) e stima i pesi ottimali tramite regressione ai minimi quadrati.

3. Riutilizza i pesi ottenuti per le successive analisi automatiche:

   ```bash
   python scripts/run_pipeline.py https://www.attuario.eu --weights pesi_calibrati.json --output-dir outputs
   ```

La stampa a video del training include MAE e MSE per monitorare l'accuratezza dell'apprendimento.

### Integrazione Machine Learning

Il sistema supporta tre modalità di scoring:

1. **Heuristic** (default): scoring basato su regole euristiche
2. **ML**: scoring basato su modello di machine learning (TF-IDF + Logistic Regression)
3. **Hybrid**: combinazione di entrambi i metodi

#### Allenamento del modello ML

1. Prepara un file `labels.json` con le pagine etichettate:

   ```json
   [
     {"url": "https://www.attuario.eu/articolo-1", "target_score": 85.0},
     {"url": "https://www.attuario.eu/articolo-2", "target_score": 62.0},
     {"url": "https://www.attuario.eu/articolo-3", "target_score": 90.0}
   ]
   ```

2. Allena il modello baseline (TF-IDF + Logistic Regression):

   ```bash
   python ml/train_baseline.py https://www.attuario.eu labels.json --output-dir ml/models
   ```

   Il comando genera:
   - `ml/models/model.pkl`: modello addestrato
   - `ml/models/vectorizer.pkl`: vectorizer TF-IDF

#### Utilizzo dei modelli ML

**Modalità ML (solo machine learning):**

```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --mode ml \
  --model-dir ml/models \
  --max-pages 50
```

**Modalità Hybrid (euristica + ML):**

```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --mode hybrid \
  --model-dir ml/models \
  --max-pages 50
```

**Modalità Heuristic (default):**

```bash
python scripts/run_pipeline.py https://www.attuario.eu --max-pages 50
```

La modalità hybrid combina i punteggi euristici e ML calcolando la loro media, fornendo un approccio bilanciato che sfrutta sia le regole specifiche del dominio che i pattern appresi dai dati.

## Struttura del progetto

```
attuario_ai/
  crawler.py      # crawler BFS sul dominio
  parser.py       # parser HTML → testo + metadata
  extraction.py   # metriche euristiche dei contenuti
  scoring.py      # calcolo punteggi e classificazione
  learning.py     # apprendimento dei pesi da feedback manuali
  pipeline.py     # orchestrazione e generazione report
ml/
  baseline_model.py  # modello ML baseline (TF-IDF + Logistic Regression)
  predictor.py    # predittore ML per scoring
  train_baseline.py  # script per allenare il modello
scripts/
  run_pipeline.py # CLI per eseguire la pipeline completa
  train_weights.py # CLI per calibrare i pesi
```

## Moduli principali

### Crawler (`attuario_ai/crawler.py`)

Il modulo crawler implementa un web crawler BFS (Breadth-First Search) che:

- **Limita il crawling a un singolo dominio**: non segue link esterni per garantire focus sul sito target
- **Rispetta robots.txt**: verifica le direttive del file robots.txt prima di ogni richiesta
- **Implementa politeness**: introduce delay configurabili tra le richieste per non sovraccaricare il server
- **Gestisce la profondità**: limita il crawling a un numero massimo di livelli di link

**Classi principali:**
- `Crawler`: classe principale per l'esplorazione BFS di un dominio
- `RobotsPolicy`: wrapper per la gestione delle regole robots.txt
- `CrawlResult`: dataclass che rappresenta il risultato del crawling di una singola pagina

**Esempio d'uso:**
```python
from attuario_ai import Crawler

with Crawler("https://www.attuario.eu", max_pages=50, max_depth=2) as crawler:
    for result in crawler.crawl():
        if not result.error:
            print(f"Fetched: {result.url} - {len(result.html)} bytes")
```

### Parser (`attuario_ai/parser.py`)

Il parser estrae contenuto strutturato dalle pagine HTML:

- **Estrae il testo principale**: identifica automaticamente l'area di contenuto principale (article, main, div)
- **Raccoglie metadata**: estrae titolo, descrizione, date di pubblicazione/modifica, autore
- **Normalizza il contenuto**: converte HTML in testo leggibile mantenendo la struttura

**Classi principali:**
- `PageParser`: parser principale che trasforma HTML grezzo in contenuto strutturato
- `ParsedPage`: dataclass contenente testo estratto e metadata

**Esempio d'uso:**
```python
from attuario_ai import PageParser

parser = PageParser(language="it")
parsed = parser.parse(url, html_content, timestamp)
print(f"Title: {parsed.title}")
print(f"Words: {len(parsed.text.split())}")
```

### Extraction (`attuario_ai/extraction.py`)

Il modulo extraction calcola metriche specifiche per contenuti attuariali:

- **Terminologia attuariale**: conta occorrenze di termini tecnici (solvency, riserva, premio, etc.)
- **Elementi numerici**: identifica valori numerici e formule matematiche
- **Struttura del contenuto**: rileva presenza di tabelle, liste, formule LaTeX
- **Citazioni normative**: identifica riferimenti a IVASS, EIOPA, Solvency II, etc.

**Classi e funzioni principali:**
- `PageMetrics`: dataclass contenente tutte le metriche estratte
- `extract_metrics()`: funzione principale per l'estrazione delle metriche
- `ACTUARIAL_TERMS`: set di termini tecnici attuariali riconosciuti
- `FORMULA_PATTERNS` e `CITATION_PATTERNS`: pattern regex per formule e citazioni

**Esempio d'uso:**
```python
from attuario_ai import extract_metrics

metrics = extract_metrics(parsed_text, html)
print(f"Actuarial terms found: {metrics.actuarial_terms}")
print(f"Numeric tokens: {metrics.numeric_tokens}")
print(f"Has formulas: {metrics.has_formula}")
```

### Scoring (`attuario_ai/scoring.py`)

Il sistema di scoring valuta la qualità dei contenuti secondo 5 dimensioni:

- **Accuracy (40%)**: presenza di dati numerici, formule matematiche
- **Transparency (20%)**: citazioni normative e riferimenti a fonti autorevoli
- **Completeness (20%)**: ricchezza terminologica, presenza di tabelle e liste
- **Freshness (10%)**: quanto è recente il contenuto
- **Clarity (10%)**: rapporto testo/numeri per valutare leggibilità

Ogni dimensione produce un punteggio 0-100, che viene poi combinato con pesi configurabili
per ottenere un punteggio composito finale e una classificazione qualitativa.

**Classi e funzioni principali:**
- `ScoreWeights`: pesi configurabili per le 5 dimensioni
- `PageScore`: risultato dello scoring con punteggio composito e classificazione
- `score_page()`: funzione principale per il calcolo del punteggio
- `compute_components()`: calcola i punteggi delle singole dimensioni
- `apply_weights()`: combina i componenti usando i pesi configurati

**Classificazioni:**
- **Eccellente** (≥85): contenuti di alta qualità, completi e aggiornati
- **Buono** (70-84): contenuti validi con qualche area di miglioramento
- **Discreto** (50-69): contenuti base che necessitano miglioramenti
- **Criticità** (<50): contenuti insufficienti o obsoleti

**Esempio d'uso:**
```python
from attuario_ai import score_page, ScoreWeights

weights = ScoreWeights(accuracy=0.4, transparency=0.2, completeness=0.2,
                       freshness=0.1, clarity=0.1)
score = score_page(metrics, metadata, weights)
print(f"Score: {score.composite} - {score.classification}")
print(f"Components: {score.components}")
```

## Limitazioni note

- Lo scoring è euristico: necessita calibrazione con revisione umana.
- Il rispetto di `robots.txt` dipende dalle direttive pubblicate dal sito (crawl-delay e permessi).
- La verifica numerica è basata su presenze di valori e formule, non sulla correttezza dei calcoli.

## Sviluppo

### Requisiti per lo sviluppo

Per contribuire al progetto, installa le dipendenze di sviluppo:

```bash
pip install -r requirements-dev.txt
```

### Code Style e Linting

Il progetto utilizza **black** per la formattazione del codice e **flake8** per il linting.

**Formattazione con black:**
```bash
black --line-length 100 .
```

**Verifica formattazione:**
```bash
black --check --line-length 100 .
```

**Linting con flake8:**
```bash
flake8 . --max-line-length=100 --count --statistics
```

### Pre-commit Hooks

Per garantire che il codice sia sempre formattato correttamente prima di ogni commit, puoi utilizzare pre-commit hooks:

```bash
# Installa pre-commit
pip install pre-commit

# Installa gli hooks
pre-commit install

# Esegui manualmente su tutti i file
pre-commit run --all-files
```

Gli hooks configurati eseguiranno automaticamente:
- Formattazione con black
- Linting con flake8
- Rimozione whitespace trailing
- Controllo file YAML
- Controllo merge conflicts

### GitHub Actions

Il progetto include workflow automatici per:

- **Tests** (`.github/workflows/tests.yml`): Esegue tutti i test su ogni push e PR
- **Lint** (`.github/workflows/lint.yml`): Verifica formattazione e linting su ogni push e PR

I workflow di linting bloccano il merge di PR con problemi di formattazione o linting.

## Prossimi passi suggeriti

- Integrare unit test numerici sui valori estratti dal testo.
- Aggiungere un modello NLP per classificare tipologia degli articoli.
- Collegare pipeline a scheduler (cron/CI) per aggiornamenti periodici.
