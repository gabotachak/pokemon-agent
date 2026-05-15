# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Requisitos del trabajo (Aprendizaje Maquinal — Proyecto 3)

- **Entrega:** 2 junio 2026, 23:59
- **Dataset:** mínimo 100,000 registros → 107,585 batallas gen1randombattle reales (HolidayOugi/pokemon-showdown-replays) ✅
- **Técnicas:** 3 distintas (agrupación, clasificación o refuerzo) → K-Means + XGBoost + Q-Learning ✅
- **Informe:** formato IEEE doble columna, **máximo 6 páginas**
- **Video:** máximo 6 minutos, **todos los integrantes deben aparecer** en cámara

### Gap conceptual a justificar en el informe

El enunciado pide "obtener conocimiento de dicha base de datos" con las 3 técnicas. K-Means y XGBoost usan el dataset directamente. El agente RL entrena contra `RandomPlayer` vía `poke-env`, no consume el dataset en entrenamiento. **Justificación:** el diseño del espacio de estados (variables discretas, rangos de HP) y la función de reward están informados por el análisis previo del dataset (features discriminantes según XGBoost, arquetipos según K-Means).

## Estilo de desarrollo

Todo script de larga duración debe mostrar progreso claro: barras `tqdm` para loops, output streameado (no silenciado) para subprocesos lentos (git, npm, uv), checkmarks `✓` al completar cada paso, y banners de sección con `─` separadores. Nunca dejar al usuario mirando una terminal en silencio.

## Commands

```bash
# Setup (once) — clones showdown/ and installs all deps
uv run python src/00_setup.py
uv run python src/01_download.py
uv run python src/02_preprocess.py

# ML pipeline (on processed data)
uv run python src/03_clustering.py
uv run python src/04_classification.py

# Training (3 terminals required)
cd showdown && node pokemon-showdown start --no-security  # Terminal A
uv run python src/06_dashboard.py                         # Terminal B
uv run python src/05_train_agent.py                       # Terminal C (after A and B)

# Post-training
uv run python src/07_report_figures.py
```

Dependency management: `uv` only — no pip, no poetry. Python 3.13+ required.

## Environment variables

Copy `.env.example` to `.env` and fill in:

```
HF_TOKEN=hf_...   # https://huggingface.co/settings/tokens (Read role)
```

`.env` is gitignored. All scripts load it automatically via `python-dotenv`.

## Implementation status

`showdown/` is downloaded by `00_setup.py` (git clone of smogon/pokemon-showdown) — it is not committed to this repo.

- [x] `src/00_setup.py` — instala deps, clona Showdown, crea carpetas
- [x] `src/01_download.py` — descarga `gen1rb.parquet` y `pokemon_stats.csv`
- [ ] `src/02_preprocess.py` — feature engineering → `battles_featured.parquet`
- [ ] `src/03_clustering.py` — K-Means arquetipos de equipo
- [ ] `src/04_classification.py` — XGBoost predicción de acción ganadora
- [ ] `src/05_train_agent.py` — Q-Learning agent (QLearningPlayer + entrenamiento)
- [ ] `src/06_dashboard.py` — FastAPI dashboard en tiempo real
- [ ] `src/07_report_figures.py` — figuras finales para el informe
- [ ] `report/ieee_report.md` — informe IEEE doble columna (máx 6 páginas)

## Architecture

Scripts run sequentially; each assumes the previous step completed.

```
Pokemon Showdown server (port 8000, Node.js)
    ↕ websocket
poke-env (Python)
    ↓
QLearningPlayer (src/05_train_agent.py)
    ↓
FastAPI dashboard (src/06_dashboard.py, port 9000)
```

**Data flow:**
- `data/raw/gen1rb.parquet` + `data/raw/pokemon_stats.csv` → `src/02_preprocess.py` → `data/processed/battles_featured.parquet`
- `data/processed/` → `src/03_clustering.py` / `src/04_classification.py` → `outputs/models/`
- Training checkpoints → POST `http://localhost:9000/update` (silently ignored if dashboard not running)

