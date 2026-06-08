# Pokémon Showdown RL — Sistemas Inteligentes

## Objetivo

Entrenar un agente de Q-Learning para ganar combates con equipo completo de 6
Pokémon en Pokémon Showdown (Gen 8 Random Battle), con visualización en vivo
del combate en el browser y dashboard de entrenamiento en tiempo real.

El proyecto combina tres técnicas de ML:
1. **Clustering** — descubrir arquetipos de equipo en batallas históricas
2. **Clasificación** — predecir acción ganadora dado el estado del combate
3. **Aprendizaje por Refuerzo** — agente Q-Learning que juega con equipo completo

---

## Fases del proyecto

### Fase MVP (obligatoria)
Agente Q-Learning tabular que juega Gen 8 Random Battle con equipo de 6.
Acciones: elegir movimiento O hacer switch. Oponente: RandomPlayer.

### Fase Ambiciosa (extensión futura, no bloquea entrega)
- Reemplazar Q-Learning tabular por DQN (red neuronal)
- Oponente: MaxDamagePlayer o agente entrenado previamente
- Agregar predicción de equipo rival basada en Pokémon vistos

---

## Arquitectura general

```
Pokémon Showdown (servidor local, puerto 8000)
        ↑↓  websocket
    poke-env (Python)
        ↓
  QLearningPlayer
  - estado: HP ratios, tipo en campo, ventaja de tipo, switches disponibles
  - acciones: 4 movimientos + hasta 5 switches = hasta 9 acciones
  - reward: daño infligido, daño recibido, victoria, derrota
        ↓
  Dashboard (FastAPI, puerto 9000)
  - win rate en tiempo real
  - reward promedio por episodio
  - epsilon actual
  - tabla de últimas 10 batallas
```

Para ver el combate en vivo: abrir `http://localhost:8000` en el browser.
Para ver el dashboard: abrir `http://localhost:9000` en el browser.

---

## Datasets

### Principal — Pokémon Showdown Replays (HuggingFace)
- **URL:** https://huggingface.co/datasets/HolidayOugi/pokemon-showdown-replays
- **Tamaño:** 31.7M batallas totales, **gen8randombattle** de jugadores humanos reales
- **Filtro a aplicar:** `formatid == 'gen8randombattle'` al descargar — no bajar el dataset completo (66.8 GB)
- **Schema:** `id`, `format`, `players`, `log`, `uploadtime`, `views`, `formatid`, `rating`
- **Uso:** clustering (técnica 1) y clasificación (técnica 2)

### Secundario — Pokémon Stats (PokeAPI)
- **URL:** https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/pokemon_stats.csv
- **Uso:** enriquecer features con stats base de cada Pokémon

---

## Estilo de desarrollo

Todo script de larga duración debe mostrar progreso claro: barras `tqdm` para loops, output streameado (no silenciado) para subprocesos lentos (git, npm, uv), checkmarks `✓` al completar cada paso, y banners de sección con `─` separadores. Nunca dejar al usuario mirando una terminal en silencio.

## Variables de entorno

Copiar `.env.example` a `.env` y completar:

```
HF_TOKEN=hf_...   # https://huggingface.co/settings/tokens (Read role)
```

`.env` está en `.gitignore`. Todos los scripts lo cargan con `python-dotenv`.

## Stack tecnológico

- Python 3.11+
- `uv` para gestión de dependencias (NO pip ni poetry)
- `poke-env` — interfaz Python para Pokémon Showdown
- `Node.js` — para correr el servidor local de Pokémon Showdown
- pandas, numpy, scikit-learn, xgboost
- FastAPI + uvicorn — dashboard web
- matplotlib, seaborn — figuras para el informe

---

## Estructura de archivos

```
project/
├── AGENTS.md
├── pyproject.toml
├── showdown/                   # servidor Showdown clonado aquí
├── data/
│   ├── raw/
│   │   ├── gen8rb.parquet
│   │   └── pokemon_stats.csv
│   └── processed/
│       ├── battles.parquet
│       └── battles_featured.parquet
├── src/
│   ├── 00_setup.py
│   ├── 01_download.py
│   ├── 02_preprocess.py
│   ├── 03_clustering.py
│   ├── 04_classification.py
│   ├── 05_train_agent.py
│   ├── 06_dashboard.py
│   └── 07_report_figures.py
├── outputs/
│   ├── figures/
│   ├── models/
│   └── metrics.json
└── report/
    └── ieee_report.md
```

---

## Tareas — ejecutar en orden

---

### 0. Setup (`src/00_setup.py`)

