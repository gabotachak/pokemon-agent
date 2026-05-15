# GEMINI.md

This file provides guidance to Gemini CLI when working with code in this repository.

## Requisitos del trabajo (Aprendizaje Maquinal — Proyecto 3)

- **Entrega:** 2 junio 2026, 23:59
- **Dataset:** mínimo 100,000 registros → 107,585 batallas gen1randombattle reales (HolidayOugi/pokemon-showdown-replays) ✅
- **Técnicas:** 3 distintas (agrupación, clasificación o refuerzo) → K-Means + XGBoost + Q-Learning ✅
- **Informe:** formato IEEE doble columna, **máximo 6 páginas**
- **Video:** máximo 6 minutos, **todos los integrantes deben aparecer** en cámara
- **Comprensión:** el equipo debe entender el desarrollo (no solo copy-paste de IA)

### Gap conceptual a justificar en el informe

El enunciado pide "obtener conocimiento de dicha base de datos" con las 3 técnicas. K-Means y XGBoost usan PokeChamp directamente. El agente RL entrena contra `RandomPlayer` vía `poke-env`, no consume el dataset en entrenamiento. **Justificación a incluir en el informe:** el diseño del espacio de estados (variables discretas, rangos de HP) y la función de reward están informados por el análisis previo del dataset (qué features discriminan victorias según XGBoost, qué arquetipos de equipo emergen según K-Means).

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

## Estilo de desarrollo

Todo script de larga duración debe mostrar progreso claro: barras `tqdm` para loops, output streameado (no silenciado) para subprocesos lentos (git, npm, uv), checkmarks `✓` al completar cada paso, y banners de sección con `─` separadores. Nunca dejar al usuario mirando una terminal en silencio.

## Environment variables

Copy `.env.example` to `.env` and fill in:

```
HF_TOKEN=hf_...   # https://huggingface.co/settings/tokens (Read role)
```

`.env` is gitignored. All scripts load it automatically via `python-dotenv`.

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

**Dataset:** HolidayOugi/pokemon-showdown-replays, filtrado a `gen1randombattle` al descargar → `data/raw/gen1rb.parquet` (~107k batallas humanas reales). No bajar dataset completo (66.8 GB).

## Outputs

- `outputs/models/`: `kmeans.pkl`, `xgboost.pkl`, `qtable.pkl`, `training_log.json`
- `outputs/figures/`: elbow curve, PCA clusters, radar chart, confusion matrix, feature importance, ROC curves, battle duration, top Pokémon, RL learning curve, model comparison table
- `outputs/metrics.json`: unified metrics for all three techniques
- `report/ieee_report.md`: IEEE double-column format, populated from `metrics.json`

## Ports

- `8000` — Pokémon Showdown (live battles in browser)
- `9000` — FastAPI dashboard (training metrics)
