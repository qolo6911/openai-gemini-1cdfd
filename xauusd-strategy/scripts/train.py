#!/usr/bin/env python3
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import torch
import yaml
from joblib import dump
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


def prepare_data(config: dict):
    print("=" * 60)
    print("1. Connecting to MT5 and fetching data...")
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

        print(f"M15 data shape: {m15_data.shape}")
        print(f"H1 data shape: {h1_data.shape}")
        print(f"H4 data shape: {h4_data.shape}")

        print("\n" + "=" * 60)
        print("2. Calculating multi-timeframe features...")
        print("=" * 60)

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

        print("\n" + "=" * 60)
        print("3. Aligning timeframes to M15 (no look-ahead bias)...")
        print("=" * 60)

        aligned_df = feature_eng.align_to_m15(m15_features, h1_features, h4_features)
        aligned_df = feature_eng.detect_regime(aligned_df)

        print(f"Aligned data shape: {aligned_df.shape}")
        print(f"Regime distribution:\n{aligned_df['regime'].value_counts()}")

        print("\n" + "=" * 60)
        print("4. Generating triple barrier labels...")
        print("=" * 60)

        labeler = TripleBarrierLabeler(
            k1_tp=config["labeling"]["k1_tp"],
            k2_sl=config["labeling"]["k2_sl"],
            holding_period=config["labeling"]["holding_period"],
            spread_points=config["labeling"]["spread_points"],
            point_value=config["labeling"]["point_value"],
        )
        labeled_df = labeler.label_dataset(aligned_df)

        cost_labeler = CostAdjustedLabeler(min_profit_threshold=0.0)
        labeled_df = cost_labeler.filter_unprofitable(labeled_df)

        print(f"Label distribution:\n{labeled_df['label'].value_counts()}")
        print(f"Expected profit stats:\n{labeled_df['expected_profit'].describe()}")

        print("\n" + "=" * 60)
        print("5. Cleaning data (removing NaN)...")
        print("=" * 60)

        initial_len = len(labeled_df)
        labeled_df = labeled_df.dropna()
        print(f"Dropped {initial_len - len(labeled_df)} rows with NaN values")
        print(f"Final dataset shape: {labeled_df.shape}")

        return labeled_df
    finally:
        connector.shutdown()


def create_datasets(df, config: dict):
    print("\n" + "=" * 60)
    print("6. Creating sequences and train/val split...")
    print("=" * 60)

    excluded_cols = {"label", "expected_profit", "regime"}
    feature_cols = [col for col in df.columns if col not in excluded_cols]

    print(f"Using {len(feature_cols)} features")

    seq_config = SequenceConfig(lookback=config["training"]["lookback"])

    split_idx = int((1 - config["training"]["val_split"]) * len(df))
    train_df = df.iloc[:split_idx].copy()
    val_df = df.iloc[split_idx:].copy()

    print(f"Train samples (rows): {len(train_df)}, Val samples (rows): {len(val_df)}")

    scaler = StandardScaler()
    train_df[feature_cols] = scaler.fit_transform(train_df[feature_cols])
    val_df[feature_cols] = scaler.transform(val_df[feature_cols])

    train_dataset = TimeSeriesDataset(train_df, feature_cols, "label", seq_config)
    val_dataset = TimeSeriesDataset(val_df, feature_cols, "label", seq_config)

    print(f"Train sequences: {len(train_dataset)}, Val sequences: {len(val_dataset)}")

    if len(train_dataset) == 0 or len(val_dataset) == 0:
        raise ValueError("Dataset has no samples. Check your data range and lookback window.")

    return train_dataset, val_dataset, feature_cols, scaler


def compute_class_weights(train_dataset) -> list[float]:
    counts = np.bincount(train_dataset.y.numpy(), minlength=3)
    counts = np.where(counts == 0, 1, counts)
    total = counts.sum()
    weights = (total / (len(counts) * counts)).tolist()
    return weights


def main():
    config_path = project_root / "config.yaml"
    config = load_config(config_path)

    df = prepare_data(config)

    train_dataset, val_dataset, feature_cols, scaler = create_datasets(df, config)

    train_loader = DataLoader(
        train_dataset,
        batch_size=config["training"]["batch_size"],
        shuffle=True,
        num_workers=config["training"].get("num_workers", 0),
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config["training"]["batch_size"],
        shuffle=False,
        num_workers=config["training"].get("num_workers", 0),
    )

    print("\n" + "=" * 60)
    print("7. Initializing TCN model...")
    print("=" * 60)

    num_features = len(feature_cols)
    model_config = ModelConfig(
        type="tcn",
        num_channels=config["model"]["num_channels"],
        kernel_size=config["model"]["kernel_size"],
        dropout=config["model"]["dropout"],
    )
    model = create_model(num_features, model_config)

    device_str = config["training"]["device"]
    if device_str == "auto":
        device_str = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Using device: {device_str}")
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    class_weights = compute_class_weights(train_dataset)
    print(f"Class weights: {class_weights}")

    print("\n" + "=" * 60)
    print("8. Starting training...")
    print("=" * 60)

    artifact_dir = project_root / "artifacts"
    artifact_dir.mkdir(exist_ok=True)

    trainer = Trainer(
        model,
        train_loader,
        val_loader,
        device=device_str,
        lr=config["training"]["lr"],
        class_weights=class_weights,
        grad_clip=config["training"].get("grad_clip"),
        output_dir=artifact_dir,
    )

    trained_model = trainer.train(
        num_epochs=config["training"]["num_epochs"],
        early_stop_patience=config["training"]["early_stop_patience"],
    )

    final_metrics = trainer.validate()
    print("\nValidation metrics:")
    for key, value in final_metrics.items():
        if key in {"report", "confusion_matrix"}:
            continue
        print(f"  {key}: {value}")

    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)

    final_model_path = artifact_dir / "final_model.pth"
    torch.save(trained_model.state_dict(), final_model_path)
    print(f"Final model saved to: {final_model_path}")

    scaler_path = artifact_dir / "feature_scaler.joblib"
    dump(scaler, scaler_path)
    print(f"Feature scaler saved to: {scaler_path}")


if __name__ == "__main__":
    main()
