"""Training loop for the TCN model with progress callbacks."""
from __future__ import annotations

from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, TensorDataset

from core.models.tcn import TCNModel
from utils.logger import get_logger

logger = get_logger(__name__)


class Trainer:
    def __init__(
        self,
        model: TCNModel,
        learning_rate: float = 0.001,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = torch.nn.CrossEntropyLoss()
        self.history = {"train_loss": [], "val_loss": [], "val_acc": []}

    def prepare_data(
        self,
        df: pd.DataFrame,
        feature_columns: list[str],
        label_column: str = "label",
        sequence_length: int = 50,
        batch_size: int = 64,
        test_size: float = 0.2,
    ) -> tuple[DataLoader, DataLoader]:
        features = df[feature_columns].values
        labels = df[label_column].values

        X_seq, y_seq = [], []
        for i in range(len(df) - sequence_length):
            X_seq.append(features[i : i + sequence_length])
            y_seq.append(labels[i + sequence_length - 1])

        X_seq = np.array(X_seq, dtype=np.float32)
        y_seq = np.array(y_seq, dtype=np.int64)

        X_train, X_val, y_train, y_val = train_test_split(
            X_seq, y_seq, test_size=test_size, shuffle=False
        )

        train_dataset = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
        val_dataset = TensorDataset(torch.tensor(X_val), torch.tensor(y_val))

        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

        logger.info(
            f"Training samples: {len(X_train)}, Validation samples: {len(X_val)}"
        )
        return train_loader, val_loader

    def train_epoch(self, train_loader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0

        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)

            self.optimizer.zero_grad()
            outputs = self.model(X_batch)
            loss = self.criterion(outputs, y_batch)
            loss.backward()
            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / len(train_loader)

    def validate(self, val_loader: DataLoader) -> tuple[float, float]:
        self.model.eval()
        total_loss = 0.0
        correct = 0
        total = 0

        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)

                outputs = self.model(X_batch)
                loss = self.criterion(outputs, y_batch)
                total_loss += loss.item()

                _, predicted = torch.max(outputs, 1)
                correct += (predicted == y_batch).sum().item()
                total += y_batch.size(0)

        avg_loss = total_loss / len(val_loader)
        accuracy = correct / total
        return avg_loss, accuracy

    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        epochs: int = 100,
        progress_callback: Callable[[int, float, float, float], None] | None = None,
    ) -> None:
        logger.info(f"Starting training for {epochs} epochs on {self.device}")

        for epoch in range(1, epochs + 1):
            train_loss = self.train_epoch(train_loader)
            val_loss, val_acc = self.validate(val_loader)

            self.history["train_loss"].append(train_loss)
            self.history["val_loss"].append(val_loss)
            self.history["val_acc"].append(val_acc)

            logger.info(
                f"Epoch {epoch}/{epochs} | Train Loss: {train_loss:.4f} | "
                f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.4f}"
            )

            if progress_callback:
                progress_callback(epoch, train_loss, val_loss, val_acc)

    def save_model(self, path: str | Path) -> None:
        torch.save(
            {
                "model_state": self.model.state_dict(),
                "optimizer_state": self.optimizer.state_dict(),
                "history": self.history,
            },
            path,
        )
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str | Path) -> None:
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state"])
        self.history = checkpoint.get("history", self.history)
        logger.info(f"Model loaded from {path}")