**Dependencias Python:**
- Inicializar con `uv init` si no existe `pyproject.toml`
- `uv add poke-env pandas numpy scikit-learn xgboost`
- `uv add fastapi uvicorn websockets huggingface_hub datasets pyarrow`

**Servidor Pokémon Showdown:**
- Verificar que Node.js está instalado. Si no: imprimir instrucciones
  para instalar desde https://nodejs.org y detener ejecución.
- Si la carpeta `showdown/` no existe:
  `git clone https://github.com/smogon/pokemon-showdown.git showdown`
- `cd showdown && npm install`
- Copiar config: `cp showdown/config/config-example.js showdown/config/config.js`
- Aplicar estos cambios en `showdown/config/config.js`:
  - `exports.workers = 1;`
  - `exports.noguestsecurity = true;`
- Crear carpetas: `outputs/figures/`, `outputs/models/`, `report/`
- Imprimir al final:
  ```
  Setup completo. Para continuar:
  1. Terminal A: cd showdown && node pokemon-showdown start --no-security
  2. Terminal B: uv run python src/06_dashboard.py
  3. Browser:    http://localhost:8000  (combates en vivo)
                 http://localhost:9000  (dashboard)
  ```

---

### 1. Descarga de datos (`src/01_download.py`)

- Descargar solo las filas `gen8randombattle` de HolidayOugi/pokemon-showdown-replays
  usando `datasets` con filtro — NO `snapshot_download` (evita bajar 66 GB)
  → `data/raw/gen8rb.parquet`
- Descargar pokemon_stats.csv con requests
  → `data/raw/pokemon_stats.csv`
- Imprimir: número de batallas descargadas, tamaño en disco, primeras filas

---

### 2. Preprocesamiento (`src/02_preprocess.py`)

**Cargar y filtrar:**
- Cargar `data/raw/gen8rb.parquet` — ya filtrado a gen8randombattle (~107k batallas)
- No se requiere filtro adicional por formato

**Extraer por batalla:**
- `team_p1`, `team_p2`: lista de hasta 6 Pokémon por equipo
- `winner`: 0 (p1) o 1 (p2)
- `n_turns`: duración en turnos
- `moves_used_p1`, `moves_used_p2`: todos los movimientos usados
- `switches_p1`, `switches_p2`: número de switches realizados

**Unir con pokemon_stats:**
- Para cada Pokémon del equipo calcular stats promedio del equipo:
  `avg_hp`, `avg_attack`, `avg_defense`, `avg_sp_attack`, `avg_sp_defense`,
  `avg_speed`
- `type_diversity`: número de tipos únicos en el equipo
- `n_fast_pokemon`: Pokémon con speed > 100 en el equipo

**Feature engineering:**
- `stat_total_diff`: diferencia de stat total promedio entre equipos (p1 - p2)
- `speed_advantage_ratio`: fracción de Pokémon de p1 más rápidos que los de p2
- `type_coverage`: número de tipos que el equipo puede cubrir ofensivamente
- `switch_rate`: switches / n_turns (agresividad táctica)
- `winning_action_type`: tipo de acción que resultó en más daño en la batalla
  ganadora — categorías: `physical`, `special`, `status`, `switch`
  (variable objetivo para clasificación)

- Guardar → `data/processed/battles_featured.parquet`
- Imprimir estadísticas descriptivas del dataset final

---

### 3. Clustering — Arquetipos de equipo (`src/03_clustering.py`)

**Objetivo:** Descubrir qué estilos de equipo emergen naturalmente en Gen 8
(ej: equipos rápidos y ofensivos, equipos lentos y defensivos, equipos mixtos)

**Proceso:**
- Cargar `data/processed/battles_featured.parquet`
- Construir un vector por equipo (no por batalla — duplicar filas):
  `avg_hp`, `avg_attack`, `avg_defense`, `avg_sp_attack`, `avg_sp_defense`,
  `avg_speed`, `type_diversity`, `n_fast_pokemon`, `type_coverage`
- StandardScaler
- PCA a 2 componentes para visualización
- Método del codo K=2..10 → `outputs/figures/elbow_curve.png`
- K-Means con K óptimo (`random_state=42`)
- Figura clusters en espacio PCA → `outputs/figures/clusters_pca.png`
- Radar chart de stats promedio por cluster → `outputs/figures/clusters_radar.png`
- Imprimir e interpretar cada cluster con etiqueta propuesta
  (ej: "Cluster 2 → Equipo ofensivo: alto ataque y velocidad, baja defensa")
