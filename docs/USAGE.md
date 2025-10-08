# Guida all'utilizzo - Attuario AI

Questa guida fornisce esempi pratici su come utilizzare Attuario AI per valutare la qualità dei contenuti attuariali su attuario.eu.

## Installazione rapida

```bash
# Clona il repository
git clone https://github.com/pietroscik/Attuario-Ai-.git
cd Attuario-Ai-

# Installa le dipendenze
pip install -r requirements.txt
```

## Esecuzione della pipeline su attuario.eu

### Esempio 1: Analisi base

Esegui una scansione rapida di 25 pagine con profondità 1:

```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --max-pages 25 \
  --max-depth 1 \
  --delay 0.2 \
  --output-dir outputs
```

**Cosa fa questo comando:**
- Inizia dal dominio `https://www.attuario.eu`
- Raccoglie fino a 25 pagine
- Segue i link fino a 1 livello di profondità
- Attende 0.2 secondi tra le richieste (politeness)
- Salva i risultati nella cartella `outputs/`

**Output generato:**
```
outputs/
  ├── report.csv         # Riepilogo tabellare per ogni pagina
  ├── report.json        # Dati completi in formato JSON
  └── summary.json       # Statistiche aggregate
```

### Esempio 2: Scansione approfondita

Per una scansione più estesa:

```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --max-pages 100 \
  --max-depth 2 \
  --delay 0.5 \
  --output-dir outputs/deep_scan
```

**Parametri:**
- `--max-pages 100`: raccoglie fino a 100 pagine
- `--max-depth 2`: segue i link fino a 2 livelli
- `--delay 0.5`: attesa di 0.5 secondi tra richieste (più rispettoso)

### Esempio 3: Utilizzo di pesi personalizzati

Se hai calibrato pesi personalizzati con feedback umano:

```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --max-pages 50 \
  --weights pesi_calibrati.json \
  --output-dir outputs/custom_weights
```

Il file `pesi_calibrati.json` deve contenere:

```json
{
  "accuracy": 0.35,
  "transparency": 0.25,
  "completeness": 0.25,
  "freshness": 0.10,
  "clarity": 0.05
}
```

## Esempi di output

### Report CSV (report.csv)

```csv
url,title,score,classification,accuracy,transparency,completeness,freshness,clarity,word_count,numeric_tokens,has_formula,has_table,has_list,citation_matches,actuarial_terms
https://www.attuario.eu/articolo-1,Introduzione a Solvency II,82.5,Buono,85.0,75.0,80.0,90.0,78.0,1250,45,True,True,True,3,solvency ii:5; ivass:2; scr:3
https://www.attuario.eu/articolo-2,Best Estimate Liabilities,76.8,Buono,80.0,70.0,75.0,85.0,72.0,980,38,False,True,True,2,best estimate:4; riserva:3
https://www.attuario.eu/articolo-3,Risk Margin Calculation,88.2,Eccellente,90.0,85.0,88.0,92.0,80.0,1450,62,True,True,True,5,risk margin:6; scr:4; solvency ii:3
```

### Report JSON (report.json)

```json
[
  {
    "page": {
      "url": "https://www.attuario.eu/articolo-1",
      "title": "Introduzione a Solvency II",
      "metadata": {
        "language": "it",
        "description": "Guida completa alla direttiva Solvency II...",
        "published": "2023-06-15T10:30:00Z",
        "modified": "2024-01-20T14:22:00Z",
        "author": "Mario Rossi"
      },
      "fetched_at": "2024-01-25T09:15:30.123456+00:00"
    },
    "metrics": {
      "word_count": 1250,
      "actuarial_terms": {
        "solvency ii": 5,
        "ivass": 2,
        "scr": 3,
        "best estimate": 2
      },
      "numeric_tokens": 45,
      "has_formula": true,
      "has_table": true,
      "has_list": true,
      "citation_matches": 3,
      "example_values": [100.0, 250.5, 1500.0, 2.5, 95.0]
    },
    "score": {
      "url": "https://www.attuario.eu/articolo-1",
      "composite": 82.5,
      "components": {
        "accuracy": 85.0,
        "transparency": 75.0,
        "completeness": 80.0,
        "freshness": 90.0,
        "clarity": 78.0
      },
      "classification": "Buono"
    }
  }
]
```

### Summary JSON (summary.json)

```json
{
  "count": 25,
  "average": 73.45,
  "minimum": 52.30,
  "maximum": 91.20
}
```

## Interpretazione dei risultati

### Punteggi delle componenti

Ogni pagina viene valutata su 5 dimensioni (0-100):

1. **Accuracy (Accuratezza)**: Valuta la presenza di dati numerici e formule
   - ≥80: Ricco di dati quantitativi e formule
   - 60-79: Presenza moderata di numeri
   - <60: Scarsa quantificazione

2. **Transparency (Trasparenza)**: Misura le citazioni normative
   - ≥80: Molti riferimenti a IVASS, EIOPA, normative
   - 60-79: Alcune citazioni presenti
   - <60: Poche o nessuna citazione

3. **Completeness (Completezza)**: Valuta ricchezza terminologica e strutturale
   - ≥80: Ricco di termini tecnici, tabelle, liste
   - 60-79: Contenuto discretamente completo
   - <60: Contenuto basilare

4. **Freshness (Aggiornamento)**: Considera la data di pubblicazione/modifica
   - ≥80: Contenuto recente (< 6 mesi)
   - 60-79: Contenuto relativamente recente (6-12 mesi)
   - <60: Contenuto datato (> 1 anno)

