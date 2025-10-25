#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import optuna
import torch
import yaml
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data.dataset import SequenceConfig, TimeSeriesDataset
from data.mt5_connector import MT5Credentials, MT5DataConnector
from features.feature_engineering import FeatureConfig, MultiTimeframeFeatures
from labeling.cost_adjusted_labels import CostAdjustedLabeler
from labeling.triple_barrier import TripleBarrierLabeler
from models.model_factory import ModelConfig, create_model
from training.trainer import Trainer


def load_config(config_path: str | Path = "config.yaml") -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def compute_class_weights(dataset: TimeSeriesDataset) -> list[float]:
    counts = np.bincount(dataset.y.numpy(), minlength=3)
    counts = np.where(counts == 0, 1, counts)
    total = counts.sum()
    weights = (total / (len(counts) * counts)).tolist()
    return weights


def objective(trial, base_df, feature_cols, base_config, trials_dir: Path):
    k1_tp = trial.suggest_float("k1_tp", 1.0, 3.0)
    k2_sl = trial.suggest_float("k2_sl", 0.5, 2.0)
    holding_period = trial.suggest_int("holding_period", 12, 48)
    lookback = trial.suggest_categorical("lookback", [64, 128, 256])
    lr = trial.suggest_loguniform("lr", 1e-4, 1e-2)
    dropout = trial.suggest_float("dropout", 0.1, 0.5)

    print(
        f"Trial {trial.number}: k1_tp={k1_tp:.2f}, k2_sl={k2_sl:.2f}, holding_period={holding_period}, lookback={lookback}, lr={lr:.5f}, dropout={dropout:.2f}"
    )

    labeler = TripleBarrierLabeler(
        k1_tp=k1_tp,
        k2_sl=k2_sl,
        holding_period=holding_period,
        spread_points=base_config["labeling"]["spread_points"],
        point_value=base_config["labeling"]["point_value"],
    )

    df_labeled = labeler.label_dataset(base_df.copy())
    cost_labeler = CostAdjustedLabeler(min_profit_threshold=0.0)
    df_labeled = cost_labeler.filter_unprofitable(df_labeled)
    df_labeled = df_labeled.dropna()

    if len(df_labeled) < lookback * 2:
        print("Insufficient samples after labeling; skipping trial.")
        return 0.0

    seq_config = SequenceConfig(lookback=lookback)
    split_idx = int(0.8 * len(df_labeled))
    train_df = df_labeled.iloc[:split_idx].copy()
    val_df = df_labeled.iloc[split_idx:].copy()

    scaler = StandardScaler()
    train_df[feature_cols] = scaler.fit_transform(train_df[feature_cols])
    val_df[feature_cols] = scaler.transform(val_df[feature_cols])

    train_dataset = TimeSeriesDataset(train_df, feature_cols, "label", seq_config)
    val_dataset = TimeSeriesDataset(val_df, feature_cols, "label", seq_config)

    if len(train_dataset) == 0 or len(val_dataset) == 0:
        print("No sequences generated for trial; skipping.")
        return 0.0

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False, num_workers=0)

    num_features = len(feature_cols)
    model_channels = trial.suggest_categorical("num_channels", [(64, 128, 256), (64, 128, 128), (32, 64, 128)])
    model_config = ModelConfig(
        type="tcn",
        num_channels=model_channels,
        kernel_size=3,
        dropout=dropout,
    )
    model = create_model(num_features, model_config)

    device = "cuda" if torch.cuda.is_available() else "cpu"

    trial_dir = trials_dir / f"trial_{trial.number}"
    trial_dir.mkdir(exist_ok=True)

    class_weights = compute_class_weights(train_dataset)

    trainer = Trainer(
        model,
        train_loader,
        val_loader,
        device=device,
        lr=lr,
        class_weights=class_weights,
        grad_clip=1.0,
        output_dir=trial_dir,
    )

    trainer.train(num_epochs=30, early_stop_patience=5)

    val_metrics = trainer.validate()
    val_acc = val_metrics.get("accuracy", 0.0)

    print(f"Trial {trial.number} accuracy: {val_acc:.4f}")

    return val_acc


def main():
    config_path = project_root / "config.yaml"
    config = load_config(config_path)

    print("=" * 60)
    print("Fetching and preparing base data for optimization...")
    print("=" * 60)

    connector = MT5DataConnector(config["data"]["symbol"])
    mt5_cfg = config["data"].get("mt5", {})
    credentials = None
    if mt5_cfg.get("login"):
        credentials = MT5Credentials(login=mt5_cfg["login"], password=mt5_cfg["password"], server=mt5_cfg["server"])

    start_date = datetime.strptime(config["data"]["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(config["data"]["end_date"], "%Y-%m-%d")

    try:
        connector.connect(credentials)

        m15_data = connector.fetch_data("M15", start_date, end_date)
        h1_data = connector.fetch_data("H1", start_date, end_date)
        h4_data = connector.fetch_data("H4", start_date, end_date)

        feature_cfg = FeatureConfig(
            ema_periods=config["features"]["ema_periods"],
            atr_window=config["features"]["atr_window"],
            rsi_window=config["features"]["rsi_window"],
            ema_slope_window=config["features"]["ema_slope_window"],
        )
        feature_eng = MultiTimeframeFeatures(feature_cfg)

        m15_features = feature_eng.calculate_indicators(m15_data, "m15")
        h1_features = feature_eng.calculate_indicators(h1_data, "h1")
        h4_features = feature_eng.calculate_indicators(h4_data, "h4")

        aligned_df = feature_eng.align_to_m15(m15_features, h1_features, h4_features)
        base_df = feature_eng.detect_regime(aligned_df)

    finally:
        connector.shutdown()

    feature_cols = [col for col in base_df.columns if col not in {"label", "expected_profit", "regime"}]

    print(f"Base dataset shape: {base_df.shape}")
    print(f"Using {len(feature_cols)} features")

    trials_dir = project_root / "optuna_trials"
    trials_dir.mkdir(exist_ok=True)

    print("\n" + "=" * 60)
    print("Starting hyperparameter optimization with Optuna...")
    print("=" * 60)

    study = optuna.create_study(direction="maximize")
    study.optimize(lambda trial: objective(trial, base_df, feature_cols, config, trials_dir), n_trials=50)

    print("\n" + "=" * 60)
    print("Optimization complete!")
    print("=" * 60)
    print(f"Best trial: {study.best_trial.number}")
    print(f"Best accuracy: {study.best_trial.value:.4f}")
    print("Best parameters:")
    for key, value in study.best_trial.params.items():
        print(f"  {key}: {value}")

    optuna_results_path = project_root / "optuna_best_params.yaml"
    with open(optuna_results_path, "w") as f:
        yaml.dump(study.best_trial.params, f)
    print(f"\nBest parameters saved to: {optuna_results_path}")


if __name__ == "__main__":
    main()
