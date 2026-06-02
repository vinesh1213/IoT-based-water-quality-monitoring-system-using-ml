# =============================================================================
# Smart Water Quality Monitoring System - ML Classification Model
# Compatible with: VS Code + Python 3.8+
# Dataset: AquaAttributes.xlsx
# Author: IoT Water Quality Project
# =============================================================================

# ── STEP 1: Import Required Libraries ────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import os
import sys
import warnings

# ensure stdout/stderr use UTF-8 on Windows so emoji prints don't crash
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

warnings.filterwarnings('ignore')

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)
from sklearn.preprocessing import LabelEncoder

# =============================================================================
# STEP 2: Load the Dataset from CSV
# =============================================================================

def load_dataset() -> pd.DataFrame:
    """
    Load the CSV files from the data set folder.
    """
    print("\n📂 Loading datasets from data set folder")

    data_folder = os.path.join(os.getcwd(), "data set")
    csv_files = [f for f in os.listdir(data_folder) if f.endswith('.csv')]
    
    if not csv_files:
        raise FileNotFoundError("No CSV files found in data set folder")

    dfs = []
    for csv_file in csv_files:
        file_path = os.path.join(data_folder, csv_file)
        print(f"Loading {csv_file}")
        df = pd.read_csv(file_path, encoding='cp1252')
        dfs.append(df)
    
    df = pd.concat(dfs, ignore_index=True)
    print(f"✅ Dataset loaded  →  {df.shape[0]} rows × {df.shape[1]} columns")
    print("\n📋 Columns found:", list(df.columns))
    print("\n🔍 First 5 rows:\n", df.head())
    return df


# =============================================================================
# STEP 3: Clean the Dataset
# =============================================================================

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    - Standardise column names (lowercase + strip spaces)
    - Drop columns that carry no useful information
    - Remove rows with missing values in key sensor columns
    """
    print("\n🧹 Cleaning dataset …")

    # Standardise column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    print("  Normalised column names:", list(df.columns))

    # Drop columns that are clearly non-numeric IDs or timestamps
    drop_candidates = ["id", "sample_id", "timestamp", "date", "location", "notes", "remarks"]
    cols_to_drop = [c for c in drop_candidates if c in df.columns]
    if cols_to_drop:
        df.drop(columns=cols_to_drop, inplace=True)
        print(f"  Dropped non-feature columns: {cols_to_drop}")

    # Report missing values before removal
    missing = df.isnull().sum()
    print("\n  Missing values per column:\n", missing[missing > 0])

    # Do not drop rows here, will drop in select_features after computing pH
    print(f"  Total rows: {len(df)}")

    return df


# =============================================================================
# STEP 4: Select Relevant Features & Map Column Names
# =============================================================================

# ── Flexible column name mapping ─────────────────────────────────────────────
# Keys   = what this script expects internally
# Values = possible real column names in your Excel sheet (add more if needed)
COLUMN_ALIASES = {
    "ph_min":            ["ph_min", "pH Min", "pH (Min)", "ph min", "ph_(min)"],
    "ph_max":            ["ph_max", "pH Max", "pH (Max)", "ph max", "ph_(max)"],
}

def resolve_columns(df: pd.DataFrame) -> dict:
    """
    Match internal feature names to actual column names in the DataFrame.
    Returns a dict: {internal_name: actual_column_name}
    """
    resolved = {}
    for internal, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                resolved[internal] = alias
                break
    return resolved


def select_features(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Identify which expected columns are present and return only pH.
    """
    print("\n🔎 Resolving feature columns …")
    mapping = resolve_columns(df)

    present   = list(mapping.keys())
    missing_f = [k for k in COLUMN_ALIASES if k not in mapping]

    print(f"  ✅ Found  : {present}")
    if missing_f:
        print(f"  ⚠️  Not found (will be skipped): {missing_f}")

    if "ph_min" not in mapping or "ph_max" not in mapping:
        raise ValueError(
            "❌ 'pH Min' and 'pH Max' columns are required but not found.\n"
            "   Check your CSV column names and update COLUMN_ALIASES above."
        )

    # Keep only resolved columns; rename to standard internal names
    actual_cols = list(mapping.values())
    df_feat = df[actual_cols].copy()
    df_feat.rename(columns={v: k for k, v in mapping.items()}, inplace=True)

    # Compute average pH
    df_feat['ph'] = (df_feat['ph_min'] + df_feat['ph_max']) / 2
    df_feat = df_feat[['ph']]
    df_feat.dropna(inplace=True)

    print(f"\n  Features selected: {list(df_feat.columns)}")
    return df_feat, mapping


# =============================================================================
# STEP 5: Create Water Quality Classification Labels
# =============================================================================

def classify_water_quality(row: pd.Series) -> str:
    """
    Classify pH levels.

    Hazard → pH < 6.5 or pH > 7.5
    Good   → 6.5 <= pH <= 7.5
    """
    ph = row.get("ph", 7.0)

    if ph < 6.5 or ph > 7.5:
        return "Hazard"
    else:
        return "Good"


