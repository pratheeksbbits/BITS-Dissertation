# ML Training Framework Documentation

## Overview

This document explains the XGBoost-based ML component for predicting DOM selector stability in Playwright automation.

## Project Structure

```
ml/
├── __init__.py           # Module initialization
├── config.py             # Configuration and hyperparameters
├── train.py              # Training pipeline
├── evaluate.py           # Evaluation and inference
├── utils.py              # Utility functions
├── models/               # Trained model files (joblib format)
└── reports/              # Evaluation reports and metrics

train_cli.py            # Command-line interface
```

## Why XGBoost?

### The Problem
**Binary Classification Task**: Predict if a DOM selector will be stable/reliable for Playwright automation.

### Why XGBoost Excels

| Aspect | XGBoost Advantage |
|--------|-------------------|
| **Feature Interactions** | Captures complex relationships between selector properties (e.g., uniqueness + static class names) |
| **Non-linear Patterns** | Selector stability isn't linear—XGBoost's tree ensembles learn complex rules |
| **Small Datasets** | With 100-300 training samples, XGBoost's regularization prevents overfitting |
| **Interpretability** | Tree-based predictions are explainable vs black-box neural networks |
| **Production Ready** | Fast inference, lightweight model files, easy deployment |
| **Feature Importance** | Shows which selector properties matter most (e.g., uniqueness is 3x more important than length) |
| **Balanced Data** | Naturally handles 50/50 positive/negative samples well |

### vs Alternatives

- **Logistic Regression**: Too simple, misses feature interactions
- **Random Forest**: Good but slower, larger models, less regularization control
- **Neural Networks**: Overkill for small datasets, hard to debug, slow inference
- **SVM**: Poor with many selector features, harder to interpret

## Model Architecture

### Input Features (20+)
```
match_count              - How many elements match this selector
is_unique               - Binary: selector matches only 1 element
selector_length         - Length of selector string
is_text                 - Binary: selector uses text content
has_dynamic_pattern     - Binary: selector contains dynamic/generated patterns
selector_token_count    - Number of tokens in selector
...and 14 more
```

### Output
```
0 = Unstable selector (will break with DOM changes)
1 = Stable selector (robust for automation)
```

### Model Configuration (ml/config.py)

```python
n_estimators = 100          # Trees to grow
max_depth = 6               # Depth limit (prevents overfitting)
learning_rate = 0.1         # Shrinkage (higher = faster, lower = better generalization)
subsample = 0.8             # Fraction of training samples per round
colsample_bytree = 0.8      # Fraction of features per tree
reg_lambda = 1.0            # L2 regularization (prevents complex trees)
reg_alpha = 0.0             # L1 regularization (feature selection)
```

## Training Your Model

### Quick Start (Recommended)

Train on all datasets in `data/final/`:

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run training
python train_cli.py train

# Output: Model saved to ml/models/selector_stability_model_YYYYMMDD_HHMMSS.joblib
```

### Training on Single Dataset

```bash
python train_cli.py train --dataset data/final/cleaned_training_dataset_example_com_20260424_000000.json
```

### Custom Hyperparameters

```bash
# Train with custom parameters
python train_cli.py train \
  --n-estimators 150 \
  --max-depth 8 \
  --learning-rate 0.05 \
  --reg-lambda 2.0
```

### Parameter Guide

```
--n-estimators      Number of boosting rounds (default: 100)
                   Higher = better fit but slower training
                   Try: 50, 100, 200

--max-depth         Maximum tree depth (default: 6)
                   Lower = simpler model, less overfitting
                   Try: 4, 5, 6, 7, 8

--learning-rate     Shrinkage parameter (default: 0.1)
                   Lower = slower but better generalization
                   Try: 0.01, 0.05, 0.1, 0.2

--subsample         Fraction of samples per round (default: 0.8)
                   Lower = more regularization
                   Try: 0.6, 0.8, 1.0

--reg-lambda        L2 regularization (default: 1.0)
                   Higher = simpler trees
                   Try: 0.1, 1.0, 5.0, 10.0

--test-size         Test set proportion (default: 0.2)
                   For small datasets, use 0.2-0.25
```

## Evaluating Your Model

### Generate Evaluation Report

```bash
python train_cli.py evaluate \
  --model ml/models/selector_stability_model_YYYYMMDD_HHMMSS.joblib \
  --test-data data/final/cleaned_training_dataset_example_com_*.json
```

**Output includes:**
- Accuracy, Precision, Recall, F1-Score
- ROC-AUC score
- Confusion matrix visualization
- Feature importance ranking

### Key Metrics Explained

```
Accuracy   = (TP + TN) / Total              # Overall correctness
Precision  = TP / (TP + FP)                 # When we predict "stable", how often correct?
Recall     = TP / (TP + FN)                 # Did we catch all stable selectors?
F1-Score   = 2 * (Precision * Recall) / ... # Balanced metric
ROC-AUC    = Area under ROC curve           # Probability ranking

