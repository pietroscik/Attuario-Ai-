# Piano di valutazione attuariale per attuario.eu

Questo documento descrive il framework di audit attuariale basato su crawl pubblico, insieme all'implementazione operativa disponibile nella cartella `attuario_ai`.

## IDEA BURST — 10 idee per integrazione AI nel dominio attuario.eu

1. Pipeline di QA automatica dei contenuti con modello LLM + checker numerico per verifiche matematiche.
2. Classificatore degli articoli per argomento attuariale (longevità, tariffe, riserve, Solvency II).
3. Estrattore strutturato di formule e parametri (LaTeX riconosciuto, convertito in JSON).
4. Sistema di segnatura di rischio/affidabilità per ogni articolo (score probabilistico).
5. Motore di ricerca semantico con retrieval-powered generation per risposte attuariali contestuali.
6. Dashboard KPI attuariali (tassi, ipotesi, date di aggiornamento, riferimenti bibliografici).
7. Alert automatici per contenuti obsoleti o conflitti con normative recenti.
8. Generatore di sintesi executive e versione “verificata” con calcoli eseguiti e fonti.
9. Modulo di test dei calcoli (unit tests numerici) che esegue esempi presenti negli articoli.
10. Sistema di crowdsourced peer review con firma digitale e integrazione dei revisori (anonimizzato).

## TOP PICKS — 3 idee selezionate con giustificazione

1. **Pipeline di QA automatica**: massimizza affidabilità, riduce rischio di errori numerici; priorità alta per dominio attuariale.
2. **Estrattore di formule/parametri**: abilita riuso, simulazioni e test automatici; elevato ROI tecnico.
3. **Sistema di segnatura di rischio/affidabilità**: fornisce punteggio leggibile agli utenti e supporta governance dei contenuti.

## PROTOTIPO TECNICO — architettura proposta (per MVP)

- **Crawl & ingest**: crawler Scrapy o requests/BeautifulSoup per scaricare pagine pubbliche.
- **Preprocessing**: parser HTML → testo, normalizzazione metadata (titolo, date, autore).
- **NLP & Extraction**: riconoscimento di entità attuariali, parsing di formule, raccolta di valori numerici.
- **Scoring & QA**: calcolo punteggi sulle dimensioni accuratezza, trasparenza, completezza, aggiornamento, chiarezza.
- **Storage & Index**: report CSV/JSON + eventuale indice full-text.
- **Dashboard**: interfaccia per revisori con elenco articoli, score, difetti identificati.

> **Implementazione**: il repository include ora la pipeline `EvaluationPipeline` (vedi `attuario_ai/pipeline.py`) che realizza il flusso end-to-end con crawler, parser, estrazione metrica e scoring.

## LIVELLO DI AUTOMAZIONE (mappa delle attività)

- **Full automation**: crawling, extraction struttura, calcolo punteggi heuristici, esportazione report.
- **Semi-automation**: revisione qualitativa su pagine con punteggio basso, verifica manuale delle segnalazioni.
- **Manuale**: approvazione finale da attuario esperto per contenuti critici.

## VALUTAZIONE QUALITÀ — metodologia e scoring esemplificativo

- **Accuratezza numerica (0–100)**: presenza di numeri, formule, densità informativa.
- **Trasparenza (0–100)**: citazioni normative e riferimenti istituzionali.
- **Completezza (0–100)**: presenza di tabelle, liste, terminologia attuariale chiave.
- **Aggiornamento (0–100)**: data di pubblicazione/modifica (ISO 8601) con decadimento annuale.
- **Chiarezza (0–100)**: equilibrio tra testo e numeri (evita overload numerico).

Il punteggio composito è dato da: `0.4*accuratezza + 0.2*trasparenza + 0.2*completezza + 0.1*aggiornamento + 0.1*chiarezza`.

> **Calibrazione dinamica**: il modulo `attuario_ai/learning.py` e lo script `scripts/train_weights.py` permettono di apprendere pesi aggiornati partendo da revisioni manuali (`labels.json`). Il fitting avviene con regressione ai minimi quadrati e il report restituisce MAE/MSE per monitorare la bontà dell'apprendimento.

Classificazione finale:

- ≥85: **Eccellente**
- 70–84: **Buono**
- 50–69: **Discreto**
- <50: **Criticità**

## ESTRAZIONE METRICHE — lista automatizzabile

- Conteggio parole e valori numerici.
- Rilevamento terminologia attuariale (Solvency II, IVASS, riserva, ecc.).
- Presenza di formule (LaTeX o simboli matematici), tabelle HTML, liste strutturate.
- Citazioni normative (regex dedicate).
- Valori numerici campione per ripetibilità di test.

Nel codice, queste metriche sono prodotte da `extract_metrics` (`attuario_ai/extraction.py`).

## AUTOMAZIONE AGGIORNAMENTI — workflow consigliato

1. Scheduler (cron/GitHub Actions) lancia `scripts/run_pipeline.py` con cadenza settimanale.
2. Output CSV/JSON archiviati con timestamp per audit trail.
3. Delta score > soglia genera alert (email/Slack) verso team contenuti.
4. Log versionati con Git/DB per assicurare tracciabilità.
5. Ogni ciclo di revisione manuale alimenta `scripts/train_weights.py` per aggiornare i pesi e chiudere il loop di apprendimento.

## NEXT-STEP — estensioni future

- Integrare parsing avanzato delle sitemap (il crawler ora rispetta già `robots.txt`).
- Aggiungere modello NLP (spaCy/transformer) per classificazioni più accurate.
- Implementare test numerici property-based sui valori estratti.
- Collegare pipeline a dashboard BI (Metabase/Superset) per monitoraggio continuo.

## ESERCIZIO DI CREATIVITÀ (SCAMPER)

Applicazione SCAMPER per migliorare un articolo tecnico:

1. **Substitute**: sostituire esempi statici con notebook interattivo condiviso.
2. **Combine**: unire normativa e caso pratico in percorso unico.
3. **Adapt**: adattare modelli standard a dati italiani.
4. **Modify**: aggiungere checklist di controllo a fine articolo.
5. **Put to another use**: trasformare contenuti in casi di test automatizzati.
6. **Eliminate**: rimuovere calcoli ridondanti non verificabili.
7. **Reverse**: mostrare prima gli errori comuni, poi la soluzione corretta.

## Suggerimenti di studio

- Glossario: mortalità, tasso tecnico, riserva matematica, best estimate, risk margin.
- Routine consigliata: 1h al giorno per 30 giorni tra letture normative, riproduzione calcoli e revisione report pipeline.
