"""04_classification.py — XGBoost: predice winning_action_type"""

import json
import pickle
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, roc_curve,
)
from xgboost import XGBClassifier
from tqdm import tqdm
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
MODELS = ROOT / "outputs" / "models"
METRICS_FILE = ROOT / "outputs" / "metrics.json"

FIGURES.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.2

FEATURE_COLS = [
    "avg_hp_p1", "avg_attack_p1", "avg_defense_p1",
    "avg_sp_attack_p1", "avg_sp_defense_p1", "avg_speed_p1",
    "type_diversity_p1", "n_fast_pokemon_p1", "type_coverage_p1",
    "avg_hp_p2", "avg_attack_p2", "avg_defense_p2",
    "avg_sp_attack_p2", "avg_sp_defense_p2", "avg_speed_p2",
    "type_diversity_p2", "n_fast_pokemon_p2", "type_coverage_p2",
    "stat_total_diff", "speed_advantage_ratio", "switch_rate", "n_turns",
]
TARGET_COL = "winning_action_type"


# ── Device detection ────────────────────────────────────────────────────────


def detect_device() -> str:
    try:
        import subprocess
        result = subprocess.run(
            ["nvidia-smi"], capture_output=True, timeout=5
        )
        if result.returncode == 0:
            return "cuda"
    except Exception:
        pass
    return "cpu"


def build_model(device: str) -> XGBClassifier:
    return XGBClassifier(
        n_estimators=1000,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        eval_metric="mlogloss",
        early_stopping_rounds=20,
        random_state=RANDOM_STATE,
        device=device,
        verbosity=0,
    )


# ── Figures ─────────────────────────────────────────────────────────────────


_DARK = "#1a1a2e"
_MID = "#16213e"
_ACCENT = "#e63946"
_GOLD = "#ffd700"
_BLUE = "#4cc9f0"


def _dark_fig(figsize=(10, 7)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_MID)
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for sp in ax.spines.values():
        sp.set_edgecolor("#444")
    return fig, ax


def plot_confusion_matrix(y_true, y_pred, classes: list) -> None:
    cm = confusion_matrix(y_true, y_pred)
    cm_pct = cm.astype(float) / cm.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(8, 7))
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_MID)

    im = ax.imshow(cm_pct, cmap="YlOrRd", vmin=0, vmax=1)
    plt.colorbar(im, ax=ax).ax.yaxis.set_tick_params(color="white")

    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, color="white", rotation=30, ha="right")
    ax.set_yticklabels(classes, color="white")
    ax.set_xlabel("Predicho", color="white")
    ax.set_ylabel("Real", color="white")
    ax.set_title("Matriz de Confusión (normalizada)", color="white", pad=12)

    for i in range(len(classes)):
        for j in range(len(classes)):
            txt = f"{cm_pct[i,j]:.2f}\n({cm[i,j]:,})"
            color = "white" if cm_pct[i, j] < 0.6 else "black"
            ax.text(j, i, txt, ha="center", va="center",
                    color=color, fontsize=8)

    plt.tight_layout()
    plt.savefig(FIGURES / "confusion_matrix.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ confusion_matrix.png")


def plot_feature_importance(model: XGBClassifier, feature_names: list) -> None:
    imp = model.feature_importances_
    idx = np.argsort(imp)[::-1]
    names = [feature_names[i] for i in idx]
    vals = imp[idx]

    fig, ax = _dark_fig(figsize=(10, 7))
    colors = [_ACCENT if v == vals.max() else _BLUE for v in vals]
    bars = ax.barh(range(len(names)), vals[::-1], color=colors[::-1])
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names[::-1], color="white", fontsize=9)
    ax.set_xlabel("Importancia (gain)")
    ax.set_title("Feature Importance — XGBoost")
    ax.axvline(vals.mean(), color=_GOLD, linestyle="--", alpha=0.6, label="Promedio")
    ax.legend(facecolor=_DARK, labelcolor="white")

    plt.tight_layout()
    plt.savefig(FIGURES / "feature_importance.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ feature_importance.png")


