#!/usr/bin/env python3
"""
ML Training CLI
Command-line interface for model training, evaluation, and inference.
"""

import sys
import os
import argparse
import logging
from pathlib import Path
import pandas as pd
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from ml.config import XGBoostConfig, TrainingConfig
from ml.train import SelectorStabilityTrainer, train_model_cli
from ml.evaluate import ModelEvaluator, SelectorStabilityInference, predict_from_dataset
from ml.utils import load_multiple_datasets, load_dataset, logger

def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def cmd_train(args):
    """Handle training command."""
    setup_logging(args.verbose)
    
    # Create config
    xgb_config = XGBoostConfig(
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
        subsample=args.subsample,
        colsample_bytree=args.colsample_bytree,
        reg_lambda=args.reg_lambda,
    )
    
    training_config = TrainingConfig(
        xgboost_config=xgb_config,
        test_size=args.test_size,
        data_dir=args.data_dir,
        model_dir=args.model_dir,
        report_dir=args.report_dir,
    )
    
    trainer = SelectorStabilityTrainer(training_config)
    
    # Train
    if args.dataset:
        if not os.path.exists(args.dataset):
            logger.error(f"Dataset not found: {args.dataset}")
            return 1
        result = trainer.train_from_single_dataset(args.dataset)
        logger.info(f"\nTrained on single dataset: {args.dataset}")
    else:
        if not os.path.exists(args.data_dir):
            logger.error(f"Data directory not found: {args.data_dir}")
            return 1
        result = trainer.train_from_multiple_datasets(args.data_dir)
        logger.info(f"\nTrained on all datasets in: {args.data_dir}")
    
    logger.info(f"Model saved to: {result['model_path']}")
    return 0

def cmd_evaluate(args):
    """Handle evaluation command."""
    setup_logging(args.verbose)
    
    if not os.path.exists(args.model):
        logger.error(f"Model not found: {args.model}")
        return 1
    
    if not os.path.exists(args.test_data):
        logger.error(f"Test data not found: {args.test_data}")
        return 1
    
    # Load test data
    X_test, y_test = load_dataset(args.test_data)
    
    # Evaluate
    evaluator = ModelEvaluator(args.model)
    evaluator.generate_evaluation_report(
        X_test,
        y_test,
        output_dir=args.report_dir
    )
    
    logger.info(f"Evaluation report saved to: {args.report_dir}")
    return 0

def cmd_predict(args):
    """Handle prediction command."""
    setup_logging(args.verbose)
    
    if not os.path.exists(args.model):
        logger.error(f"Model not found: {args.model}")
        return 1
    
    if not os.path.exists(args.data):
        logger.error(f"Data not found: {args.data}")
        return 1
    
    # Run predictions
    results_path = predict_from_dataset(
        args.model,
        args.data,
        output_dir=args.output_dir
    )
    
    logger.info(f"Predictions saved to: {results_path}")
    return 0

def cmd_benchmark(args):
    """Handle benchmark/hyperparameter tuning command."""
    setup_logging(args.verbose)
    
    logger.info("Starting hyperparameter benchmarking...")
    
    if not os.path.exists(args.data_dir):
        logger.error(f"Data directory not found: {args.data_dir}")
        return 1
    
    # Load data
    X, y = load_multiple_datasets(args.data_dir)
    
    # Try different configurations
    configs = [
        {'max_depth': 4, 'learning_rate': 0.05},
        {'max_depth': 6, 'learning_rate': 0.1},
        {'max_depth': 8, 'learning_rate': 0.1},
        {'max_depth': 6, 'learning_rate': 0.15},
    ]
    
    results = []
    
    for config in configs:
        logger.info(f"\nTesting config: {config}")
        
        xgb_config = XGBoostConfig(**config)
        training_config = TrainingConfig(
            xgboost_config=xgb_config,
            test_size=args.test_size,
            data_dir=args.data_dir,
        )
        
        trainer = SelectorStabilityTrainer(training_config)
        result = trainer._train_model(X, y, args.data_dir)
        
        results.append({
            'config': config,
            'test_metrics': result['metadata']['test_metrics'],
            'model_path': result['model_path'],
        })
    
    # Save results
    results_path = os.path.join(args.output_dir, 'benchmark_results.json')
    os.makedirs(args.output_dir, exist_ok=True)
    
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\nBenchmark results saved to: {results_path}")
    
    # Print summary
    logger.info("\nBenchmark Summary:")
    logger.info("─" * 80)
    for i, result in enumerate(results, 1):
        f1 = result['test_metrics']['f1']
        acc = result['test_metrics']['accuracy']
        logger.info(f"{i}. {result['config']} → F1: {f1:.4f}, Accuracy: {acc:.4f}")
    
    return 0

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ML Training Pipeline for Selector Stability Prediction",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Train on all datasets:
    python train_cli.py train

  Train on single dataset:
    python train_cli.py train --dataset data/final/cleaned_training_dataset_example_com_20260424_000000.json

  Evaluate model:
    python train_cli.py evaluate --model ml/models/selector_stability_model_20260424_000000.joblib --test-data data/final/cleaned_training_dataset_*.json

  Make predictions:
    python train_cli.py predict --model ml/models/selector_stability_model_*.joblib --data data/final/cleaned_training_dataset_*.json

  Run hyperparameter benchmark:
    python train_cli.py benchmark --data-dir data/final
        """
    )
    
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    
    # Shared arguments
    parser.add_argument('--data-dir', default='data/final', help='Data directory')
    parser.add_argument('--model-dir', default='ml/models', help='Model directory')
    parser.add_argument('--report-dir', default='ml/reports', help='Report directory')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train a new model')
    train_parser.add_argument('--dataset', help='Path to single dataset file (optional)')
    train_parser.add_argument('--test-size', type=float, default=0.2, help='Test set size')
    train_parser.add_argument('--n-estimators', type=int, default=100, help='Number of boosting rounds')
    train_parser.add_argument('--max-depth', type=int, default=6, help='Maximum tree depth')
    train_parser.add_argument('--learning-rate', type=float, default=0.1, help='Learning rate')
    train_parser.add_argument('--subsample', type=float, default=0.8, help='Subsample ratio')
    train_parser.add_argument('--colsample-bytree', type=float, default=0.8, help='Colsample ratio')
    train_parser.add_argument('--reg-lambda', type=float, default=1.0, help='L2 regularization')
    train_parser.set_defaults(func=cmd_train)
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate a trained model')
    eval_parser.add_argument('--model', required=True, help='Path to trained model')
    eval_parser.add_argument('--test-data', required=True, help='Path to test dataset')
    eval_parser.set_defaults(func=cmd_evaluate)
    
    # Predict command
    pred_parser = subparsers.add_parser('predict', help='Make predictions on new data')
    pred_parser.add_argument('--model', required=True, help='Path to trained model')
    pred_parser.add_argument('--data', required=True, help='Path to data file')
    pred_parser.add_argument('--output-dir', default='ml/reports', help='Output directory')
    pred_parser.set_defaults(func=cmd_predict)
    
    # Benchmark command
    bench_parser = subparsers.add_parser('benchmark', help='Run hyperparameter benchmarking')
    bench_parser.add_argument('--test-size', type=float, default=0.2, help='Test set size')
    bench_parser.add_argument('--output-dir', default='ml/reports', help='Output directory')
    bench_parser.set_defaults(func=cmd_benchmark)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