Good Model
- Accuracy ≥ 0.85
- Precision ≥ 0.80
- Recall ≥ 0.80
- F1-Score ≥ 0.80
- ROC-AUC ≥ 0.85
```

## Making Predictions

### Single Selector Prediction

```python
from ml.evaluate import SelectorStabilityInference

# Load model
inference = SelectorStabilityInference('ml/models/selector_stability_model_*.joblib')

# Predict for single selector
features = {
    'match_count': 1,
    'is_unique': 1,
    'selector_length': 25,
    'is_text': 0,
    'has_dynamic_pattern': 0,
    # ... other features
}

label, probability = inference.predict_single(features)
# label = 1 (stable), probability = 0.87 (87% confidence)
```

### Batch Predictions

```bash
python train_cli.py predict \
  --model ml/models/selector_stability_model_*.joblib \
  --data data/final/cleaned_training_dataset_*.json \
  --output-dir ml/reports
```

**Output CSV with:**
```
prediction   = 0 or 1 (unstable/stable)
probability  = Confidence score (0.0-1.0)
confidence   = Distance from decision boundary
is_stable    = True/False
selector     = Original selector string
```

## Hyperparameter Tuning

### Automated Benchmark

Test multiple configurations automatically:

```bash
python train_cli.py benchmark --data-dir data/final --output-dir ml/reports
```

Tests:
- max_depth: 4, 6, 8
- learning_rate: 0.05, 0.1, 0.15
- Saves comparison results in `ml/reports/benchmark_results.json`

### Manual Tuning Strategy

1. **Start with defaults** (already optimized for small datasets)
2. **If overfitting** (train F1 > test F1 by 0.1+):
   - Decrease max_depth (6→5)
   - Increase reg_lambda (1.0→2.0)
3. **If underfitting** (low test F1 < 0.75):
   - Increase max_depth (6→7)
   - Increase n_estimators (100→200)
4. **Re-evaluate** on test set

## Output Files

After training, you'll find:

```
ml/models/
  selector_stability_model_20260424_153000.joblib  # Trained model (100 KB)

ml/reports/
  model_metadata_20260424_153000.json              # Training info
  evaluation_metrics_20260424_153001.json          # Test metrics
  evaluation_report_20260424_153001.png            # Visualizations
  predictions_20260424_153002.csv                  # Inference results
  benchmark_results.json                           # Hyperparameter comparison
```

## Model File Format

**Format**: JobLib (Python's pickle-based model serialization)
**Size**: ~100-200 KB (very lightweight)
**Python**: 3.8+ compatible

```python
import joblib

# Load model anywhere
model = joblib.load('ml/models/selector_stability_model_*.joblib')
predictions = model.predict(xgboost.DMatrix(data))
```

## Important Notes

### Data Requirements
- Minimum 50 samples (20 train, 30 test)
- Balanced classes (50% positive, 50% negative) ideal
- All features must be numeric
- No missing values (auto-filled with 0)

### Training Time
- 100 samples: ~1-2 seconds
- 300 samples: ~3-5 seconds
- Includes evaluation

### Model Generalization
- Models trained on `example.com` work reasonably on `google.com`
- Performance may vary by website complexity
- For best results, train on diverse websites

### When to Retrain
- After collecting 100+ new samples
- When accuracy drops below 0.80
- When adding new selector types
- Quarterly for production models

## Troubleshooting

### Low Test Accuracy

```bash
# 1. Check data quality
python -c "from ml.utils import load_multiple_datasets; X, y = load_multiple_datasets('data/final'); print(X.shape, y.value_counts())"

# 2. Try simpler model
python train_cli.py train --max-depth 4 --learning-rate 0.05

# 3. More training data needed
# Collect more samples from diverse websites
```

### Model Won't Load

```python
# Ensure path is correct and file exists
import os
model_path = 'ml/models/selector_stability_model_20260424_000000.joblib'
assert os.path.exists(model_path), f"Model not found: {model_path}"

# Check model format
import joblib
try:
    model = joblib.load(model_path)
    print(f"Model loaded successfully: {type(model)}")
except Exception as e:
    print(f"Error loading model: {e}")
```

## Integration with Scraper

After training, use the model to score new selectors:

```python
from ml.evaluate import SelectorStabilityInference

# In your Playwright automation code
inference = SelectorStabilityInference('ml/models/selector_stability_model_latest.joblib')

# For each selector candidate
label, probability = inference.predict_single(features)

if probability > 0.85:  # High confidence
    use_selector()  # It's stable
else:
    find_alternative()  # Try backup selector
```

## Performance Benchmarks

On typical datasets:

```
Model Training:    2-5 seconds for 300 samples
Single Prediction: 1-2 milliseconds
Batch (100):       50-100 milliseconds
Model Size:        100-200 KB
RAM Usage:         ~50 MB when loaded
```

## References

- [XGBoost Documentation](https://xgboost.readthedocs.io/)
- [Binary Classification Metrics](https://scikit-learn.org/stable/modules/model_evaluation.html)
- [Feature Importance](https://xgboost.readthedocs.io/en/latest/python/python_intro.html#feature-importance)
