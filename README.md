# Attuario-Ai-

[![Tests](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/tests.yml/badge.svg)](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/tests.yml)
[![Lint](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/lint.yml/badge.svg)](https://github.com/pietroscik/Attuario-Ai-/actions/workflows/Pylint-lint.yml)# Attuario-Ai-

Toolkit per valutazione automatica dei contenuti attuariali del dominio attuario.eu.

## Funzionalità principali

- **Crawler** limitato al dominio per raccogliere pagine HTML pubbliche e rispettoso di `robots.txt`.
- **Parser** HTML → testo con estrazione di metadata (titolo, date, autore).
- **Estrazione metriche** attuariali (terminologia, numeri, formule, citazioni normative).
- **Scoring** composito secondo i pesi del framework attuariale proposto (accuratezza, trasparenza, completezza, aggiornamento, chiarezza) con possibilità di calibrazione dai feedback umani.
- **Reportistica** in formato CSV e JSON con riepilogo sintetico delle performance del dominio.

## Requisiti

- Python 3.10+
- Dipendenze elencate in `requirements.txt`

Installazione delle dipendenze:

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

## Struttura del progetto

```
attuario_ai/
  crawler.py      # crawler BFS sul dominio
  parser.py       # parser HTML → testo + metadata
  extraction.py   # metriche euristiche dei contenuti
  scoring.py      # calcolo punteggi e classificazione
  learning.py     # apprendimento dei pesi da feedback manuali
  pipeline.py     # orchestrazione e generazione report
scripts/
  run_pipeline.py # CLI per eseguire la pipeline completa
  train_weights.py # CLI per calibrare i pesi
```

## Limitazioni note

- Lo scoring è euristico: necessita calibrazione con revisione umana.
- Il rispetto di `robots.txt` dipende dalle direttive pubblicate dal sito (crawl-delay e permessi).
- La verifica numerica è basata su presenze di valori e formule, non sulla correttezza dei calcoli.

## Prossimi passi suggeriti

- Integrare unit test numerici sui valori estratti dal testo.
- Aggiungere un modello NLP per classificare tipologia degli articoli.
- Collegare pipeline a scheduler (cron/CI) per aggiornamenti periodici.
