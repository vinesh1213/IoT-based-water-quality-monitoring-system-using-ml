# =============================================================================
# ML Classification Accuracy Test Script
# Produces: Accuracy, Confusion Matrix, Precision/Recall/F1 per class
# =============================================================================

import sys
import os
import warnings

# ensure stdout/stderr use UTF-8 on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # headless backend
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)

# Import pipeline functions from your training script
from water_quality_model import (
    load_dataset,
    clean_dataset,
    select_features,
    add_labels,
    split_data,
    train_model,
)

OUTPUT_DIR = "model_outputs"

def main():
    print("=" * 60)
    print("  ML CLASSIFICATION ACCURACY TEST")
    print("=" * 60)

    # ── Re-run the pipeline to get consistent train/test split ────────────
    df_raw      = load_dataset()
    df_clean    = clean_dataset(df_raw)
    df_feat, _  = select_features(df_clean)
    df_labelled = add_labels(df_feat)

    X_train, X_test, y_train, y_test, le, feat_names = split_data(df_labelled)

    # ── Train ─────────────────────────────────────────────────────────────
    model = train_model(X_train, y_train)

    # ── Predict on test set ───────────────────────────────────────────────
    y_pred = model.predict(X_test)

    class_names = list(le.classes_)

    # ══════════════════════════════════════════════════════════════════════
    # (1) OVERALL ACCURACY
    # ══════════════════════════════════════════════════════════════════════
    acc = accuracy_score(y_test, y_pred)
    print("\n" + "=" * 60)
    print(f"  (1) OVERALL ACCURACY : {acc * 100:.2f} %")
    print("=" * 60)
    print(f"      Correct predictions  : {int(acc * len(y_test))} / {len(y_test)}")

    # ══════════════════════════════════════════════════════════════════════
    # (2) CONFUSION MATRIX
    # ══════════════════════════════════════════════════════════════════════
    cm = confusion_matrix(y_test, y_pred)
    print("\n" + "=" * 60)
    print("  (2) CONFUSION MATRIX")
    print("=" * 60)

    # Pretty-print confusion matrix as table
    header = "Predicted ->  " + "  ".join(f"{c:>10}" for c in class_names)
    print(f"\n  {header}")
    print("  " + "-" * len(header))
    for i, row_label in enumerate(class_names):
        row_vals = "  ".join(f"{cm[i][j]:>10}" for j in range(len(class_names)))
        print(f"  {row_label:>12} | {row_vals}")

    print("\n  Interpretation:")
    for i, actual in enumerate(class_names):
        for j, predicted in enumerate(class_names):
            count = cm[i][j]
            if i == j:
                print(f"    Correctly classified as '{actual}' : {count}")
            elif count > 0:
                print(f"    Misclassified '{actual}' as '{predicted}' : {count}")

    # ══════════════════════════════════════════════════════════════════════
    # (3) PRECISION, RECALL, F1-SCORE PER CLASS
    # ══════════════════════════════════════════════════════════════════════
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, y_pred, labels=range(len(class_names)), zero_division=0
    )

    print("\n" + "=" * 60)
    print("  (3) PRECISION / RECALL / F1-SCORE  (per class)")
    print("=" * 60)
    print(f"\n  {'Class':>12}  {'Precision':>10}  {'Recall':>10}  {'F1-Score':>10}  {'Support':>10}")
    print("  " + "-" * 58)
    for i, cls in enumerate(class_names):
        print(f"  {cls:>12}  {precision[i]*100:>9.2f}%  {recall[i]*100:>9.2f}%  {f1[i]*100:>9.2f}%  {support[i]:>10}")

    # Weighted averages
    w_prec = np.average(precision, weights=support)
    w_rec  = np.average(recall, weights=support)
    w_f1   = np.average(f1, weights=support)
    print("  " + "-" * 58)
    print(f"  {'Weighted Avg':>12}  {w_prec*100:>9.2f}%  {w_rec*100:>9.2f}%  {w_f1*100:>9.2f}%  {sum(support):>10}")

    # ── Full sklearn classification report for reference ──────────────────
    print("\n" + "=" * 60)
    print("  FULL CLASSIFICATION REPORT (sklearn)")
    print("=" * 60)
    print(classification_report(y_test, y_pred, target_names=class_names, digits=4))

    # ══════════════════════════════════════════════════════════════════════
    # (4) SAVE CONFUSION MATRIX PLOT
    # ══════════════════════════════════════════════════════════════════════
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
        linewidths=0.5,
        linecolor="grey",
        annot_kws={"size": 14, "weight": "bold"},
        ax=ax,
    )
    ax.set_xlabel("Predicted Label", fontsize=13, labelpad=10)
    ax.set_ylabel("Actual Label",    fontsize=13, labelpad=10)
    ax.set_title("Confusion Matrix - Water Quality Classifier\n"
                 f"Overall Accuracy: {acc*100:.2f}%",
                 fontsize=15, pad=15, weight="bold")
    plt.tight_layout()

    cm_path = os.path.join(OUTPUT_DIR, "test_confusion_matrix.png")
    plt.savefig(cm_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\n  Confusion matrix image saved -> {cm_path}")

    # ── also save a per-class bar chart ───────────────────────────────────
    fig2, axes = plt.subplots(1, 3, figsize=(14, 5))
    metrics = [("Precision", precision), ("Recall", recall), ("F1-Score", f1)]
    colors = ["#2196F3", "#4CAF50", "#FF9800"]
    for ax_i, (metric_name, values) in enumerate(metrics):
        bars = axes[ax_i].bar(class_names, values * 100, color=colors[ax_i], edgecolor="white", width=0.5)
        axes[ax_i].set_title(metric_name, fontsize=13, weight="bold")
        axes[ax_i].set_ylim(0, 110)
        axes[ax_i].set_ylabel("Percentage (%)")
        for bar, v in zip(bars, values * 100):
            axes[ax_i].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                            f"{v:.1f}%", ha="center", va="bottom", fontsize=10, weight="bold")
    fig2.suptitle("Per-Class Metrics", fontsize=15, weight="bold", y=1.02)
    plt.tight_layout()
    metrics_path = os.path.join(OUTPUT_DIR, "test_per_class_metrics.png")
    fig2.savefig(metrics_path, dpi=150, bbox_inches="tight")
    plt.close(fig2)
    print(f"  Per-class metrics chart saved -> {metrics_path}")

    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