def add_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the classification function row-wise and show class distribution."""
    print("\n🏷️  Generating water quality labels …")
    df["water_quality"] = df.apply(classify_water_quality, axis=1)

    dist = df["water_quality"].value_counts()
    print("  Label distribution:\n", dist.to_string())
    return df


# =============================================================================
# STEP 6: Train / Test Split
# =============================================================================

def split_data(df: pd.DataFrame, target_col: str = "water_quality",
               test_size: float = 0.2, random_state: int = 42):
    """
    Encode labels and split into stratified train / test sets (80 / 20).
    Returns X_train, X_test, y_train, y_test, label_encoder, feature_names.
    """
    print("\n✂️  Splitting dataset (80 % train / 20 % test) …")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=test_size,
        random_state=random_state, stratify=y_encoded
    )

    print(f"  Training samples : {len(X_train)}")
    print(f"  Testing  samples : {len(X_test)}")
    print(f"  Classes          : {list(le.classes_)}")

    return X_train, X_test, y_train, y_test, le, list(X.columns)


# =============================================================================
# STEP 7: Train Random Forest Classifier
# =============================================================================

def train_model(X_train, y_train, random_state: int = 42) -> RandomForestClassifier:
    """
    Train a Random Forest with 200 estimators.
    Random Forest is ideal for IoT sensor data because it:
      • Handles non-linear relationships between pH, DO, conductivity etc.
      • Is robust to outliers (common in raw sensor readings)
      • Provides built-in feature importance scores
    """
    print("\n🌲 Training Random Forest Classifier …")

    model = RandomForestClassifier(
        n_estimators=200,      # number of decision trees
        max_depth=10,          # prevents overfitting
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",  # handles class imbalance
        random_state=random_state,
        n_jobs=-1              # use all CPU cores
    )
    model.fit(X_train, y_train)
    print("  ✅ Training complete!")
    return model


# =============================================================================
# STEP 8: Evaluate the Model
# =============================================================================

def evaluate_model(model, X_test, y_test, le: LabelEncoder,
                   feature_names: list, output_dir: str = ".",
                   show_plots: bool = True):
    """
    Print accuracy + full classification report.
    Plot and save Confusion Matrix and Feature Importance charts.

    Parameters
    ----------
    show_plots : bool
        If True (the default) call ``plt.show()`` after creating each figure.
        Set to False for headless runs so the function doesn't block.
    """
    print("\n📊 Evaluating model …")
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    print(f"\n  ✅ Accuracy : {acc * 100:.2f} %")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))

    os.makedirs(output_dir, exist_ok=True)

    # ── Confusion Matrix ──────────────────────────────────────────────────────
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(7, 5))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=le.classes_)
    disp.plot(ax=ax, colorbar=True, cmap="Blues")
    ax.set_title("Confusion Matrix – Water Quality Classifier", fontsize=14, pad=12)
    plt.tight_layout()
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plt.savefig(cm_path, dpi=150)
    if show_plots:
        plt.show()
    plt.close(fig)
    print(f"  Confusion matrix saved → {cm_path}")

    # ── Feature Importance ────────────────────────────────────────────────────
    importances = model.feature_importances_
    sorted_idx  = np.argsort(importances)[::-1]

    fig, ax = plt.subplots(figsize=(8, 5))
    colours = plt.cm.RdYlGn(np.linspace(0.3, 0.9, len(feature_names)))
    bars = ax.bar(
        range(len(feature_names)),
        importances[sorted_idx],
        color=colours
    )
    ax.set_xticks(range(len(feature_names)))
    ax.set_xticklabels([feature_names[i] for i in sorted_idx], rotation=30, ha="right")
    ax.set_ylabel("Importance Score")
    ax.set_title("Feature Importance – Random Forest", fontsize=14, pad=12)
    for bar, imp in zip(bars, importances[sorted_idx]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.005,
                f"{imp:.3f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    fi_path = os.path.join(output_dir, "feature_importance.png")
    plt.savefig(fi_path, dpi=150)
    if show_plots:
        plt.show()
    plt.close(fig)
    print(f"  Feature importance chart saved → {fi_path}")

    return acc


# =============================================================================
# STEP 9: Save the Trained Model
# =============================================================================

def save_model(model, le: LabelEncoder, feature_names: list,
               output_dir: str = "."):
    """
    Persist the trained classifier, label encoder, and feature list to disk
    so they can be reloaded for prediction without retraining.
    """
    os.makedirs(output_dir, exist_ok=True)

    model_path   = os.path.join(output_dir, "water_quality_rf_model.joblib")
    encoder_path = os.path.join(output_dir, "label_encoder.joblib")
    features_path= os.path.join(output_dir, "feature_names.joblib")

    joblib.dump(model,         model_path)
    joblib.dump(le,            encoder_path)
    joblib.dump(feature_names, features_path)

    print(f"\n💾 Model saved      → {model_path}")
    print(f"   Encoder saved    → {encoder_path}")
    print(f"   Features saved   → {features_path}")


# =============================================================================
# STEP 10: Prediction Function (Live Sensor Input from ESP32)
# =============================================================================

def predict_water_quality(
    ph: float,
    turbidity: float      = 1.0,
    temperature: float    = 25.0,
    dissolved_oxygen: float = 8.0,
    conductivity: float   = 400.0,
    nitrate: float        = 5.0,
    model_dir: str        = "."
) -> dict:
    """
    Load the saved model and predict water quality from live sensor readings.

    Parameters (all floats, matching ESP32 sensor outputs):
      ph               – pH sensor reading       (ideal: 6.5 – 7.5)
      turbidity        – Turbidity sensor (NTU)  (ideal: < 4 NTU)
      temperature      – Temperature (°C)        (ideal: 10 – 30 °C)
      dissolved_oxygen – DO sensor (mg/L)        (ideal: > 6 mg/L)
      conductivity     – EC sensor (µS/cm)       (ideal: < 1000 µS/cm)
      nitrate          – Nitrate sensor (mg/L)   (ideal: < 10 mg/L)

    Returns:
      dict with 'prediction', 'confidence', and 'probabilities'
    """
    # Load saved artefacts
    model_path    = os.path.join(model_dir, "water_quality_rf_model.joblib")
    encoder_path  = os.path.join(model_dir, "label_encoder.joblib")
    features_path = os.path.join(model_dir, "feature_names.joblib")

    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"❌ Model not found at '{model_path}'.\n"
            "   Run the training script first to generate the model file."
        )

    model         = joblib.load(model_path)
    le            = joblib.load(encoder_path)
    feature_names = joblib.load(features_path)

    # Build sensor input dict
    sensor_data = {
        "ph":               ph,
        "temperature":      temperature,
        "dissolved_oxygen": dissolved_oxygen,
        "conductivity":     conductivity,
        "nitrate":          nitrate,
        "turbidity":        turbidity,
    }

    # Align with features the model was trained on
    input_row = pd.DataFrame(
        [[sensor_data.get(f, 0.0) for f in feature_names]],
        columns=feature_names
    )

    prediction_idx  = model.predict(input_row)[0]
    probabilities   = model.predict_proba(input_row)[0]
    predicted_class = le.inverse_transform([prediction_idx])[0]
    confidence      = probabilities[prediction_idx] * 100

    prob_dict = {le.classes_[i]: f"{p*100:.1f}%" for i, p in enumerate(probabilities)}

    result = {
        "prediction":    predicted_class,
        "confidence":    f"{confidence:.1f}%",
        "probabilities": prob_dict,
    }

    print("\n" + "═" * 45)
    print("  💧 WATER QUALITY PREDICTION RESULT")
    print("═" * 45)
    print(f"  pH              : {ph}")
    print(f"  Turbidity (NTU) : {turbidity}")
    print(f"  Temp (°C)       : {temperature}")
    print(f"  DO (mg/L)       : {dissolved_oxygen}")
    print(f"  Conductivity    : {conductivity}")
    print(f"  Nitrate (mg/L)  : {nitrate}")
    print("─" * 45)
    print(f"  🏷️  Prediction   : {predicted_class}")
    print(f"  📈 Confidence   : {confidence:.1f}%")
    print(f"  📊 Probabilities: {prob_dict}")
    print("═" * 45)

    return result


# =============================================================================
# MAIN – Run the full training pipeline
# =============================================================================

if __name__ == "__main__":

    # ── CONFIG ─────────────────────────────────────────────────────────────────
    DATASET_FILE = "AquaAttributes.xlsx"   # ← place this file in the same folder
    OUTPUT_DIR   = "model_outputs"         # plots + saved model go here

    # ── PIPELINE ───────────────────────────────────────────────────────────────
    print("=" * 55)
    print("  Smart Water Quality Monitoring System – ML Training")
    print("=" * 55)

    # 1. Load
    df_raw = load_dataset()

    # 2. Clean
    df_clean = clean_dataset(df_raw)

    # 3 & 4. Select features + create labels
    df_features, col_map = select_features(df_clean)
    df_labelled          = add_labels(df_features)

    # 5. Split
    X_train, X_test, y_train, y_test, label_enc, feat_names = split_data(df_labelled)

    # 6. Train
    rf_model = train_model(X_train, y_train)

    # 7. Evaluate
    evaluate_model(rf_model, X_test, y_test, label_enc, feat_names, OUTPUT_DIR, show_plots=False)

    # 8. Save
    save_model(rf_model, label_enc, feat_names, OUTPUT_DIR)

    # 9. Quick demo prediction with sample ESP32 sensor values
    print("\n🧪 Demo Prediction with sample ESP32 sensor readings …")
    predict_water_quality(
        ph=7.2,
        turbidity=2.5,
        temperature=24.0,
        dissolved_oxygen=7.8,
        conductivity=450.0,
        nitrate=8.0,
        model_dir=OUTPUT_DIR
    )

    print("\n✅ All done! Check the 'model_outputs' folder for saved files.")
