import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import roc_curve, auc, confusion_matrix
import matplotlib.pyplot as plt

from ml.utils import load_model, save_metadata, print_evaluation_report, logger

class SelectorStabilityInference:

    # Initializes the inference engine with a trained model
    def __init__(self, model_path: str):
        self.model = load_model(model_path)
        self.model_path = model_path
        self.feature_names = None
        
        # Try to load metadata
        self._load_metadata()
    
    # Loads metadata associated with the model
    def _load_metadata(self) -> None:
        report_dir = os.path.dirname(self.model_path).replace('models', 'reports')
        
        # Find corresponding metadata file
        metadata_files = list(Path(report_dir).glob("model_metadata_*.json"))
        if metadata_files:
            metadata_path = sorted(metadata_files)[-1]  # Most recent
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                self.feature_names = metadata.get('features')
                logger.info(f"Loaded metadata from {metadata_path}")
    
    # Predicts stability for a batch of selectors
    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        if self.feature_names:
            # Reorder columns to match training data
            X = X[self.feature_names]
        
        dmatrix = xgb.DMatrix(X, feature_names=self.feature_names)
        proba = self.model.predict(dmatrix)
        labels = (proba > 0.5).astype(int)
        
        return labels, proba
    
    # Predicts stability for a single selector
    def predict_single(self, features: Dict[str, float]) -> Tuple[int, float]:
        X = pd.DataFrame([features])
        labels, proba = self.predict(X)
        return int(labels[0]), float(proba[0])
    
    # Predicts stability for a batch with confidence scores
    def predict_batch(self, X: pd.DataFrame, threshold: float = 0.5) -> pd.DataFrame:
        labels, proba = self.predict(X)
        
        results = pd.DataFrame({
            'prediction': labels,
            'probability': proba,
            'confidence': np.abs(proba - 0.5) * 2,  # Distance from decision boundary
            'is_stable': labels == 1
        })
        
        return results

