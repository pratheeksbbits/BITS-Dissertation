"""
ML Utilities
Helper functions for model training, evaluation, and inference.
"""

import json
import os
from pathlib import Path
from typing import Tuple, Dict, List, Any
from datetime import datetime
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report, roc_curve
)
import joblib
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_dataset(filepath: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load training dataset from JSON file.
    
    Args:
        filepath: Path to cleaned dataset JSON
        
    Returns:
        Tuple of (features_df, labels_series)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data)} samples from {filepath}")
        
        # Convert to DataFrame
        features_list = [item['features'] for item in data]
        labels = [item['label'] for item in data]
        
        features_df = pd.DataFrame(features_list)
        labels_series = pd.Series(labels)
        
        return features_df, labels_series
    except Exception as e:
        logger.error(f"Error loading dataset: {e}")
        raise

def load_multiple_datasets(data_dir: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load and combine multiple datasets from directory.
    
    Args:
        data_dir: Directory containing cleaned training datasets
        
    Returns:
        Tuple of combined (features_df, labels_series)
    """
    all_features = []
    all_labels = []
    
    # Find all cleaned dataset files
    json_files = sorted(Path(data_dir).glob("cleaned_training_dataset_*.json"))
    
    if not json_files:
        raise ValueError(f"No datasets found in {data_dir}")
    
    for filepath in json_files:
        logger.info(f"Loading {filepath.name}...")
        features, labels = load_dataset(str(filepath))
        all_features.append(features)
        all_labels.extend(labels)
    
    # Combine datasets
    combined_features = pd.concat(all_features, ignore_index=True)
    combined_labels = pd.Series(all_labels)
    
    logger.info(f"Combined {len(json_files)} datasets: {len(combined_features)} total samples")
    
    return combined_features, combined_labels

def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split data into train and test sets.
    
    Args:
        X: Features
        y: Labels
        test_size: Proportion for test set
        random_state: Random seed
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y  # Maintain class balance
    )
    
    logger.info(f"Train set: {len(X_train)} samples")
    logger.info(f"Test set: {len(X_test)} samples")
    logger.info(f"Class distribution - Train: {y_train.value_counts().to_dict()}")
    logger.info(f"Class distribution - Test: {y_test.value_counts().to_dict()}")
    
    return X_train, X_test, y_train, y_test

def save_model(model: Any, filepath: str) -> None:
    """
    Save trained model to disk.
    
    Args:
        model: Trained model object
        filepath: Path to save model
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    joblib.dump(model, filepath)
    file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
    logger.info(f"Model saved to {filepath} ({file_size_mb:.2f} MB)")

def load_model(filepath: str) -> Any:
    """
    Load trained model from disk.
    
    Args:
        filepath: Path to model file
        
    Returns:
        Loaded model
    """
    model = joblib.load(filepath)
    logger.info(f"Model loaded from {filepath}")
    return model

def save_metadata(
    metadata: Dict[str, Any],
    filepath: str
) -> None:
    """
    Save model metadata and training info.
    
    Args:
        metadata: Dictionary with training info
        filepath: Path to save metadata
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, default=str)
    logger.info(f"Metadata saved to {filepath}")

def evaluate_model(
    y_true: pd.Series,
    y_pred: np.ndarray,
    y_pred_proba: np.ndarray = None
) -> Dict[str, float]:
    """
    Evaluate model performance.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        y_pred_proba: Prediction probabilities
        
    Returns:
        Dictionary with evaluation metrics
    """
    metrics = {
        'accuracy': accuracy_score(y_true, y_pred),
        'precision': precision_score(y_true, y_pred),
        'recall': recall_score(y_true, y_pred),
        'f1': f1_score(y_true, y_pred),
    }
    
    if y_pred_proba is not None:
        metrics['roc_auc'] = roc_auc_score(y_true, y_pred_proba)
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred)
    metrics['tn'] = int(cm[0, 0])
    metrics['fp'] = int(cm[0, 1])
    metrics['fn'] = int(cm[1, 0])
    metrics['tp'] = int(cm[1, 1])
    
    return metrics

def print_evaluation_report(
    y_true: pd.Series,
    y_pred: np.ndarray,
    set_name: str = "Test"
) -> None:
    """
    Print detailed evaluation report.
    
    Args:
        y_true: True labels
        y_pred: Predicted labels
        set_name: Name of the evaluation set
    """
    metrics = evaluate_model(y_true, y_pred)
    
    print(f"\n{'='*60}")
    print(f"{set_name} Set Evaluation")
    print('='*60)
    print(f"Accuracy:  {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    print(f"F1-Score:  {metrics['f1']:.4f}")
    if 'roc_auc' in metrics:
        print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
    print(f"\nConfusion Matrix:")
    print(f"  True Negatives:  {metrics['tn']}")
    print(f"  False Positives: {metrics['fp']}")
    print(f"  False Negatives: {metrics['fn']}")
    print(f"  True Positives:  {metrics['tp']}")
    print('='*60)
    
    return metrics

def get_feature_importance(model: Any, top_n: int = 15) -> pd.DataFrame:
    """
    Get feature importance from trained model.
    
    Args:
        model: Trained XGBoost model
        top_n: Number of top features to return
        
    Returns:
        DataFrame with feature importance
    """
    # Handle xgb.Booster model (uses get_score)
    if hasattr(model, 'get_score'):
        importance_dict = model.get_score(importance_type='weight')
        if importance_dict:
            importance_df = pd.DataFrame(list(importance_dict.items()), columns=['feature', 'importance'])
            importance_df = importance_df.sort_values('importance', ascending=False)
        else:
            print("\nNo feature importance data available")
            return pd.DataFrame()
    # Handle sklearn model types (have feature_importances_)
    elif hasattr(model, 'feature_importances_'):
        feature_names = model.feature_names_in_ if hasattr(model, 'feature_names_in_') else [f'f{i}' for i in range(len(model.feature_importances_))]
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': model.feature_importances_
        }).sort_values('importance', ascending=False)
    else:
        print("\nModel type not supported for feature importance extraction")
        return pd.DataFrame()
    
    print(f"\nTop {top_n} Important Features:")
    print(importance_df.head(top_n).to_string(index=False))
    
    return importance_df.head(top_n)

def generate_timestamp() -> str:
    """Generate timestamp for filenames."""
    return datetime.now().strftime('%Y%m%d_%H%M%S')
