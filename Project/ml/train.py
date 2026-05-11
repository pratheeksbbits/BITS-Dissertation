import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import xgboost as xgb
from sklearn.metrics import roc_curve
import matplotlib.pyplot as plt

from ml.config import TrainingConfig, XGBoostConfig
from ml.utils import (
    load_dataset, load_multiple_datasets, split_data, save_model, load_model,
    save_metadata, evaluate_model, print_evaluation_report, get_feature_importance,
    generate_timestamp, logger
)

class SelectorStabilityTrainer:

    # Initializes the XGBoost trainer with configuration
    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.model = None
        self.metadata = {}
        self.feature_names = None
        
    # Trains the model using a single dataset file
    def train_from_single_dataset(self, dataset_path: str) -> Dict[str, Any]:
        logger.info(f"\n{'='*60}")
        logger.info("Training from Single Dataset")
        logger.info(f"Dataset: {Path(dataset_path).name}")
        logger.info('='*60)
        
        # Load data
        X, y = load_dataset(dataset_path)
        return self._train_model(X, y, dataset_path)
    
    # Trains the model using all datasets in a directory
    def train_from_multiple_datasets(self, data_dir: str) -> Dict[str, Any]:
        logger.info(f"\n{'='*60}")
        logger.info("Training from Multiple Datasets")
        logger.info(f"Data Directory: {data_dir}")
        logger.info('='*60)
        
        # Load all datasets
        X, y = load_multiple_datasets(data_dir)
        return self._train_model(X, y, data_dir)
    
    # Internal method that handles the core training logic
    def _train_model(self, X: pd.DataFrame, y: pd.Series, data_source: str) -> Dict[str, Any]:
        # Check data quality
        logger.info(f"\nDataset Shape: {X.shape}")
        logger.info(f"Features: {list(X.columns)}")
        logger.info(f"Label Distribution:\n{y.value_counts()}")
        
        # Check for missing values
        missing = X.isnull().sum()
        if missing.any():
            logger.warning(f"Missing values found:\n{missing[missing > 0]}")
            X = X.fillna(0)
            logger.info("Filled missing values with 0")
        
        # Store feature names
        self.feature_names = X.columns.tolist()
        
        # Split data
        X_train, X_test, y_train, y_test = split_data(
            X, y,
            test_size=self.config.test_size,
            random_state=self.config.random_state
        )
        
        # Convert to DMatrix for XGBoost
        dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=self.feature_names)
        dtest = xgb.DMatrix(X_test, label=y_test, feature_names=self.feature_names)
        
        # Train model
        logger.info(f"\nTraining XGBoost Model...")
        logger.info(f"Parameters: {self.config.xgboost_config.to_dict()}")
        
        evals = [(dtrain, 'train'), (dtest, 'test')]
        evals_result = {}
        
        self.model = xgb.train(
            params=self.config.xgboost_config.to_dict(),
            dtrain=dtrain,
            num_boost_round=self.config.xgboost_config.n_estimators,
            evals=evals,
            evals_result=evals_result,
            early_stopping_rounds=self.config.xgboost_config.early_stopping_rounds,
            verbose_eval=10
        )
        
        logger.info(f"Training completed. Best iteration: {self.model.best_iteration}")
        
        # Make predictions
        y_pred_train = self.model.predict(dtrain)
        y_pred_test = self.model.predict(dtest)
        y_pred_train_labels = (y_pred_train > 0.5).astype(int)
        y_pred_test_labels = (y_pred_test > 0.5).astype(int)
        
        # Evaluate
        train_metrics = print_evaluation_report(y_train, y_pred_train_labels, "Training")
        test_metrics = print_evaluation_report(y_test, y_pred_test_labels, "Test")
        
        # Feature importance
        get_feature_importance(self.model, top_n=15)
        
        # Save model
        timestamp = generate_timestamp()
        model_path = os.path.join(
            self.config.model_dir,
            f"selector_stability_model_{timestamp}.joblib"
        )
        save_model(self.model, model_path)
        
        # Save metadata
        metadata = {
            'timestamp': timestamp,
            'model_type': 'XGBoost',
            'data_source': str(data_source),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'features': self.feature_names,
            'feature_count': len(self.feature_names),
            'training_metrics': train_metrics,
            'test_metrics': test_metrics,
            'best_iteration': self.model.best_iteration,
            'config': self.config.xgboost_config.to_dict()
        }
        
        self.metadata = metadata
        
        metadata_path = os.path.join(
            self.config.report_dir,
            f"model_metadata_{timestamp}.json"
        )
        save_metadata(metadata, metadata_path)
        
        logger.info(f"\nModel saved to: {model_path}")
        logger.info(f"Metadata saved to: {metadata_path}")
        
        return {
            'model_path': model_path,
            'metadata': metadata,
            'evals_result': evals_result
        }
    
    # Makes predictions on new data using the trained model
    def predict(self, X: pd.DataFrame) -> tuple:
        if self.model is None:
            raise ValueError("Model not trained. Call train_from_dataset first.")
        
        dmatrix = xgb.DMatrix(X, feature_names=self.feature_names)
        proba = self.model.predict(dmatrix)
        labels = (proba > 0.5).astype(int)
        
        return labels, proba

# CLI entry point for training the model
def train_model_cli(
    dataset_path: Optional[str] = None,
    data_dir: Optional[str] = None,
    model_config: Optional[XGBoostConfig] = None
) -> str:
    # Create config
    training_config = TrainingConfig(xgboost_config=model_config or XGBoostConfig())
    trainer = SelectorStabilityTrainer(training_config)
    
    # Train
    if dataset_path:
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Dataset not found: {dataset_path}")
        result = trainer.train_from_single_dataset(dataset_path)
    elif data_dir:
        if not os.path.exists(data_dir):
            raise FileNotFoundError(f"Data directory not found: {data_dir}")
        result = trainer.train_from_multiple_datasets(data_dir)
    else:
        dataset_path = training_config.data_dir  # Use default
        if os.path.exists(dataset_path):
            result = trainer.train_from_multiple_datasets(dataset_path)
        else:
            raise ValueError("No dataset found. Specify dataset_path or data_dir.")
    
    return result['model_path']

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train XGBoost selector stability model")
    parser.add_argument(
        "--dataset",
        type=str,
        help="Path to single dataset file"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/final",
        help="Directory with multiple datasets (default: data/final)"
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=6,
        help="XGBoost max_depth parameter"
    )
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=0.1,
        help="XGBoost learning_rate parameter"
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=100,
        help="Number of boosting rounds"
    )
    
    args = parser.parse_args()
    
    # Create custom config if parameters provided
    config = XGBoostConfig(
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        n_estimators=args.n_estimators
    )
    
    try:
        model_path = train_model_cli(
            dataset_path=args.dataset,
            data_dir=args.data_dir,
            model_config=config
        )
        logger.info(f"\nSUCCESS: Model trained and saved to: {model_path}")
    except Exception as e:
        logger.error(f"ERROR: {e}")
        sys.exit(1)