- Silhouette score e inercia
- Guardar modelo → `outputs/models/kmeans.pkl`
- Guardar métricas → `outputs/metrics.json`:
  ```json
  { "clustering": { "k": 0, "silhouette_score": 0.0, "inertia": 0.0 } }
  ```

---

### 4. Clasificación — Predicción de acción ganadora (`src/04_classification.py`)

**Objetivo:** Dado el contexto de una batalla, predecir qué tipo de acción
(físico, especial, status, switch) resulta más frecuentemente en victoria

**Proceso:**
- Variable objetivo: `winning_action_type` (4 clases)
- Features: stats promedio de ambos equipos, `stat_total_diff`,
  `speed_advantage_ratio`, `type_coverage`, `switch_rate`, `n_turns`
- Split 80/20 estratificado (`random_state=42`)
- XGBClassifier con `early_stopping_rounds=20`, `eval_metric='mlogloss'`
- Métricas: accuracy, F1 macro, AUC-ROC (one-vs-rest)
- Figuras:
  - Matriz de confusión → `outputs/figures/confusion_matrix.png`
  - Feature importance (top 15) → `outputs/figures/feature_importance.png`
  - Curvas ROC por clase → `outputs/figures/roc_curves.png`
- Guardar modelo → `outputs/models/xgboost.pkl`
- Agregar métricas → `outputs/metrics.json`:
  ```json
  { "classification": { "accuracy": 0.0, "f1_macro": 0.0, "auc_roc_macro": 0.0 } }
  ```

---

### 5. Agente RL con poke-env (`src/05_train_agent.py`)

**Objetivo:** Agente Q-Learning que juega Gen 8 Random Battle con equipo
completo de 6 Pokémon, eligiendo entre movimientos y switches cada turno.

#### 5.1 Clase `QLearningPlayer(poke_env.player.Player)`

**Estado (tuple hashable — mantener pequeño para Q-table tabular):**
- `hp_self`: HP del Pokémon activo propio en 4 rangos (0=crítico, 1=bajo,
  2=medio, 3=alto) — umbrales: 0-25%, 25-50%, 50-75%, 75-100%
- `hp_opp`: HP del Pokémon activo rival en 4 rangos (mismos umbrales)
- `type_advantage`: ventaja de tipo del activo propio vs rival (-1, 0, 1)
- `can_outspeed`: booleano — el activo propio es más rápido que el rival
- `team_size_self`: Pokémon propios aún en pie (1..6)
- `team_size_opp`: Pokémon rivales aún en pie — estimado por Pokémon vistos (1..6)
- `n_available_moves`: movimientos disponibles (1..4)
- `has_switch`: booleano — hay al menos un Pokémon disponible para switch

**Espacio de acciones (discreto, tamaño fijo 9):**
- Acciones 0..3: usar movimiento en slot 0..3 (si no disponible, usar el primero)
- Acciones 4..8: hacer switch al Pokémon en slot 0..4 del banco
  (si no disponible o ya está activo, elegir movimiento aleatorio)
- poke-env llama a `choose_move()` — implementar lógica de mapeo ahí

**Reward por turno:**
- `+1.5` si el Pokémon rival pierde HP este turno
- `-1.0` si el Pokémon propio pierde HP sin infligir daño
- `+0.5` si se hace un switch después del que entra tiene ventaja de tipo
- `-0.3` si se hace switch innecesario (sin ventaja de tipo obvia)
- `+10` al ganar la batalla
- `-10` al perder la batalla

**Hiperparámetros Q-Learning:**
- `learning_rate = 0.1`
- `gamma = 0.9`
- `epsilon_start = 1.0`
- `epsilon_end = 0.05`
- `epsilon_decay_episodes = 1500` (de 2000 totales)
- Q-table: `collections.defaultdict(lambda: np.zeros(9))`

#### 5.2 Oponente

`poke_env.player.RandomPlayer` — elige acciones al azar. Simple, suficiente
para demostrar aprendizaje claro en la curva de win rate.

#### 5.3 Entrenamiento

- 2000 episodios en total
- Cada 100 episodios calcular y guardar:
  - `winrate_last_100`: win rate de los últimos 100 episodios
  - `avg_reward_last_100`: reward promedio de los últimos 100
  - `epsilon`: valor actual
  - `episode`: número de episodio
- Imprimir checkpoint en consola
- POST a `http://localhost:9000/update` con el checkpoint (ignorar si falla)
- Al terminar:
  - Guardar Q-table → `outputs/models/qtable.pkl`
  - Guardar lista de checkpoints → `outputs/models/training_log.json`
  - Agregar a `outputs/metrics.json`:
    ```json
    { "reinforcement": {
        "final_winrate": 0.0,
        "avg_reward_last_100": 0.0,
        "total_episodes": 2000,
        "qtable_states_visited": 0
      }
    }
    ```

