# ML Module - Machine Learning Integration

This module provides machine learning capabilities for scoring actuarial content, offering an alternative to rule-based heuristics.

## Overview

The ML module includes:

- **BaselineMLModel**: TF-IDF + Logistic Regression baseline model
- **MLPredictor**: Predictor interface for scoring pages using trained models
- **train_baseline.py**: Training script for the baseline model

## Quick Start

### 1. Prepare Training Data

Create a `labels.json` file with labeled pages:

```json
[
  {"url": "https://www.attuario.eu/articolo-1", "target_score": 85.0},
  {"url": "https://www.attuario.eu/articolo-2", "target_score": 62.0},
  {"url": "https://www.attuario.eu/articolo-3", "target_score": 90.0},
  {"url": "https://www.attuario.eu/articolo-4", "target_score": 55.0}
]
```

### 2. Train the Model

```bash
python ml/train_baseline.py https://www.attuario.eu labels.json --output-dir ml/models
```

This will:
- Crawl the specified pages
- Extract text content
- Train a TF-IDF + Logistic Regression classifier
- Save the model to `ml/models/model.pkl` and `ml/models/vectorizer.pkl`

### 3. Use the Trained Model

**ML Mode (machine learning only):**

```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --mode ml \
  --model-dir ml/models \
  --max-pages 50
```

**Hybrid Mode (heuristic + ML):**

```bash
python scripts/run_pipeline.py https://www.attuario.eu \
  --mode hybrid \
  --model-dir ml/models \
  --max-pages 50
```

## Model Architecture

### Baseline Model (TF-IDF + Logistic Regression)

The baseline model uses a simple but effective approach:

1. **Text Vectorization**: TF-IDF (Term Frequency-Inverse Document Frequency)
   - Max features: 500
   - N-gram range: (1, 2) - unigrams and bigrams
   - Stop words: English

2. **Classification**: Logistic Regression
   - Scores are binned into 4 classes:
     - Class 0: 0-50 (Criticità) → midpoint 25.0
     - Class 1: 50-70 (Discreto) → midpoint 60.0
     - Class 2: 70-85 (Buono) → midpoint 77.5
     - Class 3: 85-100 (Eccellente) → midpoint 92.5

3. **Evaluation**: MAE and MSE on held-out test set

## Scoring Modes

### Heuristic Mode (default)
- Uses rule-based scoring with domain-specific metrics
- Components: accuracy, transparency, completeness, freshness, clarity
- Good for interpretability and domain knowledge

### ML Mode
- Uses trained machine learning model
- Learns patterns from labeled data
- Better for generalization to unseen pages

### Hybrid Mode
- Combines both approaches
- Averages heuristic and ML scores
- Balances domain rules with learned patterns
- Includes both component scores and ML score in output

## Example Usage

See `examples/ml_modes_comparison.py` for a complete example comparing all three modes.

```python
from ml.baseline_model import BaselineMLModel
from ml.predictor import MLPredictor

# Train model
model = BaselineMLModel()
metrics = model.train(texts, scores)

# Save model
model.save(Path("models/model.pkl"), Path("models/vectorizer.pkl"))

# Load and use for prediction
predictor = MLPredictor(model_dir=Path("models"))
score = predictor.score_page(text, metrics, metadata)
```

## API Reference

### BaselineMLModel

**Methods:**
- `train(texts, scores, test_size=0.2)`: Train the model on labeled data
- `predict(texts)`: Predict scores for new texts
- `save(model_path, vectorizer_path)`: Save trained model to disk
- `load(model_path, vectorizer_path)`: Load model from disk

**Properties:**
- `is_trained`: Check if model has been trained

### MLPredictor

**Methods:**
- `__init__(model_dir=None)`: Initialize predictor, optionally loading from directory
- `score_page(text, metrics, metadata)`: Score a page using ML model

## Testing

Run ML tests:

```bash
pytest tests/test_ml.py -v
```

## Performance Considerations

- **Training time**: Fast (seconds for small datasets)
- **Prediction time**: Very fast (milliseconds per page)
- **Memory usage**: Low (model size ~100KB)
- **Accuracy**: Depends on training data quality and quantity

## Future Enhancements

Potential improvements:
- Deep learning models (BERT, transformers)
- Word embeddings (Word2Vec, GloVe)
- Ensemble methods
- Multi-task learning (predicting components separately)
- Active learning for efficient labeling
