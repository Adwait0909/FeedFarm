"""Livestock Scheme Advisor API. Run: python -m uvicorn app:app --reload --port 8000"""
from __future__ import annotations

import io
import json
import os
import threading
from pathlib import Path
from typing import Optional, Any, Literal

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

# Photo-model safety net. The breed CNN only knows the classes in breed_labels.json, so a hen,
# a goat or a dog still gets squeezed into one of them. We refuse to answer when the model is
# not clearly sure. Tune these two numbers by testing a few photos of unsupported animals.
# Override without editing code:  BREED_MIN_CONFIDENCE=0.7 BREED_MIN_MARGIN=0.25 uvicorn ...
BREED_MIN_CONFIDENCE = float(os.getenv("BREED_MIN_CONFIDENCE", "0.60"))  # top class at least this sure
BREED_MIN_MARGIN = float(os.getenv("BREED_MIN_MARGIN", "0.20"))          # and this far ahead of #2

app = FastAPI(title="Livestock Scheme Advisor API", version="1.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your frontend origin in production.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

breed_model = None
breed_classes: list[str] = []
breed_img_size = (224, 224)
breed_mean = [0.485, 0.456, 0.406]
breed_std = [0.229, 0.224, 0.225]
eligibility_pipeline = None
top1_pipeline = None
top1_encoder = None
feature_metadata: dict[str, Any] = {}
rules_manifest: dict[str, Any] = {}
scheme_lookup: dict[str, dict[str, Any]] = {}
artifact_errors: dict[str, str] = {}
_artifacts_loaded = False
_artifact_load_lock = threading.Lock()


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        result = json.load(f)
    if not isinstance(result, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return result


def _build_breed_architecture(num_classes: int, architecture: str = "mobilenet_v2"):
    """Rebuild the exact torchvision architecture used in training, so a plain state_dict
    (just the learned numbers) can be loaded into it. Deliberately avoids torch.jit/TorchScript
    entirely -- PyTorch's own loader currently warns that torch.jit.load is unreliable on
    Python 3.14+ ("switch to torch.export"), and a plain state_dict has no such caveat."""
    import torch.nn as nn
    from torchvision import models as tv_models

    if architecture != "mobilenet_v2":
        raise ValueError(f"Unsupported architecture '{architecture}' in breed_labels.json")

    model = tv_models.mobilenet_v2(weights=None)  # weights=None: we're about to load our own
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, num_classes)
    return model


def repair_breed_labels(classes: list[str], valid_options: list[str]) -> list[str]:
    """Make the photo model's class names match the names the eligibility model was trained on.

    breed_labels.json can contain a name cut off at a comma, e.g. "Crossbred (HF" instead of
    "Crossbred (HF/Jersey)". Sent as-is, that fails validation in /predict/eligibility. A class
    is repaired only when exactly ONE valid option starts with it; anything ambiguous or
    unmatched is left alone. The class ORDER never changes, so the trained weights still line up.
    """
    if not valid_options:
        return classes
    valid = set(valid_options)
    fixed: list[str] = []
    for name in classes:
        if name in valid:
            fixed.append(name)
            continue
        matches = [opt for opt in valid_options if opt.startswith(name)]
        if len(matches) == 1:
            print(f"[startup] Repaired breed label '{name}' -> '{matches[0]}'")
            fixed.append(matches[0])
        else:
            print(f"[startup] WARNING: breed label '{name}' is not in breed_options and could not be repaired")
            fixed.append(name)
    return fixed


@app.on_event("startup")
def load_artifacts():
    global breed_model, breed_classes, breed_img_size, breed_mean, breed_std
    global eligibility_pipeline, top1_pipeline, top1_encoder
    global feature_metadata, rules_manifest, scheme_lookup, artifact_errors

    artifact_errors = {}
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Stage 1: PyTorch CNN, loaded from a plain state_dict (not TorchScript/torch.jit).
    labels_path = MODELS_DIR / "breed_labels.json"
    weights_path = MODELS_DIR / "breed_classifier_weights.pt"
    if labels_path.is_file() and weights_path.is_file():
        try:
            import torch

            meta = read_json(labels_path)
            classes = meta.get("classes", [])
            if not classes:
                raise ValueError("breed_labels.json has no non-empty 'classes' list")

            model = _build_breed_architecture(
                num_classes=len(classes),
                architecture=meta.get("architecture", "mobilenet_v2"),
            )
            state_dict = torch.load(str(weights_path), map_location="cpu", weights_only=True)
            model.load_state_dict(state_dict)
            model.eval()

            breed_model = model
            breed_classes = classes
            # Metadata commonly stores [height, width].
            breed_img_size = tuple(meta.get("img_size", [224, 224]))
            breed_mean = meta.get("mean", breed_mean)
            breed_std = meta.get("std", breed_std)
            print(f"[startup] Loaded breed classifier ({len(breed_classes)} classes)")
        except Exception as e:
            breed_model = None
            artifact_errors["breed"] = str(e)
            print(f"[startup] ERROR loading breed classifier: {e}")
    else:
        print("[startup] Breed model or labels missing; breed endpoint unavailable. "
              "Expected models/breed_classifier_weights.pt + models/breed_labels.json.")

    # Stage 2: serialized sklearn models. Versions must match training version.
    elig_path = MODELS_DIR / "eligibility_model_compact.joblib"
    top1_path = MODELS_DIR / "top1_model.joblib"
    encoder_path = MODELS_DIR / "top1_label_encoder.joblib"
    metadata_path = MODELS_DIR / "feature_metadata.json"
    compact_metadata_path = MODELS_DIR / "compact_model_metadata.json"
    manifest_path = MODELS_DIR / "rules_manifest.json"

    if elig_path.is_file():
        try:
            eligibility_pipeline = joblib.load(elig_path)
            print("[startup] Loaded compact eligibility model")
        except Exception as e:
            eligibility_pipeline = None
            artifact_errors["eligibility"] = str(e)
            print(f"[startup] ERROR loading eligibility model: {e}")
    else:
        print("[startup] eligibility_model_compact.joblib missing.")

    if top1_path.is_file() and encoder_path.is_file():
        try:
            top1_pipeline = joblib.load(top1_path)
            top1_encoder = joblib.load(encoder_path)
            print("[startup] Loaded top1 model and encoder")
        except Exception as e:
            top1_pipeline = top1_encoder = None
            artifact_errors["top1"] = str(e)
            print(f"[startup] ERROR loading top1 artifacts: {e}")
    else:
        print("[startup] top1 model or encoder missing.")

    if metadata_path.is_file():
        try:
            feature_metadata = read_json(metadata_path)
            print("[startup] Loaded feature_metadata.json")
        except Exception as e:
            feature_metadata = {}
            artifact_errors["feature_metadata"] = str(e)
            print(f"[startup] ERROR loading feature metadata: {e}")
    else:
        print("[startup] WARNING: feature_metadata.json missing.")

    if compact_metadata_path.is_file():
        try:
            compact_metadata = read_json(compact_metadata_path)
            feature_metadata["model_label_cols"] = compact_metadata.get("model_label_cols", [])
            print(
                "[startup] Loaded compact model metadata "
                f"({len(feature_metadata['model_label_cols'])} labels)"
            )
        except Exception as e:
            artifact_errors["compact_model_metadata"] = str(e)
            print(f"[startup] ERROR loading compact model metadata: {e}")

    if manifest_path.is_file():
        try:
            rules_manifest = read_json(manifest_path)
            scheme_lookup = {
                str(x["code"]): x for x in rules_manifest.get("labels", [])
                if isinstance(x, dict) and "code" in x
            }
            print(f"[startup] Loaded rules_manifest.json ({len(scheme_lookup)} schemes)")
        except Exception as e:
            rules_manifest, scheme_lookup = {}, {}
            artifact_errors["rules_manifest"] = str(e)
            print(f"[startup] ERROR loading rules manifest: {e}")
    else:
        print("[startup] WARNING: rules_manifest.json missing.")

    # Runs last, because it needs both the photo model's classes and feature_metadata.
    if breed_classes and feature_metadata.get("breed_options"):
        breed_classes = repair_breed_labels(breed_classes, feature_metadata["breed_options"])


def ensure_artifacts_loaded():
    """Load bundled models once when a scheme API request first needs them."""
    global _artifacts_loaded
    if _artifacts_loaded:
        return
    with _artifact_load_lock:
        if not _artifacts_loaded:
            load_artifacts()
            _artifacts_loaded = True


class FarmerProfile(BaseModel):
    breed: str = Field(..., description="Breed predicted from photo or selected manually")
    animals_owned: int = Field(..., ge=0)
    social_category: str
    land_holding: str
    employment_status: str
    gender: str
    district: str


class SchemeResult(BaseModel):
    code: str
    name: str
    level: Optional[str] = None
    kind: Optional[str] = None
    eligible: Optional[bool] = None
    eligibility_status: Literal["estimated", "unscored"]
    confidence: Optional[float] = None


class TopPick(BaseModel):
    code: str
    name: str
    score: Optional[float] = None


class EligibilityResponse(BaseModel):
    species: Optional[str] = None
    top1_recommendation: Optional[str] = None
    top_recommendations: list[TopPick] = []
    eligible_count: int
    scored_count: int
    unscored_count: int
    recommendation_method: Literal[
        "trained_ranker", "eligibility_confidence_fallback", "none"
    ]
    schemes: list[SchemeResult]


def validate_option(field: str, value: str, key: str):
    options = feature_metadata.get(key)
    if options and value not in options:
        raise HTTPException(400, f"Invalid {field} '{value}'. Expected one of: {options}")


def image_tensor(raw: bytes):
    import torch
    from PIL import Image
    try:
        image = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise ValueError(f"Unsupported or corrupt image: {e}") from e
    height, width = breed_img_size
    image = image.resize((width, height))
    arr = np.asarray(image, dtype=np.float32) / 255.0
    arr = (arr - np.asarray(breed_mean, dtype=np.float32)) / np.asarray(breed_std, dtype=np.float32)
    arr = arr.transpose(2, 0, 1)
    return torch.from_numpy(np.ascontiguousarray(arr)).float().unsqueeze(0)


@app.get("/")
def root():
    ensure_artifacts_loaded()
    model_metadata = {}
    compact_metadata_path = MODELS_DIR / "compact_model_metadata.json"
    if compact_metadata_path.is_file():
        try:
            model_metadata = read_json(compact_metadata_path)
        except Exception:
            model_metadata = {}
    return {
        "status": "ok",
        "breed_model_loaded": breed_model is not None,
        "eligibility_model_loaded": eligibility_pipeline is not None,
        "top1_model_loaded": top1_pipeline is not None and top1_encoder is not None,
        "feature_metadata_loaded": bool(feature_metadata),
        "rules_manifest_loaded": bool(rules_manifest),
        "breed_classes": breed_classes,
        "breed_thresholds": {"min_confidence": BREED_MIN_CONFIDENCE, "min_margin": BREED_MIN_MARGIN},
        "artifact_errors": artifact_errors,
        "options": {
            "social_category": feature_metadata.get("social_category_options"),
            "land_holding": feature_metadata.get("land_holding_options"),
            "employment_status": feature_metadata.get("employment_status_options"),
            "gender": feature_metadata.get("gender_options"),
            "district": feature_metadata.get("district_options"),
            "breed": feature_metadata.get("breed_options"),
        },
        "breed_species_map": feature_metadata.get("breed_species_map", {}),
        "eligibility_coverage": {
            "catalogue_schemes": len(scheme_lookup),
            "model_scored_schemes": len(feature_metadata.get("model_label_cols", [])),
            "validation_metrics": model_metadata.get("validation"),
            "training_data": model_metadata.get("training_data"),
            "warning": (
                "The supplied eligibility dataset is generated from assumptions and "
                "rule patterns; validation metrics do not establish real-world eligibility."
            ),
        },
    }


@app.get("/health")
def health():
    ensure_artifacts_loaded()
    return {
        "status": "ok",
        "models_dir": str(MODELS_DIR),
        "loaded": {
            "breed": breed_model is not None,
            "eligibility": eligibility_pipeline is not None,
            "top1": top1_pipeline is not None and top1_encoder is not None,
        },
        "artifact_errors": artifact_errors,
    }


@app.post("/predict/breed")
async def predict_breed(file: UploadFile = File(...)):
    ensure_artifacts_loaded()
    if breed_model is None:
        raise HTTPException(
            503,
            "Breed classifier not loaded. Check models/breed_classifier_weights.pt and "
            "models/breed_labels.json; inspect / for details.",
        )
    import torch
    raw = await file.read()
    try:
        tensor = image_tensor(raw)
    except Exception as e:
        raise HTTPException(400, f"Could not read image: {e}") from e
    try:
        with torch.no_grad():
            output = breed_model(tensor)
            # `output` is the whole batch's logits, shape (batch_size, num_classes) — here
            # batch_size is always 1 (one uploaded photo per request). Some architectures
            # return a tuple (e.g. auxiliary-loss heads); unwrap that first, THEN pull out
            # this single example, THEN softmax across the class dimension (dim=1 of the
            # batch, which becomes dim=0 once we've dropped the batch dimension).
            batched_logits = output[0] if isinstance(output, (tuple, list)) else output
            logits = batched_logits[0]  # this request's one image
            probs = torch.softmax(logits, dim=0).cpu().numpy()
    except Exception as e:
        raise HTTPException(500, f"Breed inference failed: {e}") from e
    if len(probs) != len(breed_classes):
        raise HTTPException(500, "Model output count does not match breed_labels.json classes.")

    order = np.argsort(-probs)
    top = float(probs[int(order[0])])
    second = float(probs[int(order[1])]) if len(order) > 1 else 0.0
    top5 = [
        {"breed": breed_classes[int(i)], "confidence": float(probs[int(i)])}
        for i in order[:5]
    ]

    # A closed-set classifier must pick *something*, so a hen or a goat can come back as
    # "buffalo". When the model is not clearly sure, say so instead of guessing.
    # The best guess is ALWAYS returned, so a frontend that ignores `recognized` still shows a
    # breed name instead of going blank. A frontend that reads the flag can warn the user.
    recognized = not (top < BREED_MIN_CONFIDENCE or (top - second) < BREED_MIN_MARGIN)
    if not recognized:
        return {
            "predicted_breed": breed_classes[int(order[0])],
            "recognized": False,
            "confidence": top,
            "top5": top5,
            "note": "Low confidence: this may not be a supported animal. Ask the user to confirm or select the breed manually.",
        }

    return {
        "predicted_breed": breed_classes[int(order[0])],
        "recognized": True,
        "confidence": top,
        "top5": top5,
        "note": "Only breeds listed in breed_labels.json are recognized. Select unsupported species manually.",
    }


@app.post("/predict/eligibility", response_model=EligibilityResponse)
def predict_eligibility(profile: FarmerProfile):
    ensure_artifacts_loaded()
    if eligibility_pipeline is None:
        raise HTTPException(
            503,
            "Compact eligibility model not loaded. Check models/eligibility_model_compact.joblib and inspect / for artifact_errors.",
        )
    if not feature_metadata:
        raise HTTPException(
            503,
            "feature_metadata.json is missing or invalid. Copy the actual file exported by Colab into backend/models/.",
        )

    for field, key in [
        ("breed", "breed_options"),
        ("social_category", "social_category_options"),
        ("land_holding", "land_holding_options"),
        ("employment_status", "employment_status_options"),
        ("gender", "gender_options"),
        ("district", "district_options"),
    ]:
        validate_option(field, getattr(profile, field), key)

    row = pd.DataFrame([{
        "breed": profile.breed,
        "animals_owned": profile.animals_owned,
        "social_category": profile.social_category,
        "land_holding": profile.land_holding,
        "employment_status": profile.employment_status,
        "gender": profile.gender,
        "district": profile.district,
    }])

    label_cols = feature_metadata.get(
        "model_label_cols",
        feature_metadata.get("label_cols", []),
    )
    if not isinstance(label_cols, list) or not label_cols:
        raise HTTPException(503, "feature_metadata.json must contain a non-empty label_cols list.")

    try:
        pred = np.asarray(eligibility_pipeline.predict(row)[0]).reshape(-1)
    except Exception as e:
        raise HTTPException(500, f"Eligibility prediction failed: {e}") from e
    if len(pred) != len(label_cols):
        raise HTTPException(500, f"Model returned {len(pred)} predictions, metadata lists {len(label_cols)} labels.")

    confidences: list[Optional[float]] = [None] * len(label_cols)
    try:
        probas = eligibility_pipeline.predict_proba(row)
        if isinstance(probas, list):
            confidences = [
                float(p[0][1]) if p.shape[1] > 1 else (1.0 if bool(pred[i]) else 0.0)
                for i, p in enumerate(probas)
            ]
    except Exception:
        pass

    # Return the complete catalogue, but distinguish model estimates from schemes
    # that have no score. Missing labels are not negative eligibility decisions.
    scored_by_code = {
        str(col).removeprefix("elig_"): (bool(pred[i]), confidences[i])
        for i, col in enumerate(label_cols)
    }
    catalog = dict(scheme_lookup)
    for code in scored_by_code:
        catalog.setdefault(code, {})

    results = []
    for code, meta in catalog.items():
        scored = scored_by_code.get(code)
        results.append(SchemeResult(
            code=code,
            name=meta.get("name", code),
            level=meta.get("level"),
            kind=meta.get("kind"),
            eligible=scored[0] if scored is not None else None,
            eligibility_status="estimated" if scored is not None else "unscored",
            confidence=scored[1] if scored is not None else None,
        ))
    results.sort(key=lambda x: (
        x.eligibility_status == "unscored",
        x.eligible is not True,
        x.code,
    ))

    # Top recommendations: rank every scheme by the top-1 model's probability, but never
    # headline one the eligibility model says the farmer cannot get.
    recommendation = None
    top_picks: list[TopPick] = []
    recommendation_method = "none"
    if top1_pipeline is not None and top1_encoder is not None:
        try:
            eligible_codes = {r.code for r in results if r.eligible}
            ranked: list[tuple[str, Optional[float]]] = []
            try:
                probs = np.asarray(top1_pipeline.predict_proba(row)[0], dtype=float)
                labels = top1_encoder.inverse_transform(np.asarray(top1_pipeline.classes_))
                if len(probs) == len(labels):
                    ranked = [(str(labels[i]), float(probs[i])) for i in np.argsort(-probs)]
            except Exception:
                ranked = []
            if not ranked:
                # Estimator without predict_proba: fall back to the single predicted label.
                encoded = top1_pipeline.predict(row)[0]
                ranked = [(str(top1_encoder.inverse_transform([encoded])[0]), None)]

            shortlist = [(c, s) for c, s in ranked if c in eligible_codes]
            for code, score in shortlist[:2]:
                top_picks.append(TopPick(
                    code=code,
                    name=scheme_lookup.get(code, {}).get("name", code),
                    score=score,
                ))
            recommendation = top_picks[0].code if top_picks else None
            if recommendation:
                recommendation_method = "trained_ranker"
        except Exception as e:
            print(f"[predict] Top recommendation skipped: {e}")
    else:
        eligible = [item for item in results if item.eligible]
        # The original top-1 ranking artifact is not distributed with this app.
        # Do not pretend catalogue priority is a learned recommendation model: use
        # the eligibility model's own confidence as a transparent fallback.
        eligible.sort(
            key=lambda item: (-(item.confidence if item.confidence is not None else -1.0), item.code)
        )
        top_picks = [
            TopPick(
                code=item.code,
                name=item.name,
                score=item.confidence,
            )
            for item in eligible[:2]
        ]
        recommendation = top_picks[0].code if top_picks else None
        if recommendation:
            recommendation_method = "eligibility_confidence_fallback"

    species = feature_metadata.get("breed_species_map", {}).get(profile.breed)
    return EligibilityResponse(
        species=species,
        top1_recommendation=recommendation,
        top_recommendations=top_picks,
        eligible_count=sum(item.eligible is True for item in results),
        scored_count=len(scored_by_code),
        unscored_count=sum(item.eligibility_status == "unscored" for item in results),
        recommendation_method=recommendation_method,
        schemes=results,
    )