#### 5.4 Nota sobre visualización

Mientras entrena, abrir `http://localhost:8000` en el browser de Showdown.
Las batallas aparecen en tiempo real con la animación completa del juego.
Para el video, capturar pantalla con Showdown a la izquierda y el dashboard
a la derecha.

---

### 6. Dashboard de entrenamiento (`src/06_dashboard.py`)

Todo en un solo archivo Python. FastAPI sirve el HTML inline.

**Endpoints:**
- `GET /` → HTML del dashboard
- `GET /metrics` → JSON con lista de todos los checkpoints registrados
- `POST /update` → recibe `{episode, winrate_last_100, avg_reward_last_100, epsilon}`
  y lo agrega a lista en memoria (sin base de datos, solo RAM)

**HTML del dashboard (string inline en el código Python):**

Estructura visual:
```
┌─────────────────────────────────────────────────┐
│  🎮 Pokémon RL — Dashboard de Entrenamiento     │
├──────────┬──────────┬──────────┬────────────────┤
│ Episodio │ Win Rate │  Reward  │    Epsilon     │
│   2000   │  73.0%   │   4.2    │    0.05        │
├──────────┴──────────┴──────────┴────────────────┤
│  [Gráfica win rate por episodio - línea roja]   │
├─────────────────────────────────────────────────┤
│  [Gráfica reward promedio - línea amarilla]     │
├─────────────────────────────────────────────────┤
│  Últimas 10 batallas                            │
│  Ep.1950: WIN  +8.3  |  Ep.1960: LOSS  -2.1 …  │
└─────────────────────────────────────────────────┘
```

Implementación:
- Chart.js desde CDN `https://cdn.jsdelivr.net/npm/chart.js`
- `setInterval(fetchMetrics, 2000)` para auto-refresh
- Fondo `#1a1a2e`, texto blanco
- Colores: win rate `#e63946` (rojo), reward `#ffd700` (amarillo)
- Indicadores grandes en la fila superior (font-size grande, bold)
- Tabla de últimas 10 batallas con color verde/rojo según victoria/derrota

**Arranque:**
```bash
uv run python src/06_dashboard.py
# Abre http://localhost:9000
```

---

### 7. Figuras para el informe (`src/07_report_figures.py`)

Leer `outputs/metrics.json` y `outputs/models/training_log.json` para
poblar figuras con valores reales.

- Distribución de duración de combates (turnos)
  → `outputs/figures/battle_duration.png`
- Top 10 Pokémon más usados en Gen 8 Random Battle
  → `outputs/figures/top_pokemon.png`
- Curva de aprendizaje: win rate vs episodios (con línea de RandomPlayer
  al 50% como baseline)
  → `outputs/figures/rl_learning_curve.png`
- Tabla comparativa de las tres técnicas como PNG:

  | Técnica       | Algoritmo  | Métrica principal | Valor   |
  |---|---|---|---|
  | Clustering    | K-Means    | Silhouette Score  | [valor] |
  | Clasificación | XGBoost    | F1 Macro          | [valor] |
  | Refuerzo      | Q-Learning | Win Rate final    | [valor] |

  → `outputs/figures/model_comparison.png`

- Todas: seaborn whitegrid, títulos en español, 150 dpi, figsize apropiado

---

### 8. Informe IEEE (`report/ieee_report.md`)

Markdown con estructura IEEE doble columna simulada. Poblar con valores
reales de `outputs/metrics.json`. Placeholder `[VALOR]` donde falten datos.

**Límite estricto: máximo 6 páginas IEEE doble columna.** Ser conciso — cada
sección debe caber en el espacio asignado. Priorizar figuras sobre texto.

**Justificar conexión RL-dataset:** mencionar explícitamente en la sección de
metodología que el diseño del MDP (variables de estado, reward shaping) se
derivó del análisis previo del dataset (features discriminantes del
clasificador, arquetipos del clustering).

**Secciones:**

1. **Abstract** — máx 150 palabras. Dataset gen8randombattle, tres técnicas,
   hallazgo principal de cada una, resultado del agente.

2. **I. Introducción** — Pokémon Showdown como benchmark de IA, por qué Gen 8,
   motivación, estructura.

3. **II. Dataset y Preprocesamiento** — HolidayOugi/pokemon-showdown-replays, filtrado gen8randombattle,
   tabla de features extraídas, estadísticas descriptivas del dataset limpio.

