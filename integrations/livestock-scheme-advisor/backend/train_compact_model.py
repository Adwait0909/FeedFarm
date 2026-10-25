"""Train the small serving model from the supplied synthetic scheme dataset.

Run from this directory with: python train_compact_model.py
The held-out split is used only for the reported validation metrics.
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "data" / "stage2_scheme_eligibility_slim.csv"
MODELS_DIR = BASE_DIR / "models"
FEATURE_METADATA_PATH = MODELS_DIR / "feature_metadata.json"
MODEL_PATH = MODELS_DIR / "eligibility_model_compact.joblib"
COMPACT_METADATA_PATH = MODELS_DIR / "compact_model_metadata.json"


def main() -> None:
    metadata = json.loads(FEATURE_METADATA_PATH.read_text(encoding="utf-8"))
    frame = pd.read_csv(DATA_PATH)
    feature_cols = metadata["feature_cols"]
    label_cols = [name for name in metadata["label_cols"] if name in frame.columns]
    train = frame[frame["split"] == "train"]
    valid = frame[frame["split"] == "val"]
    if train.empty or valid.empty or not label_cols:
        raise ValueError("Training data needs train/val rows and supported eligibility labels.")

    preprocess = ColumnTransformer(
        [
            ("categorical", OneHotEncoder(handle_unknown="ignore"), metadata["categorical_cols"]),
            ("numeric", "passthrough", metadata["numeric_cols"]),
        ]
    )
    model = Pipeline(
        [
            ("preprocess", preprocess),
            (
                "classifier",
                MultiOutputClassifier(
                    DecisionTreeClassifier(
                        max_depth=12,
                        min_samples_leaf=8,
                        random_state=42,
                    ),
                    n_jobs=1,
                ),
            ),
        ]
    )
    model.fit(train[feature_cols], train[label_cols].astype(int))

    prediction = model.predict(valid[feature_cols])
    truth = valid[label_cols].astype(int).to_numpy()
    metrics = {
        "validation_rows": len(valid),
        "labels": len(label_cols),
        "mean_label_accuracy": float((prediction == truth).mean()),
        "exact_match_accuracy": float((prediction == truth).all(axis=1).mean()),
    }
    compact_metadata = {
        "model_label_cols": label_cols,
        "validation": metrics,
        "training_data": str(DATA_PATH.name),
    }
    COMPACT_METADATA_PATH.write_text(
        json.dumps(compact_metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH, compress=3)
    print(json.dumps(metrics, indent=2))
    print(f"Saved compact model: {MODEL_PATH} ({MODEL_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