class ModelEvaluator:

    # Initializes the model evaluator
    def __init__(self, model_path: str):
        self.inference = SelectorStabilityInference(model_path)
        self.model_path = model_path
    
    # Evaluates the model on test data
    def evaluate_on_test_data(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series
    ) -> Dict[str, Any]:
        labels, proba = self.inference.predict(X_test)
        
        metrics = print_evaluation_report(y_test, labels, "Test Set")
        
        # Additional metrics
        fpr, tpr, _ = roc_curve(y_test, proba)
        roc_auc = auc(fpr, tpr)
        metrics['roc_auc'] = roc_auc
        metrics['fpr'] = fpr
        metrics['tpr'] = tpr
        
        return metrics
    
    # Generates a comprehensive evaluation report with visualizations
    def generate_evaluation_report(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        output_dir: str = "ml/reports"
    ) -> str:
        os.makedirs(output_dir, exist_ok=True)
        
        # Get metrics
        metrics = self.evaluate_on_test_data(X_test, y_test)
        
        # Create visualization
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # ROC Curve
        axes[0, 0].plot(metrics['fpr'], metrics['tpr'], label=f"ROC (AUC = {metrics['roc_auc']:.3f})")
        axes[0, 0].plot([0, 1], [0, 1], 'k--', label='Random Classifier')
        axes[0, 0].set_xlabel('False Positive Rate')
        axes[0, 0].set_ylabel('True Positive Rate')
        axes[0, 0].set_title('ROC Curve')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Confusion Matrix Heatmap
        cm = np.array([[metrics['tn'], metrics['fp']], [metrics['fn'], metrics['tp']]])
        im = axes[0, 1].imshow(cm, cmap='Blues')
        axes[0, 1].set_xticks([0, 1])
        axes[0, 1].set_yticks([0, 1])
        axes[0, 1].set_xticklabels(['Negative', 'Positive'])
        axes[0, 1].set_yticklabels(['Negative', 'Positive'])
        axes[0, 1].set_ylabel('True Label')
        axes[0, 1].set_xlabel('Predicted Label')
        axes[0, 1].set_title('Confusion Matrix')
        for i in range(2):
            for j in range(2):
                axes[0, 1].text(j, i, str(cm[i, j]), ha='center', va='center', color='black' if cm[i, j] < cm.max()/2 else 'white')
        
        # Metrics Bar Chart
        metric_names = ['Accuracy', 'Precision', 'Recall', 'F1']
        metric_values = [metrics['accuracy'], metrics['precision'], metrics['recall'], metrics['f1']]
        axes[1, 0].bar(metric_names, metric_values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
        axes[1, 0].set_ylim([0, 1])
        axes[1, 0].set_ylabel('Score')
        axes[1, 0].set_title('Model Performance Metrics')
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        for i, v in enumerate(metric_values):
            axes[1, 0].text(i, v + 0.02, f'{v:.3f}', ha='center', va='bottom')
        
        # Metrics Summary Text
        axes[1, 1].axis('off')
        summary_text = f"""
        Model Evaluation Summary
        
        Accuracy:  {metrics['accuracy']:.4f}
        Precision: {metrics['precision']:.4f}
        Recall:    {metrics['recall']:.4f}
        F1-Score:  {metrics['f1']:.4f}
        ROC-AUC:   {metrics['roc_auc']:.4f}
        
        Confusion Matrix:
        TP: {metrics['tp']:4d} | FP: {metrics['fp']:4d}
        FN: {metrics['fn']:4d} | TN: {metrics['tn']:4d}
        
        Test Samples: {len(y_test)}
        """
        axes[1, 1].text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
                       verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        
        # Save figure
        timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(output_dir, f"evaluation_report_{timestamp}.png")
        plt.savefig(report_path, dpi=150, bbox_inches='tight')
        logger.info(f"Evaluation report saved to: {report_path}")
        
        # Save metrics as JSON
        metrics_json = {k: v for k, v in metrics.items() if k not in ['fpr', 'tpr']}
        metrics_path = os.path.join(output_dir, f"evaluation_metrics_{timestamp}.json")
        with open(metrics_path, 'w') as f:
            json.dump(metrics_json, f, indent=2, default=str)
        
        return report_path

# Runs inference on a dataset and saves the results
def predict_from_dataset(
    model_path: str,
    data_path: str,
    output_dir: str = "ml/reports"
) -> str:
    import json
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load data
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features_list = [item['features'] for item in data]
    X = pd.DataFrame(features_list)
    
    # Initialize inference engine first
    inference = SelectorStabilityInference(model_path)
    
    # Add missing features with default values if this is a raw dataset
    expected_features = set(inference.feature_names) if inference.feature_names else set()
    current_features = set(X.columns)
    missing_features = expected_features - current_features
    
    if missing_features:
        logger.info(f"Adding {len(missing_features)} missing features with default values: {sorted(missing_features)}")
        for feature in missing_features:
            if feature == 'is_probably_generated_class':
                # Check if selector looks like generated class (contains multiple underscores, numbers, etc.)
                X[feature] = X.apply(lambda row: 1 if '_' in str(row.get('selector', '')) and sum(c.isdigit() for c in str(row.get('selector', ''))) > 2 else 0, axis=1)
            elif feature == 'selector_token_count':
                # Count tokens in selector (split by common delimiters)
                X[feature] = X.apply(lambda row: len(str(row.get('selector', '')).replace('.', ' ').replace('#', ' ').replace('[', ' ').replace(']', ' ').split()), axis=1)
            elif feature == 'avg_token_length':
                # Average length of tokens
                X[feature] = X.apply(lambda row: sum(len(t) for t in str(row.get('selector', '')).replace('.', ' ').replace('#', ' ').replace('[', ' ').replace(']', ' ').split()) / max(1, len(str(row.get('selector', '')).replace('.', ' ').replace('#', ' ').replace('[', ' ').replace(']', ' ').split())), axis=1)
            elif feature == 'has_numeric_token':
                # Check if selector contains numeric tokens
                X[feature] = X.apply(lambda row: 1 if any(any(c.isdigit() for c in token) for token in str(row.get('selector', '')).replace('.', ' ').replace('#', ' ').replace('[', ' ').replace(']', ' ').split()) else 0, axis=1)
            elif feature == 'text_length':
                # Length of associated text content (default to 0 for raw datasets)
                X[feature] = 0
            elif feature == 'is_text_short':
                # Whether text is short (default to 1 for raw datasets without text)
                X[feature] = 1
            elif feature == 'is_xpath_absolute':
                # Check if XPath starts with /html or similar absolute path
                X[feature] = X.apply(lambda row: 1 if str(row.get('selector', '')).startswith('/') or str(row.get('selector', '')).startswith('xpath=') else 0, axis=1)
            else:
                # Default to 0 for any other missing features
                X[feature] = 0
    
    # Ensure all expected features are present
    if inference.feature_names:
        X = X[inference.feature_names]
    
    # Predict
    results_df = inference.predict_batch(X)
    
    # Add original data
    results_df['original_label'] = [item.get('label') for item in data]
    results_df['selector'] = [item.get('selector', 'N/A') for item in data]
    
    # Save results
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')
    results_path = os.path.join(output_dir, f"predictions_{timestamp}.csv")
    results_df.to_csv(results_path, index=False)
    
    logger.info(f"Predictions saved to: {results_path}")
    print(f"\nPrediction Summary:")
    print(f"Total predictions: {len(results_df)}")
    print(f"Stable selectors: {results_df['is_stable'].sum()}")
    print(f"Unstable selectors: {(~results_df['is_stable']).sum()}")
    
    return results_path
