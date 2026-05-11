from dataclasses import dataclass
from typing import Dict, Any
import os

@dataclass
class XGBoostConfig:

    n_estimators: int = 100
    max_depth: int = 6
    learning_rate: float = 0.1
    subsample: float = 0.8
    colsample_bytree: float = 0.8
    reg_lambda: float = 1.0
    reg_alpha: float = 0.0
    min_child_weight: int = 1
    random_state: int = 42
    early_stopping_rounds: int = 20
    eval_metric: str = "logloss"
    scale_pos_weight: float = 1.0

    # Converts the config to a dictionary for XGBoost
    def to_dict(self) -> Dict[str, Any]:
        return {
            'n_estimators': self.n_estimators,
            'max_depth': self.max_depth,
            'learning_rate': self.learning_rate,
            'subsample': self.subsample,
            'colsample_bytree': self.colsample_bytree,
            'reg_lambda': self.reg_lambda,
            'reg_alpha': self.reg_alpha,
            'min_child_weight': self.min_child_weight,
            'random_state': self.random_state,
            'scale_pos_weight': self.scale_pos_weight,
            'eval_metric': self.eval_metric,
            'verbosity': 1,
            'objective': 'binary:logistic'
        }

@dataclass
class TrainingConfig:
    """Training pipeline configuration."""
    
    # Data paths
    data_dir: str = "data/final"
    model_dir: str = "ml/models"
    report_dir: str = "ml/reports"
    
    # Train/test split
    test_size: float = 0.2  # 80/20 split for small datasets
    val_size: float = 0.1  # 10% validation from training data
    random_state: int = 42
    
    # Training parameters
    xgboost_config: XGBoostConfig = None
    batch_training: bool = False  # When True, train on all datasets combined
    
    def __post_init__(self):
        if self.xgboost_config is None:
            self.xgboost_config = XGBoostConfig()
        
        # Create directories if they don't exist
        os.makedirs(self.model_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)

# Default configurations
DEFAULT_TRAINING_CONFIG = TrainingConfig()
DEFAULT_XGBOOST_CONFIG = XGBoostConfig()