## Key design decisions

**`random_state=42` everywhere** — all models, splits, and random operations.

**Q-table state (8 discrete variables):** `hp_self` and `hp_opp` in 4 HP buckets (0–25%, 25–50%, 50–75%, 75–100%), `type_advantage` (-1/0/1), `can_outspeed` bool, `team_size_self` (1–6), `team_size_opp` (1–6), `n_available_moves` (1–4), `has_switch` bool. Intentionally small for tabular RL viability — document in report as interpretability vs scalability tradeoff.

**Action space (fixed size 9):** slots 0–3 = moves, slots 4–8 = switches. Invalid actions fall back to first available move / random move.

**Reward shaping:** +1.5 damage dealt, -1.0 damage taken without dealing, +0.5 switch into type advantage, -0.3 unnecessary switch, ±10 win/loss.

**Hyperparameters:** lr=0.1, gamma=0.9, epsilon 1.0→0.05 over 1500 of 2000 episodes.

## Preprocessing spec (`src/02_preprocess.py`)

Input: `data/raw/gen1rb.parquet` (gen1randombattle already filtered), `data/raw/pokemon_stats.csv`.

Extract per battle from the `log` field:
- `team_p1`, `team_p2`: list of up to 6 Pokémon per team
- `winner`: 0 (p1) or 1 (p2)
- `n_turns`: battle duration in turns
- `moves_used_p1/p2`, `switches_p1/p2`

Join with pokemon_stats to compute per-team averages: `avg_hp`, `avg_attack`, `avg_defense`, `avg_sp_attack`, `avg_sp_defense`, `avg_speed`. Also compute: `type_diversity` (unique types in team), `n_fast_pokemon` (speed > 100).

Derived features: `stat_total_diff` (p1–p2 avg stat totals), `speed_advantage_ratio`, `type_coverage` (types team covers offensively), `switch_rate` (switches/n_turns), `winning_action_type` (target variable for classifier — categories: `physical`, `special`, `status`, `switch`).

Output: `data/processed/battles_featured.parquet`.

## Clustering spec (`src/03_clustering.py`)

Team vectors (duplicate rows per battle): `avg_hp`, `avg_attack`, `avg_defense`, `avg_sp_attack`, `avg_sp_defense`, `avg_speed`, `type_diversity`, `n_fast_pokemon`, `type_coverage`. StandardScaler → PCA(2) → K-Means elbow K=2..10. Figures: `elbow_curve.png`, `clusters_pca.png`, `clusters_radar.png`. Save `outputs/models/kmeans.pkl` and clustering metrics to `outputs/metrics.json`.

## Classification spec (`src/04_classification.py`)

Target: `winning_action_type` (4 classes). Features: team stats + derived features. 80/20 stratified split. XGBClassifier with `early_stopping_rounds=20`, `eval_metric='mlogloss'`. Figures: `confusion_matrix.png`, `feature_importance.png`, `roc_curves.png`. Save `outputs/models/xgboost.pkl` and metrics to `outputs/metrics.json`.

## Dashboard spec (`src/06_dashboard.py`)

FastAPI with HTML served inline. Endpoints: `GET /` (dashboard HTML), `GET /metrics` (JSON list of checkpoints), `POST /update` (append checkpoint to in-memory list). UI: Chart.js from CDN, dark background `#1a1a2e`, win rate line in `#e63946`, reward line in `#ffd700`, auto-refresh every 2s, last 10 battles table.

## Outputs

- `outputs/models/`: `kmeans.pkl`, `xgboost.pkl`, `qtable.pkl`, `training_log.json`
- `outputs/figures/`: elbow curve, PCA clusters, radar chart, confusion matrix, feature importance, ROC curves, battle duration, top Pokémon, RL learning curve, model comparison table
- `outputs/metrics.json`: unified metrics for all three techniques
- `report/ieee_report.md`: IEEE double-column format, populated from `metrics.json`

## Ports

- `8000` — Pokémon Showdown (live battles in browser)
- `9000` — FastAPI dashboard (training metrics)
