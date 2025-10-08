# Machine Learning Integration - Implementation Summary

## Overview
Successfully integrated machine learning capabilities into the Attuario-Ai pipeline, enabling three scoring modes: heuristic, ML, and hybrid.

## What Was Implemented

### 1. ML Module (`ml/`)
- **baseline_model.py**: TF-IDF + Logistic Regression model
  - Vectorization with 500 max features, unigrams and bigrams
  - Classification into 4 quality bins
  - Training with train/test split and evaluation metrics (MAE, MSE)
  - Model save/load functionality

- **predictor.py**: ML-based scoring interface
  - Loads trained models from disk
  - Scores pages using ML predictions
  - Returns PageScore objects compatible with existing pipeline

- **train_baseline.py**: CLI training script
  - Crawls labeled pages from base URL
  - Trains model on text content
  - Saves trained model and vectorizer

- **__init__.py**: Module initialization and exports

### 2. Pipeline Integration
- **Modified `attuario_ai/pipeline.py`**:
  - Added `mode` parameter (heuristic, ml, hybrid)
  - Added `model_dir` parameter for loading trained models
  - Hybrid mode combines heuristic and ML scores by averaging
  - All three modes return compatible PageScore objects

- **Modified `scripts/run_pipeline.py`**:
  - Added `--mode` CLI option with choices: heuristic, ml, hybrid
  - Added `--model-dir` CLI option for specifying trained model location
  - Validation to require model-dir when using ml or hybrid modes

### 3. Testing
- **tests/test_ml.py**: Comprehensive ML tests (14 new tests)
  - Model initialization and training
  - Prediction with and without training
  - Save/load functionality
  - Predictor integration
  - Error handling for edge cases
  - All 70 tests pass (56 existing + 14 new)

### 4. Documentation
- **README.md**: Updated with ML integration section
  - Training workflow instructions
  - Usage examples for all three modes
  - Updated project structure to show ml/ directory

- **ml/README.md**: Detailed ML module documentation
  - Architecture description
  - API reference
  - Performance considerations
  - Future enhancement ideas

### 5. Examples
- **examples/ml_modes_comparison.py**: Working demonstration
  - Shows all three scoring modes on the same content
  - Displays scores, classifications, and breakdowns
  - Trains a model in the example for demonstration

- **labels.json**: Example training data format

### 6. Infrastructure
- **.gitignore**: Updated to exclude trained models and output directories

## Key Features

### Three Scoring Modes

1. **Heuristic Mode** (default)
   ```bash
   python scripts/run_pipeline.py https://www.attuario.eu --max-pages 50
   ```
   - Rule-based scoring with domain-specific metrics
   - Provides interpretable component scores

2. **ML Mode**
   ```bash
   python scripts/run_pipeline.py https://www.attuario.eu \
     --mode ml --model-dir ml/models --max-pages 50
   ```
   - Data-driven scoring using trained model
   - Learns patterns from labeled examples

3. **Hybrid Mode**
   ```bash
   python scripts/run_pipeline.py https://www.attuario.eu \
     --mode hybrid --model-dir ml/models --max-pages 50
   ```
   - Combines both approaches
   - Averages heuristic and ML scores
   - Best of both worlds

### Training Workflow

1. Create labels.json with scored pages
2. Train model:
   ```bash
   python ml/train_baseline.py https://www.attuario.eu labels.json \
     --output-dir ml/models
   ```
3. Use trained model for scoring (see modes above)

## Technical Details

### Model Architecture
- **Vectorizer**: TF-IDF (Term Frequency-Inverse Document Frequency)
- **Classifier**: Logistic Regression
- **Classes**: 4 quality bins (Criticità, Discreto, Buono, Eccellente)
- **Output**: Mapped to 0-100 score range

### Performance
- Training: Fast (seconds for small datasets)
- Prediction: Very fast (milliseconds per page)
- Model size: Small (~100KB)

## Testing Results
```
============================== 70 passed in 3.05s ==============================
```
- All existing tests still pass
- 14 new ML tests added
- Integration tests verify end-to-end workflow

## Files Changed/Added

### New Files (9)
1. `ml/__init__.py`
2. `ml/baseline_model.py`
3. `ml/predictor.py`
4. `ml/train_baseline.py`
5. `ml/README.md`
6. `labels.json`
7. `tests/test_ml.py`
8. `examples/ml_modes_comparison.py`

### Modified Files (4)
1. `attuario_ai/pipeline.py` - Added mode support
2. `scripts/run_pipeline.py` - Added CLI options
3. `README.md` - Added ML documentation
4. `.gitignore` - Exclude trained models

## Example Output

Running the comparison example shows all three modes:
```
SUMMARY
======================================================================
Heuristic Mode: 82.15 (Buono)
ML Mode:        92.50 (Eccellente)
Hybrid Mode:    87.33 (Eccellente)
```

## Benefits

1. **Flexibility**: Choose the right scoring method for your use case
2. **Extensibility**: Easy to add more ML models in the future
3. **Backward Compatibility**: Heuristic mode is still the default
4. **Hybrid Approach**: Best of both worlds with combined scoring
5. **Well-Tested**: Comprehensive test coverage
6. **Documented**: Clear documentation and examples

## Future Enhancements

Potential improvements mentioned in documentation:
- Deep learning models (BERT, transformers)
- Word embeddings (Word2Vec, GloVe)
- Ensemble methods
- Multi-task learning
- Active learning for efficient labeling
