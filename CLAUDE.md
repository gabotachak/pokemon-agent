# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup (once)
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

Dependency management: `uv` only — no pip, no poetry.

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
- `data/raw/` → `src/02_preprocess.py` → `data/processed/battles_featured.parquet`
- `data/processed/` → `src/03_clustering.py` / `src/04_classification.py` → `outputs/models/`
- Training checkpoints → POST `http://localhost:9000/update` (silently ignored if dashboard not running)

## Key design decisions

**Q-table state (8 discrete variables):** HP ranges (4 buckets), type advantage (-1/0/1), outspeed bool, team sizes, move count, has-switch bool. Intentionally small for tabular RL viability — document in report as interpretability vs scalability tradeoff.

**Action space (fixed size 9):** slots 0–3 = moves, slots 4–8 = switches. Invalid actions fall back to first available move / random move.

**Reward shaping:** +1.5 damage dealt, -1.0 damage taken without dealing, ±0.5 for switch quality, ±10 win/loss.

**Hyperparameters:** lr=0.1, gamma=0.9, epsilon 1.0→0.05 over 1500 of 2000 episodes, `random_state=42` everywhere.

**Dataset cap:** If PokeChamp exceeds RAM, sample 300k Gen 1 battles (still meets 100k requirement). Filtered to `gen1randombattle` format only.

## Outputs

- `outputs/models/`: `kmeans.pkl`, `xgboost.pkl`, `qtable.pkl`, `training_log.json`
- `outputs/figures/`: elbow curve, PCA clusters, radar chart, confusion matrix, feature importance, ROC curves, battle duration, top Pokémon, RL learning curve, model comparison table
- `outputs/metrics.json`: unified metrics for all three techniques
- `report/ieee_report.md`: IEEE double-column format, populated from `metrics.json`

## Ports

- `8000` — Pokémon Showdown (live battles in browser)
- `9000` — FastAPI dashboard (training metrics)
