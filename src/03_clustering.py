"""03_clustering.py — K-Means arquetipos de equipo → elbow, PCA plot, radar chart"""

import json
import pickle
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from tqdm import tqdm
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

# Estilo global de figuras: fuentes grandes para legibilidad en PDF doble columna
plt.rcParams.update({
    "font.size": 17,
    "axes.titlesize": 19,
    "axes.titleweight": "bold",
    "axes.labelsize": 17,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15,
    "legend.fontsize": 15,
})

ROOT = Path(__file__).parent.parent
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "outputs" / "figures"
MODELS = ROOT / "outputs" / "models"
METRICS_FILE = ROOT / "outputs" / "metrics.json"

FIGURES.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)

TEAM_FEATURES = [
    "avg_hp", "avg_attack", "avg_defense",
    "avg_sp_attack", "avg_sp_defense", "avg_speed",
    "type_diversity", "n_fast_pokemon", "type_coverage",
]

K_RANGE = range(2, 11)
RANDOM_STATE = 42


# ── Data preparation ────────────────────────────────────────────────────────


def build_team_vectors(df: pd.DataFrame) -> pd.DataFrame:
    """Expand battles to one row per team (2 rows per battle)."""
    p1 = df[[f"{f}_p1" for f in TEAM_FEATURES]].copy()
    p1.columns = TEAM_FEATURES
    p1["side"] = "p1"

    p2 = df[[f"{f}_p2" for f in TEAM_FEATURES]].copy()
    p2.columns = TEAM_FEATURES
    p2["side"] = "p2"

    return pd.concat([p1, p2], ignore_index=True)


# ── Elbow curve ─────────────────────────────────────────────────────────────


def compute_elbow(X_scaled: np.ndarray) -> tuple[list, list, int]:
    inertias, silhouettes = [], []
    for k in tqdm(K_RANGE, desc="  K-Means elbow", unit=" k"):
        km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(X_scaled, labels, sample_size=10_000,
                                            random_state=RANDOM_STATE))

    # Best K by silhouette
    best_k = list(K_RANGE)[int(np.argmax(silhouettes))]
    return inertias, silhouettes, best_k


def plot_elbow(inertias: list, silhouettes: list, best_k: int) -> None:
    ks = list(K_RANGE)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    fig.patch.set_facecolor("#1a1a2e")
    for ax in (ax1, ax2):
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#444")

    ax1.plot(ks, inertias, "o-", color="#e63946", linewidth=2, markersize=6)
    ax1.axvline(best_k, color="#ffd700", linestyle="--", alpha=0.7)
    ax1.set_xlabel("K")
    ax1.set_ylabel("Inercia")
    ax1.set_title("Curva del Codo")
    ax1.set_xticks(ks)

    ax2.plot(ks, silhouettes, "o-", color="#4cc9f0", linewidth=2, markersize=6)
    ax2.axvline(best_k, color="#ffd700", linestyle="--", alpha=0.7,
                label=f"Mejor K={best_k}")
    ax2.set_xlabel("K")
    ax2.set_ylabel("Coef. de silueta")
    ax2.set_title("Silueta por K")
    ax2.set_xticks(ks)
    ax2.legend(facecolor="#1a1a2e", labelcolor="white")

    plt.tight_layout()
    plt.savefig(FIGURES / "elbow_curve.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print(f"  ✓ elbow_curve.png  (mejor K={best_k})")


# ── PCA scatter ─────────────────────────────────────────────────────────────


CLUSTER_COLORS = [
    "#e63946", "#ffd700", "#4cc9f0", "#06d6a0", "#ff9f1c",
    "#c77dff", "#ff6b6b", "#48cae4", "#80b918",
]


def plot_pca_clusters(X_pca: np.ndarray, labels: np.ndarray, best_k: int,
                      explained: np.ndarray) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")
    ax.tick_params(colors="white")
    ax.xaxis.label.set_color("white")
    ax.yaxis.label.set_color("white")
    ax.title.set_color("white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")

    for k in range(best_k):
        mask = labels == k
        ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
                   c=CLUSTER_COLORS[k % len(CLUSTER_COLORS)],
                   alpha=0.3, s=4, label=f"Grupo {k}")
        cx, cy = X_pca[mask, 0].mean(), X_pca[mask, 1].mean()
        ax.text(cx, cy, str(k), fontsize=20, fontweight="bold",
                color="white", ha="center", va="center",
                path_effects=[pe.withStroke(linewidth=3, foreground="black")])

    ax.set_xlabel(f"PC1 ({explained[0]:.1%} varianza)")
    ax.set_ylabel(f"PC2 ({explained[1]:.1%} varianza)")
    ax.set_title(f"Arquetipos de equipo — K-Means K={best_k} (PCA 2D)")
    ax.legend(facecolor="#1a1a2e", labelcolor="white", markerscale=3)

    plt.tight_layout()
    plt.savefig(FIGURES / "clusters_pca.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ clusters_pca.png")


