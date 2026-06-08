"""07_report_figures.py — Figuras finales para el informe IEEE

Genera (si no existen ya):
  - battle_duration.png     histograma duración de batallas
  - top_pokemon.png         Pokémon más frecuentes en el dataset
  - rl_learning_curve.png   curva de aprendizaje del agente
  - model_comparison.png    tabla comparativa de las 3 técnicas
"""

import json
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
MODELS = ROOT / "outputs" / "models"
METRICS_FILE = ROOT / "outputs" / "metrics.json"

FIGURES.mkdir(parents=True, exist_ok=True)

_DARK = "#1a1a2e"
_MID = "#16213e"
_ACCENT = "#e63946"
_GOLD = "#ffd700"
_BLUE = "#4cc9f0"
_GREEN = "#06d6a0"


def _dark_ax(figsize=(10, 5)):
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


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


# ── Battle duration ──────────────────────────────────────────────────────────


def plot_battle_duration(df: pd.DataFrame) -> None:
    fig, ax = _dark_ax(figsize=(10, 5))
    counts, edges = np.histogram(df["n_turns"].clip(upper=100), bins=40)
    centers = (edges[:-1] + edges[1:]) / 2
    ax.bar(centers, counts, width=edges[1] - edges[0], color=_BLUE, alpha=0.85, edgecolor="none")
    ax.axvline(df["n_turns"].median(), color=_GOLD, linestyle="--",
               label=f"Mediana: {df['n_turns'].median():.0f} turnos")
    ax.set_xlabel("Duración (turnos)")
    ax.set_ylabel("Batallas")
    ax.set_title("Distribución de duración de batallas — gen8randombattle")
    ax.legend(facecolor=_DARK, labelcolor="white")
    plt.tight_layout()
    plt.savefig(FIGURES / "battle_duration.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ battle_duration.png")


# ── Top Pokémon ──────────────────────────────────────────────────────────────


def _extract_top_pokemon(parquet_path: Path, n: int = 20) -> pd.Series:
    df_raw = pd.read_parquet(parquet_path, columns=["log"])
    counts: dict[str, int] = {}
    for log in df_raw["log"]:
        for line in log.split("\n"):
            parts = line.split("|")
            if len(parts) > 3 and parts[1] in ("switch", "drag"):
                name = parts[3].split(",")[0].strip()
                counts[name] = counts.get(name, 0) + 1
    series = pd.Series(counts).sort_values(ascending=False)
    return series.head(n)


def plot_top_pokemon(top: pd.Series) -> None:
    fig, ax = _dark_ax(figsize=(10, 7))
    colors = [_ACCENT if i == 0 else _BLUE for i in range(len(top))]
    ax.barh(range(len(top)), top.values[::-1], color=colors[::-1])
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top.index[::-1], color="white", fontsize=9)
    ax.set_xlabel("Apariciones en el dataset")
    ax.set_title(f"Top {len(top)} Pokémon más frecuentes — gen8randombattle")
    plt.tight_layout()
    plt.savefig(FIGURES / "top_pokemon.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ top_pokemon.png")


# ── RL learning curve ────────────────────────────────────────────────────────


def plot_rl_learning_curve(log_path: Path) -> None:
    with open(log_path) as f:
        log = json.load(f)

    episodes = [e["episode"] for e in log]
    win_rates = [e["win_rate"] for e in log]
    epsilons = [e["epsilon"] for e in log]

    fig, ax1 = plt.subplots(figsize=(11, 5))
    fig.patch.set_facecolor(_DARK)
    ax1.set_facecolor(_MID)
    for sp in ax1.spines.values():
        sp.set_edgecolor("#444")

    # Smooth win rate
    window = max(1, len(win_rates) // 40)
    smoothed = pd.Series(win_rates).rolling(window, center=True).mean()

    ax1.plot(episodes, win_rates, color=_ACCENT, alpha=0.2, linewidth=1)
    ax1.plot(episodes, smoothed, color=_ACCENT, linewidth=2.5, label="Win Rate (suavizado)")
    ax1.axhline(0.5, color="white", linestyle="--", alpha=0.3, label="50% baseline")
    ax1.set_xlabel("Episodio", color="white")
    ax1.set_ylabel("Win Rate (ventana 100)", color=_ACCENT)
    ax1.tick_params(colors="white")
    ax1.set_ylim(0, 1)
    ax1.title.set_color("white")
    ax1.set_title("Curva de Aprendizaje — Q-Learning vs RandomPlayer")

    ax2 = ax1.twinx()
    ax2.plot(episodes, epsilons, color=_GOLD, linewidth=1.5,
             linestyle=":", alpha=0.8, label="Epsilon")
    ax2.set_ylabel("Epsilon", color=_GOLD)
    ax2.tick_params(colors="white")
    ax2.set_facecolor(_MID)
    ax2.set_ylim(0, 1.05)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               facecolor=_DARK, labelcolor="white", loc="lower right")

    plt.tight_layout()
    plt.savefig(FIGURES / "rl_learning_curve.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ rl_learning_curve.png")