4. **III. Metodología**
   - A. Clustering K-Means — descripción, método del codo, interpretación
     de arquetipos encontrados
   - B. Clasificación XGBoost — variable objetivo, features, hiperparámetros
   - C. Q-Learning con poke-env — definición formal del MDP:
     - Estado S (8 variables discretas)
     - Acciones A (9 acciones: 4 movimientos + 5 switches)
     - Función de reward R
     - Parámetros (lr, gamma, epsilon decay)
     - Mención de visualización en Showdown

5. **IV. Resultados y Discusión** — métricas reales con figuras referenciadas,
   análisis de la curva de aprendizaje (¿en qué episodio supera el 50%?),
   interpretación de clusters, features más importantes del clasificador,
   comparación de las tres técnicas.

6. **V. Conclusiones** — hallazgos, limitaciones documentadas:
   - Q-Learning tabular no escala bien a estados continuos
   - Q-Learning tabular con estado discreto (tradeoff interpretabilidad vs escala)
   - Oponente RandomPlayer es débil — win rate alto no garantiza competitividad
   - Trabajo futuro: DQN, oponente MaxDamage, equipo fijo optimizado

7. **Referencias** — formato IEEE, mínimo 5:
   - HolidayOugi/pokemon-showdown-replays (HuggingFace)
   - poke-env (Sahovic, 2020)
   - XGBoost (Chen & Guestrin, 2016)
   - Sutton & Barto — RL: An Introduction, 2nd ed. (2018)
   - Pokémon Showdown — github.com/smogon/pokemon-showdown

---

## Cómo correr el proyecto completo

```bash
# ── Una sola vez ──────────────────────────────────────────
uv run python src/00_setup.py
uv run python src/01_download.py
uv run python src/02_preprocess.py

# ── Técnicas sobre datos históricos ──────────────────────
uv run python src/03_clustering.py
uv run python src/04_classification.py

# ── Entrenamiento (abrir 3 terminales) ───────────────────

# Terminal A — servidor Showdown
cd showdown && node pokemon-showdown start --no-security

# Terminal B — dashboard
uv run python src/06_dashboard.py

# Terminal C — agente (arrancar después de A y B)
uv run python src/05_train_agent.py

# ── Ver en el browser ────────────────────────────────────
# http://localhost:8000  →  combates en vivo (Showdown)
# http://localhost:9000  →  dashboard de entrenamiento

# ── Figuras e informe (después del entrenamiento) ────────
uv run python src/07_report_figures.py
# Editar report/ieee_report.md con valores reales
```

---

## Notas importantes

- `random_state=42` en todo lo que requiera aleatoriedad
- Cada script es independiente; asume que el paso anterior ya corrió
- El estado de la Q-table es intencionalmente pequeño (8 variables discretas)
  para que el aprendizaje tabular sea viable. Documentar esta decisión
  en el informe: ventaja = interpretabilidad, limitación = no escala
- Si el dataset supera la RAM disponible, usar muestra de 300,000 batallas
  gen8randombattle — sigue cumpliendo el requisito de 100,000 registros
- El dashboard tolera que el script de entrenamiento no esté corriendo
  y viceversa — los errores de conexión se ignoran silenciosamente
- **Para el video de 6 minutos:**
  - 0:00–1:00 Intro: qué es Pokémon Showdown, motivación del proyecto
  - 1:00–2:00 Dataset y preprocesamiento
  - 2:00–3:00 Clustering: mostrar radar chart y clusters
  - 3:00–4:00 Clasificación: matriz de confusión y feature importance
  - 4:00–5:30 Agente jugando en vivo: pantalla dividida Showdown + dashboard
  - 5:30–6:00 Conclusiones y trabajo futuro

## Fase ambiciosa (no implementar aún — documentar como trabajo futuro)

Cuando el MVP esté funcionando, los siguientes pasos para escalar:

1. **DQN en lugar de Q-Learning tabular**
   - Red neuronal que recibe el estado como vector continuo
   - Usar `stable-baselines3` con política MlpPolicy
   - El estado puede incluir stats exactos en lugar de rangos discretos

2. **Oponente más fuerte**
   - Reemplazar RandomPlayer por `MaxDamagePlayer` (elige siempre el
     movimiento de mayor daño base)
   - Luego self-play: el agente se enfrenta a versiones anteriores de sí mismo

3. **Predicción del equipo rival**
   - Usar el clasificador XGBoost para estimar el arquetipo del equipo rival
     basándose en los Pokémon vistos, e incorporarlo al estado del agente