def plot_roc_curves(y_test_bin, y_prob, classes: list) -> None:
    COLORS = [_ACCENT, _GOLD, _BLUE, "#06d6a0"]
    fig, ax = _dark_fig(figsize=(9, 7))

    for i, cls in enumerate(classes):
        fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_prob[:, i])
        auc = roc_auc_score(y_test_bin[:, i], y_prob[:, i])
        ax.plot(fpr, tpr, color=COLORS[i % len(COLORS)],
                linewidth=2, label=f"{cls} (AUC={auc:.3f})")

    ax.plot([0, 1], [0, 1], "w--", alpha=0.4)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("Curvas ROC — Clasificación multiclase (OvR)")
    ax.legend(facecolor=_DARK, labelcolor="white")

    plt.tight_layout()
    plt.savefig(FIGURES / "roc_curves.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ roc_curves.png")


# ── Metrics persistence ─────────────────────────────────────────────────────


def save_metrics(report: dict, roc_aucs: dict, best_iteration: int,
                 device_used: str) -> None:
    existing = {}
    if METRICS_FILE.exists():
        with open(METRICS_FILE) as f:
            existing = json.load(f)
    existing["classification"] = {
        "device": device_used,
        "best_iteration": best_iteration,
        "accuracy": report["accuracy"],
        "macro_f1": report["macro avg"]["f1-score"],
        "weighted_f1": report["weighted avg"]["f1-score"],
        "roc_auc_per_class": roc_aucs,
        "per_class": {
            cls: report[cls]
            for cls in report
            if cls not in ("accuracy", "macro avg", "weighted avg")
        },
    }
    with open(METRICS_FILE, "w") as f:
        json.dump(existing, f, indent=2)
    print("  ✓ metrics.json actualizado")


# ── Main ────────────────────────────────────────────────────────────────────


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def main() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║    Pokémon Showdown — Clasificación XGBoost      ║")
    print("╚══════════════════════════════════════════════════╝")

    section("1/5  Cargando datos")
    df = pd.read_parquet(PROCESSED / "battles_featured.parquet")
    print(f"  ✓ {len(df):,} batallas")
    print(f"  Distribución target:\n{df[TARGET_COL].value_counts().to_string()}")

    section("2/5  Preparando features")
    available = [c for c in FEATURE_COLS if c in df.columns]
    missing = set(FEATURE_COLS) - set(available)
    if missing:
        print(f"  ⚠ Features faltantes: {missing}")

    X = df[available].values
    le = LabelEncoder()
    y = le.fit_transform(df[TARGET_COL])
    classes = le.classes_.tolist()
    print(f"  Features: {len(available)}  |  Clases: {classes}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )
    print(f"  Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    section("3/5  Entrenando XGBoost")
    device = detect_device()
    print(f"  Device detectado: {device}")

    model = build_model(device)
    try:
        model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False,
        )
        device_used = device
    except Exception as e:
        if device == "cuda":
            print(f"  ⚠ CUDA falló ({e}), reintentando en CPU...")
            model = build_model("cpu")
            model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                verbose=False,
            )
            device_used = "cpu"
        else:
            raise

    best_iter = model.best_iteration
    print(f"  ✓ Entrenado en {device_used}  |  Mejor iteración: {best_iter}")

    section("4/5  Evaluación")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)

    report = classification_report(y_test, y_pred,
                                   target_names=classes, output_dict=True)
    print(classification_report(y_test, y_pred, target_names=classes))

    from sklearn.preprocessing import label_binarize
    y_test_bin = label_binarize(y_test, classes=list(range(len(classes))))
    roc_aucs = {
        cls: float(roc_auc_score(y_test_bin[:, i], y_prob[:, i]))
        for i, cls in enumerate(classes)
    }
    print("  ROC AUC por clase:")
    for cls, auc in roc_aucs.items():
        print(f"    {cls}: {auc:.4f}")

    section("5/5  Figuras y guardado")
    plot_confusion_matrix(y_test, y_pred, classes)
    plot_feature_importance(model, available)
    plot_roc_curves(y_test_bin, y_prob, classes)

    with open(MODELS / "xgboost.pkl", "wb") as f:
        pickle.dump({"model": model, "label_encoder": le,
                     "features": available}, f)
    print("  ✓ xgboost.pkl")

    save_metrics(report, roc_aucs, int(best_iter), device_used)

    print(f"\n{'─' * 50}")
    print("  Clasificación completa.")
    print("  Siguiente paso: uv run python src/05_train_agent.py")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
