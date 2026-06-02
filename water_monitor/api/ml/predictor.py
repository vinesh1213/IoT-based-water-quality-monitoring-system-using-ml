"""
predictor.py — ML Prediction Helper
====================================
Loads the pre-trained Random Forest model (from model_outputs/) and
provides a single public function: predict(ph)

The model was trained with features:
  ph

For the ESP32 sensor setup, we only use pH sensor.
"""

import os
import logging
import pandas as pd
import joblib

logger = logging.getLogger(__name__)

# ─── Lazy-loaded globals (cached after first load) ────────────────────────────
_model         = None
_label_encoder = None
_feature_names = None


def _get_model_dir() -> str:
    """
    Returns the absolute path to model_outputs/ directory.
    Tries Django settings first, falls back to relative path search.
    """
    try:
        from django.conf import settings
        model_dir = str(settings.ML_MODEL_DIR)
        if os.path.isdir(model_dir):
            return model_dir
    except Exception:
        pass

    # Fallback: walk upward from this file to find model_outputs/
    current = os.path.dirname(__file__)
    for _ in range(6):
        candidate = os.path.join(current, 'model_outputs')
        if os.path.isdir(candidate):
            return candidate
        current = os.path.dirname(current)

    raise FileNotFoundError(
        "Cannot locate model_outputs/ directory. "
        "Make sure the trained model files exist there."
    )


def _load_model():
    """Load model artifacts from disk (once) and cache globally."""
    global _model, _label_encoder, _feature_names

    if _model is not None:
        return  # Already loaded

    model_dir = _get_model_dir()
    model_path    = os.path.join(model_dir, 'water_quality_rf_model.joblib')
    encoder_path  = os.path.join(model_dir, 'label_encoder.joblib')
    features_path = os.path.join(model_dir, 'feature_names.joblib')

    logger.info(f"Loading ML model from: {model_dir}")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            "Run water_quality_model.py first to train and save the model."
        )

    _model         = joblib.load(model_path)
    _label_encoder = joblib.load(encoder_path)
    _feature_names = joblib.load(features_path)

    logger.info(f"Model loaded — features: {_feature_names}")
    logger.info(f"Label classes: {list(_label_encoder.classes_)}")


def predict(ph: float) -> dict:
    """
    Run the Random Forest classifier on pH reading.

    Parameters
    ----------
    ph : pH value from sensor (required)

    Returns
    -------
    dict:
        prediction   — 'Acidic' | 'Neutral' | 'Basic'
        confidence   — e.g. '92.4%'
        probabilities— dict of class → probability string
    """
    _load_model()

    # Build input with only pH
    input_row = pd.DataFrame([[ph]], columns=_feature_names)

    pred_idx   = _model.predict(input_row)[0]
    proba      = _model.predict_proba(input_row)[0]
    pred_class = _label_encoder.inverse_transform([pred_idx])[0]
    confidence = proba[pred_idx] * 100

    prob_dict = {
        _label_encoder.classes_[i]: f"{p * 100:.1f}%"
        for i, p in enumerate(proba)
    }

    result = {
        'prediction':    pred_class,
        'confidence':    f"{confidence:.1f}%",
        'probabilities': prob_dict,
    }

    logger.info(f"Prediction: {pred_class} ({confidence:.1f}%) | pH={ph}")
    return result