# ── Radar chart ─────────────────────────────────────────────────────────────


def plot_radar(centroids_original: np.ndarray, best_k: int) -> None:
    labels_short = ["HP", "Atk", "Def", "SpA", "SpD", "Spe",
                    "TypeDiv", "FastPoke", "TypeCov"]
    n = len(labels_short)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"polar": True})
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")
    ax.tick_params(colors="white")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels_short, color="white", size=15)
    ax.set_yticklabels([], color="white")
    ax.spines["polar"].set_color("#444")
    ax.grid(color="#333", linewidth=0.8)
    ax.set_title("Radar de arquetipos (centroides normalizados)",
                 color="white", pad=20, size=17, fontweight="bold")

    # Normalize centroids to 0-1 range for radar
    mins = centroids_original.min(axis=0)
    maxs = centroids_original.max(axis=0)
    rng = np.where(maxs - mins == 0, 1, maxs - mins)
    normalized = (centroids_original - mins) / rng

    for k in range(best_k):
        vals = normalized[k].tolist() + normalized[k][:1].tolist()
        color = CLUSTER_COLORS[k % len(CLUSTER_COLORS)]
        ax.plot(angles, vals, "o-", linewidth=2, color=color, label=f"Grupo {k}")
        ax.fill(angles, vals, alpha=0.1, color=color)

    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1),
              facecolor="#1a1a2e", labelcolor="white")

    plt.tight_layout()
    plt.savefig(FIGURES / "clusters_radar.png", dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    print("  ✓ clusters_radar.png")


# ── Metrics persistence ─────────────────────────────────────────────────────


def save_metrics(best_k: int, inertias: list, silhouettes: list,
                 explained: np.ndarray, cluster_sizes: list) -> None:
    existing = {}
    if METRICS_FILE.exists():
        with open(METRICS_FILE) as f:
            existing = json.load(f)
    existing["clustering"] = {
        "best_k": best_k,
        "inertias": inertias,
        "silhouettes": silhouettes,
        "pca_explained_variance": explained.tolist(),
        "cluster_sizes": cluster_sizes,
    }
    with open(METRICS_FILE, "w") as f:
        json.dump(existing, f, indent=2)
    print(f"  ✓ metrics.json actualizado")


# ── Main ────────────────────────────────────────────────────────────────────


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def main() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║    Pokémon Showdown — Clustering K-Means         ║")
    print("╚══════════════════════════════════════════════════╝")

    section("1/5  Cargando datos")
    df = pd.read_parquet(PROCESSED / "battles_featured.parquet")
    print(f"  ✓ {len(df):,} batallas")

    section("2/5  Construyendo vectores de equipo")
    teams = build_team_vectors(df)
    print(f"  ✓ {len(teams):,} vectores (2 por batalla)")

    X = teams[TEAM_FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2, random_state=RANDOM_STATE)
    X_pca = pca.fit_transform(X_scaled)
    explained = pca.explained_variance_ratio_
    print(f"  PCA varianza explicada: PC1={explained[0]:.1%}  PC2={explained[1]:.1%}")

    section("3/5  Elbow K=2..10")
    inertias, silhouettes, best_k = compute_elbow(X_scaled)
    print(f"  Mejor K por silhouette: {best_k}")
    plot_elbow(inertias, silhouettes, best_k)

    section("4/5  Modelo final K={best_k}")
    km_final = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10)
    labels = km_final.fit_predict(X_scaled)

    cluster_sizes = [int((labels == k).sum()) for k in range(best_k)]
    print("  Tamaño de clusters:")
    for k, sz in enumerate(cluster_sizes):
        print(f"    Cluster {k}: {sz:,} equipos ({sz/len(labels):.1%})")

    # Back-transform centroids to original scale for radar
    centroids_original = scaler.inverse_transform(km_final.cluster_centers_)

    section("5/5  Figuras y guardado")
    plot_pca_clusters(X_pca, labels, best_k, explained)
    plot_radar(centroids_original, best_k)

    with open(MODELS / "kmeans.pkl", "wb") as f:
        pickle.dump({"model": km_final, "scaler": scaler, "pca": pca,
                     "features": TEAM_FEATURES}, f)
    print("  ✓ kmeans.pkl")

    save_metrics(best_k, inertias, silhouettes, explained, cluster_sizes)

    print(f"\n{'─' * 50}")
    print("  Clustering completo.")
    print("  Siguiente paso: uv run python src/04_classification.py")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