# ── Model comparison table ───────────────────────────────────────────────────


def plot_model_comparison(metrics: dict) -> None:
    clus = metrics.get("clustering", {})
    clf = metrics.get("classification", {})
    rl = metrics.get("rl", {})

    rows = [
        ["Técnica",       "K-Means",                 "XGBoost",                    "Q-Learning"],
        ["Tipo",          "Agrupación",              "Clasificación",              "Refuerzo"],
        ["Datos",         "484k equipos",            "484k batallas",              "2000 episodios"],
        ["Métrica principal",
                          f"Silhouette={clus.get('silhouettes', [0])[0]:.3f}",
                          f"Accuracy={clf.get('accuracy', 0):.1%}",
                          f"Win Rate={rl.get('final_win_rate', '—')}"],
        ["Resultado",
                          f"K={clus.get('best_k', '?')} clusters",
                          f"F1={clf.get('weighted_f1', 0):.3f}",
                          f"{rl.get('q_states', '—')} Q-states"],
        ["Device",        "CPU",
                          clf.get("device", "cpu").upper(),
                          "CPU"],
    ]

    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor(_DARK)
    ax.set_facecolor(_DARK)
    ax.axis("off")

    col_colors = [_MID] + [_MID] * (len(rows[0]) - 1)
    header_colors = [[_ACCENT if i == 0 else "#0f3460" for i in range(len(rows[0]))]]
    cell_colors = [["#16213e" if j % 2 == 0 else "#1a2744"
                    for _ in range(len(rows[0]))]
                   for j in range(len(rows) - 1)]

    table = ax.table(
        cellText=rows[1:],
        colLabels=rows[0],
        cellLoc="center",
        loc="center",
        cellColours=cell_colors,
        colColours=["#0f3460"] * len(rows[0]),
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#0f3460")
        cell.set_text_props(color="white")

    ax.set_title("Comparativa de las 3 Técnicas de ML", color="white",
                 fontsize=12, pad=10)
    plt.tight_layout()
    plt.savefig(FIGURES / "model_comparison.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ model_comparison.png")


# ── Main ─────────────────────────────────────────────────────────────────────


def main() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║    Pokémon Showdown — Figuras para informe       ║")
    print("╚══════════════════════════════════════════════════╝")

    metrics = {}
    if METRICS_FILE.exists():
        with open(METRICS_FILE) as f:
            metrics = json.load(f)

    section("1/4  Duración de batallas")
    df = pd.read_parquet(PROCESSED / "battles_featured.parquet")
    plot_battle_duration(df)
    print(f"  n_turns: mediana={df['n_turns'].median():.0f}, "
          f"media={df['n_turns'].mean():.1f}, p95={df['n_turns'].quantile(.95):.0f}")

    section("2/4  Top Pokémon")
    raw_parquet = ROOT / "data" / "raw" / "gen8rb.parquet"
    top = _extract_top_pokemon(raw_parquet, n=20)
    plot_top_pokemon(top)
    print(f"  Top 3: {', '.join(top.head(3).index.tolist())}")

    section("3/4  Curva de aprendizaje RL")
    log_path = MODELS / "training_log.json"
    if log_path.exists():
        plot_rl_learning_curve(log_path)

        with open(log_path) as f:
            log = json.load(f)
        last_100 = [e["win_rate"] for e in log[-100:]]
        final_wr = sum(last_100) / len(last_100)
        q_states = log[-1].get("q_states", 0)

        metrics.setdefault("rl", {})
        metrics["rl"]["final_win_rate"] = f"{final_wr:.1%}"
        metrics["rl"]["q_states"] = q_states
        with open(METRICS_FILE, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"  Win rate final: {final_wr:.1%} | Q-states: {q_states:,}")
    else:
        print("  ⚠ training_log.json no encontrado — correr 05_train_agent.py primero")

    section("4/4  Tabla comparativa")
    plot_model_comparison(metrics)

    print(f"\n{'─' * 50}")
    print("  Figuras completas.")
    print(f"  Archivos en: {FIGURES}")
    existing = sorted(FIGURES.glob("*.png"))
    for f in existing:
        size_kb = f.stat().st_size / 1024
        print(f"    {f.name:<35} {size_kb:.0f} KB")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