5. **Clarity (Chiarezza)**: Rapporto testo/numeri
   - ≥80: Buon equilibrio tra testo esplicativo e dati
   - 60-79: Accettabile
   - <60: Troppi numeri senza contesto o troppo generico

### Classificazioni complessive

Il punteggio composito (0-100) determina la classificazione:

- **Eccellente** (≥85): Contenuti di riferimento, altamente tecnici e aggiornati
- **Buono** (70-84): Contenuti validi, possono essere migliorati
- **Discreto** (50-69): Contenuti base, necessitano miglioramenti
- **Criticità** (<50): Contenuti insufficienti o obsoleti, da rivedere

## Calibrazione dei pesi con feedback umano

Se vuoi addestrare il sistema sui tuoi giudizi di qualità:

### Passo 1: Crea un file di labels

Crea `labels.json` con le tue valutazioni:

```json
[
  {"url": "https://www.attuario.eu/articolo-1", "target_score": 85.0},
  {"url": "https://www.attuario.eu/articolo-2", "target_score": 62.0},
  {"url": "https://www.attuario.eu/articolo-3", "target_score": 90.0},
  {"url": "https://www.attuario.eu/articolo-4", "target_score": 55.0}
]
```

### Passo 2: Addestra i pesi

```bash
python scripts/train_weights.py https://www.attuario.eu labels.json \
  --output pesi_calibrati.json
```

**Output atteso:**
```
Fetched 4 pages for training
Training results:
  MAE: 5.23
  MSE: 42.15
Optimized weights saved to pesi_calibrati.json
```

### Passo 3: Usa i pesi calibrati

```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --weights pesi_calibrati.json \
  --max-pages 50 \
  --output-dir outputs/calibrated
```

## Utilizzo programmatico

### Esempio Python completo

```python
from attuario_ai import EvaluationPipeline, ScoreWeights

# Configura pesi personalizzati
weights = ScoreWeights(
    accuracy=0.35,
    transparency=0.25,
    completeness=0.25,
    freshness=0.10,
    clarity=0.05
)

# Esegui la pipeline
with EvaluationPipeline(
    "https://www.attuario.eu",
    max_pages=50,
    max_depth=2,
    delay_seconds=0.5,
    weights=weights
) as pipeline:
    # Esegui l'analisi
    results = pipeline.run()

    # Esporta in CSV e JSON
    from pathlib import Path
    output_dir = Path("outputs")
    pipeline.export_csv(results, output_dir / "report.csv")
    pipeline.export_json(results, output_dir / "report.json")

    # Calcola statistiche
    summary = pipeline.summary(results)
    print(f"Analyzed {summary['count']} pages")
    print(f"Average score: {summary['average']}")
    print(f"Score range: {summary['minimum']} - {summary['maximum']}")

    # Mostra dettagli delle pagine migliori
    sorted_results = sorted(results, key=lambda r: r.score.composite, reverse=True)
    print("\nTop 5 pages:")
    for result in sorted_results[:5]:
        print(f"  {result.score.composite:.1f} - {result.page.title}")
        print(f"    URL: {result.page.url}")
        print(f"    Classification: {result.score.classification}")
```

### Analisi di singole pagine

```python
from attuario_ai import PageParser, extract_metrics, score_page, ScoreWeights
import requests
import time

# Fetch una singola pagina
url = "https://www.attuario.eu/articolo-esempio"
response = requests.get(url)
html = response.text
timestamp = time.time()

# Parse
parser = PageParser()
parsed = parser.parse(url, html, timestamp)

# Estrai metriche
metrics = extract_metrics(parsed.text, parsed.html)

# Calcola score
metadata = {**parsed.metadata, "url": parsed.url}
weights = ScoreWeights()
score = score_page(metrics, metadata, weights)

# Risultati
print(f"Page: {parsed.title}")
print(f"Score: {score.composite} ({score.classification})")
print(f"Components:")
for component, value in score.components.items():
    print(f"  {component}: {value}")
```

## Best practices

1. **Rispetta il delay**: Usa almeno 0.2 secondi tra le richieste, meglio 0.5 per siti in produzione
2. **Limita max_pages**: Inizia con 25-50 pagine per test, aumenta gradualmente
3. **Controlla robots.txt**: Il crawler rispetta automaticamente robots.txt
4. **Calibra i pesi**: Usa il training per adattare i pesi al tuo dominio specifico
5. **Monitora il summary**: Controlla le statistiche aggregate per identificare trend

## Troubleshooting

### Errore: "Too many requests"

Aumenta il delay:
```bash
python scripts/run_pipeline.py https://www.attuario.eu --delay 1.0
```

### Errore: "No pages crawled"

Verifica che il sito sia raggiungibile e che robots.txt permetta il crawling:
```python
from attuario_ai import Crawler
crawler = Crawler("https://www.attuario.eu")
print(f"Allowed: {crawler._robots.is_allowed('https://www.attuario.eu/')}")
```

### Punteggi troppo bassi o troppo alti

Calibra i pesi usando feedback umano (vedi sezione "Calibrazione dei pesi").

## Prossimi passi

Dopo aver eseguito le prime analisi:

1. Identifica le pagine con punteggi bassi e analizza le cause
2. Crea un dataset di labels manuale per calibrare i pesi
3. Confronta i risultati prima e dopo la calibrazione
4. Integra la pipeline in un workflow CI/CD per monitoraggio continuo
5. Esporta i report in formati visualizzabili (dashboard, grafici)
