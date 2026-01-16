from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from .losses import create_cross_entropy_loss
from .metrics import compute_classification_metrics


class Trainer:
    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: DataLoader,
        device: str = "cuda",
        lr: float = 0.001,
        class_weights: Optional[list[float]] = None,
        grad_clip: Optional[float] = None,
        output_dir: str | Path = ".",
    ) -> None:
        self.model = model.to(device)
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.device = torch.device(device)
        self.grad_clip = grad_clip
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Weighted loss for class imbalance
        self.criterion = create_cross_entropy_loss(class_weights=class_weights).to(self.device)
        self.optimizer = torch.optim.Adam(model.parameters(), lr=lr)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="max", patience=5, factor=0.5
        )

    def train_epoch(self) -> float:
        self.model.train()
        total_loss = 0.0

        for batch_x, batch_y in self.train_loader:
            batch_x = batch_x.to(self.device)
            batch_y = batch_y.to(self.device)

            self.optimizer.zero_grad(set_to_none=True)
            outputs = self.model(batch_x)
            loss = self.criterion(outputs, batch_y)
            loss.backward()

            if self.grad_clip is not None:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.grad_clip)

            self.optimizer.step()

            total_loss += loss.item()

        return total_loss / max(1, len(self.train_loader))

    def validate(self) -> dict:
        self.model.eval()
        all_preds = []
        all_labels = []

        with torch.no_grad():
            for batch_x, batch_y in self.val_loader:
                batch_x = batch_x.to(self.device)
                outputs = self.model(batch_x)
                preds = torch.argmax(outputs, dim=1)

                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(batch_y.numpy())

        return compute_classification_metrics(
            y_true=np.array(all_labels, dtype=int),
            y_pred=np.array(all_preds, dtype=int),
            target_names=["flat", "long", "short"],
        )

    def train(self, num_epochs: int = 100, early_stop_patience: int = 10) -> nn.Module:
        best_val_acc = 0.0
        patience_counter = 0
        best_model_path = self.output_dir / "best_model.pth"

        for epoch in range(num_epochs):
            train_loss = self.train_epoch()
            val_metrics = self.validate()
            val_acc = val_metrics["accuracy"]

            print(f"Epoch {epoch + 1}/{num_epochs}")
            print(f"Train Loss: {train_loss:.4f}, Val Accuracy: {val_acc:.4f}")

            self.scheduler.step(val_acc)

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                patience_counter = 0
                torch.save(self.model.state_dict(), best_model_path)
            else:
                patience_counter += 1

            if patience_counter >= early_stop_patience:
                print("Early stopping triggered")
                break

        if best_model_path.exists():
            self.model.load_state_dict(torch.load(best_model_path, map_location=self.device))

        return self.model
