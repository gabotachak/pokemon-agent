# AGENTS.md

Guidance for AI agents working in this repository. See CLAUDE.md for full implementation specs, architecture, and design decisions.

## Quick commands

```bash
make pipeline          # preprocess → cluster → classify → figures → report → pdf
make setup             # 00_setup.py
make download          # 01_download.py
make train             # prints 3-terminal instructions for RL training
make pdf               # typst compile → report/ieee_report.pdf
```

## Key constraints

- `uv` only — no pip, no poetry. Python 3.13+.
- `random_state=42` everywhere.
- GPU fallback: try `device='cuda'`, auto-retry with `device='cpu'` on failure.
- Scripts must show progress (tqdm, ✓ checkmarks, section banners).
- Dashboard at port 9000 is optional — training continues if it's not running.

## Video presentation structure (6 min max)

| Time | Content |
|------|---------|
| 0:00–1:00 | Intro: qué es Pokémon Showdown, motivación del proyecto |
| 1:00–2:00 | Dataset y preprocesamiento — 484,130 batallas reales |
| 2:00–3:00 | Clustering K-Means — radar chart y arquetipos |
| 3:00–4:00 | Clasificación XGBoost — feature importance y confusion matrix |
| 4:00–5:30 | Agente jugando en vivo: pantalla dividida Showdown + dashboard |
| 5:30–6:00 | Conclusiones y cadena metodológica |

All team members must appear on camera.
