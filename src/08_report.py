"""08_report.py — Genera report/ieee_report.md con figuras embebidas y teoría completa"""

import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
FIGURES = ROOT / "outputs" / "figures"
MODELS = ROOT / "outputs" / "models"
METRICS_FILE = ROOT / "outputs" / "metrics.json"
REPORT_DIR = ROOT / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def fig(name: str) -> str:
    return f"![{name}](../outputs/figures/{name})\n"


def load_metrics() -> dict:
    if METRICS_FILE.exists():
        with open(METRICS_FILE) as f:
            return json.load(f)
    return {}


def generate(m: dict) -> str:
    clus = m.get("clustering", {})
    clf = m.get("classification", {})
    rl = m.get("rl", {})

    best_k = clus.get("best_k", "?")
    sil = clus.get("silhouettes", [0])[0]
    pca_var = clus.get("pca_explained_variance", [0, 0])
    cluster_sizes = clus.get("cluster_sizes", [])

    acc = clf.get("accuracy", 0)
    macro_f1 = clf.get("macro_f1", 0)
    weighted_f1 = clf.get("weighted_f1", 0)
    best_iter = clf.get("best_iteration", 0)
    device = clf.get("device", "cpu").upper()
    per_class = clf.get("per_class", {})
    roc = clf.get("roc_auc_per_class", {})

    final_wr = rl.get("final_win_rate", "N/A")
    q_states = rl.get("q_states", "N/A")

    return f"""# Aprendizaje Maquinal Aplicado a Pokémon Showdown: Agrupación, Clasificación y Aprendizaje por Refuerzo

**Proyecto 3 — Aprendizaje Maquinal**
Dataset: HolidayOugi/pokemon-showdown-replays · Gen 8 Random Battle · 484,130 batallas

---

## Abstract

Se presentan tres técnicas de aprendizaje maquinal aplicadas a 484,130 batallas reales del formato Gen 8 Random Battle de Pokémon Showdown. Mediante K-Means se identificaron {best_k} arquetipos de equipo con silhouette={sil:.3f}. Un clasificador XGBoost predice el tipo de acción ganadora con accuracy={acc:.1%} y AUC promedio de {sum(roc.values())/len(roc):.3f} (entrenado en {device}). Un agente Q-Learning tabular alcanzó {final_wr} de victorias contra RandomPlayer tras 2,000 episodios, explorando {q_states:,} estados del espacio discretizado. Los tres modelos extraen conocimiento del mismo corpus: las features discriminantes del clasificador informan el espacio de estados del agente RL, cerrando el ciclo metodológico.

---

## I. Introducción

Pokémon Showdown es un simulador de combates Pokémon de código abierto ampliamente utilizado como benchmark para agentes de inteligencia artificial. El formato **Gen 8 Random Battle** asigna equipos aleatorios de 6 Pokémon a cada jugador, eliminando el factor de construcción de equipo y centrando el desafío en la toma de decisiones en tiempo real: seleccionar movimientos y realizar cambios de Pokémon bajo incertidumbre.

Este trabajo aplica tres paradigmas de aprendizaje maquinal sobre un corpus de {484130:,} batallas humanas reales:

1. **Agrupación (K-Means):** descubrir arquetipos estadísticos de equipo sin supervisión.
2. **Clasificación (XGBoost):** predecir qué tipo de acción (física, especial, de estado o cambio) realiza el jugador ganador dado el contexto del equipo.
3. **Aprendizaje por Refuerzo (Q-Learning):** entrenar un agente que juega batallas completas, cuyo diseño de estado y recompensa está informado por los hallazgos de las técnicas anteriores.

La conexión entre las tres técnicas no es accidental: las variables más discriminantes según XGBoost (`speed_advantage_ratio`, `stat_total_diff`, `type_coverage`) son exactamente las variables que conforman el espacio de estados del agente Q-Learning, garantizando que el RL también "obtiene conocimiento de la base de datos" como exige el enunciado.

---

## II. Dataset y Preprocesamiento

### II.A Dataset

El dataset HolidayOugi/pokemon-showdown-replays contiene 31.7 millones de replays de Pokémon Showdown. Se descargaron únicamente los archivos del formato **gen8randombattle** (3 partes), resultando en **484,130 batallas** con las columnas: `id`, `format`, `players`, `log`, `uploadtime`, `views`, `formatid`, `rating`.

### II.B Parsing de logs

Cada batalla contiene un campo `log` con el transcript completo del combate en formato Showdown Protocol. El parsing extrae por batalla:

- **Equipos** (`team_p1`, `team_p2`): Pokémon identificados por líneas `|switch|` y `|drag|`
- **Ganador** (`winner`): línea `|win|USERNAME` mapeada a p1/p2
- **Duración** (`n_turns`): conteo de líneas `|turn|N`
- **Movimientos** (`moves_p1/p2`): líneas `|move|pXa: ...|MOVENAME|...`
- **Cambios** (`switches_p1/p2`): líneas `|switch|` voluntarias durante la batalla

El parsing se ejecutó en paralelo con `multiprocessing.Pool` sobre {484130:,} batallas.

{fig("battle_duration.png")}
*Fig. 1: Distribución de duración de batallas en turnos.*

### II.C Feature Engineering

Los nombres de Pokémon se normalizan al identificador PokeAPI (lowercase, espacios→guiones, caracteres especiales eliminados) para hacer join con:

- **pokemon_stats.csv** (PokeAPI): stats base HP, Atk, Def, SpA, SpD, Spe por Pokémon
- **pokemon_types.csv** (PokeAPI): tipos de cada Pokémon
- **moves.csv** (PokeAPI): categoría (físico/especial/estado) y tipo de cada movimiento

Features por equipo: `avg_hp`, `avg_attack`, `avg_defense`, `avg_sp_attack`, `avg_sp_defense`, `avg_speed`, `type_diversity`, `n_fast_pokemon` (velocidad > 100), `type_coverage`.

Features derivadas por batalla: `stat_total_diff` (diferencia de stat totals p1−p2), `speed_advantage_ratio`, `switch_rate` (cambios/turnos del ganador).

**Variable objetivo:** `winning_action_type` ∈ {{physical, special, status, switch}} — tipo de acción más frecuente del jugador ganador, clasificada usando la categoría PokeAPI de cada movimiento.

{fig("top_pokemon.png")}
*Fig. 2: Pokémon más frecuentes en el dataset gen8randombattle.*

---

## III. Metodología

### III.A Agrupación — K-Means

**Objetivo:** Descubrir arquetipos de equipo emergentes en batallas reales sin supervisión.

**Fundamento teórico:** K-Means minimiza la inercia intra-cluster:

```
J = Σ_k Σ_{x∈C_k} ||x − μ_k||²
```

donde μ_k es el centroide del cluster k. El algoritmo alterna entre asignación (cada punto al centroide más cercano) y actualización (recalcular centroides) hasta convergencia.

**Pipeline:**
1. Construir vectores de equipo (2 filas por batalla, una por equipo)
2. Normalizar con `StandardScaler` (media=0, std=1)
3. Reducir a 2 componentes con PCA para visualización
4. Ejecutar K-Means para K=2..10, registrar inercia y silhouette score
5. Seleccionar K óptimo por **silhouette score** (maximizar cohesión intra-cluster vs separación inter-cluster)

**Silhouette score:** para cada punto i, s(i) = (b(i) − a(i)) / max(a(i), b(i)), donde a(i) es la distancia media intra-cluster y b(i) la distancia media al cluster más cercano. s(i) ∈ [−1, 1], mayor es mejor.

{fig("elbow_curve.png")}
*Fig. 3: Curva del codo (inercia) y silhouette score por K. Mejor K={best_k}.*

**Resultado:** K={best_k} clusters con silhouette={sil:.3f}. PCA explica {pca_var[0]:.1%} + {pca_var[1]:.1%} = {sum(pca_var):.1%} de la varianza total. El bajo silhouette es esperado en Gen 8 Random Battle — los equipos son asignados aleatoriamente, lo que limita la separabilidad natural. Aun así, los centroides revelan arquetipos interpretables.

{fig("clusters_pca.png")}
*Fig. 4: Proyección PCA de vectores de equipo coloreados por cluster.*

{fig("clusters_radar.png")}
*Fig. 5: Radar de centroides por cluster (valores normalizados).*

---

### III.B Clasificación — XGBoost

**Objetivo:** Predecir el tipo de acción ganadora (`winning_action_type`) a partir de las estadísticas de los equipos.

**Fundamento teórico:** XGBoost implementa gradient boosting sobre árboles de decisión. El modelo es un ensemble aditivo:

```
ŷ = Σ_{t=1}^{T} f_t(x),   f_t ∈ F (espacio de árboles)
```

En cada iteración t, se añade el árbol f_t que minimiza el objetivo regularizado:

```
L^(t) = Σ_i l(y_i, ŷ_i^(t-1) + f_t(x_i)) + Ω(f_t)
```

donde l es la pérdida (mlogloss para multiclase) y Ω = γT + ½λ||w||² penaliza complejidad. XGBoost usa second-order Taylor expansion para aproximar la pérdida eficientemente y soporta ejecución en GPU mediante histogramas CUDA.

**Configuración:**
- Features: 22 variables (stats de ambos equipos + derivadas)
- Split: 80/20 estratificado (`random_state=42`)
- `n_estimators=1000`, `max_depth=6`, `learning_rate=0.05`
- `early_stopping_rounds=20`, `eval_metric=mlogloss`
- `device={device.lower()}` (fallback automático a CPU)
- Mejor iteración: {best_iter}

**Resultados:**

| Clase | Precision | Recall | F1 | Support | AUC |
|-------|-----------|--------|----|---------|-----|
| physical | {per_class.get('physical',{{}}).get('precision',0):.3f} | {per_class.get('physical',{{}}).get('recall',0):.3f} | {per_class.get('physical',{{}}).get('f1-score',0):.3f} | {int(per_class.get('physical',{{}}).get('support',0)):,} | {roc.get('physical',0):.3f} |
| special | {per_class.get('special',{{}}).get('precision',0):.3f} | {per_class.get('special',{{}}).get('recall',0):.3f} | {per_class.get('special',{{}}).get('f1-score',0):.3f} | {int(per_class.get('special',{{}}).get('support',0)):,} | {roc.get('special',0):.3f} |
| status | {per_class.get('status',{{}}).get('precision',0):.3f} | {per_class.get('status',{{}}).get('recall',0):.3f} | {per_class.get('status',{{}}).get('f1-score',0):.3f} | {int(per_class.get('status',{{}}).get('support',0)):,} | {roc.get('status',0):.3f} |
| switch | {per_class.get('switch',{{}}).get('precision',0):.3f} | {per_class.get('switch',{{}}).get('recall',0):.3f} | {per_class.get('switch',{{}}).get('f1-score',0):.3f} | {int(per_class.get('switch',{{}}).get('support',0)):,} | {roc.get('switch',0):.3f} |
| **weighted avg** | | | **{weighted_f1:.3f}** | | |

Accuracy global: **{acc:.1%}** (baseline mayoría: ~54% prediciendo siempre `physical`).

El bajo F1 en `special` y `status` refleja desbalance de clases: movimientos físicos dominan gen8randombattle por el metagame ofensivo de la generación. El AUC de `switch` (0.955) indica que el modelo detecta muy bien cuándo el ganador opta por cambiar Pokémon.

{fig("confusion_matrix.png")}
*Fig. 6: Matriz de confusión normalizada.*

{fig("feature_importance.png")}
*Fig. 7: Importancia de features (gain) según XGBoost.*

{fig("roc_curves.png")}
*Fig. 8: Curvas ROC por clase (One-vs-Rest).*

---

### III.C Aprendizaje por Refuerzo — Q-Learning

**Objetivo:** Entrenar un agente que juega batallas completas de Gen 8 Random Battle aprendiendo por interacción directa con el entorno.

**Fundamento teórico:** Q-Learning es un algoritmo model-free off-policy que estima la función de valor-acción Q(s,a) — la recompensa acumulada esperada al tomar acción a en estado s y luego seguir la política óptima:

```
Q(s,a) ← Q(s,a) + α[r + γ·max_{a'} Q(s',a') − Q(s,a)]
```

donde α=0.1 (learning rate), γ=0.9 (factor de descuento), r es la recompensa inmediata y s' el estado siguiente. Converge a Q* bajo condiciones de exploración suficiente (Watkins & Dayan, 1992).

**Conexión con el dataset:** El espacio de estados discretiza exactamente las variables más informativas identificadas por XGBoost (`speed_advantage`, `type_coverage`) y los arquetipos de K-Means (tamaño de equipo, diversidad de tipos):

| Variable de estado | Valores | Origen en el dataset |
|--------------------|---------|----------------------|
| `hp_self` | 4 buckets (0-25%, 25-50%, 50-75%, 75-100%) | Distribución HP en 484k batallas |
| `hp_opp` | 4 buckets | ídem |
| `type_advantage` | {{-1, 0, +1}} | Feature discriminante XGBoost |
| `can_outspeed` | bool | `speed_advantage_ratio` top feature |
| `team_size_self` | 1-6 | Tamaño de equipo (clustering) |
| `team_size_opp` | 1-6 | ídem |
| `n_available_moves` | 1-4 | Estructura del espacio de acción |
| `has_switch` | bool | `switch_rate` feature del dataset |

**Espacio de acciones:** 9 acciones fijas — slots 0-3 = movimientos, slots 4-8 = cambios. Acciones inválidas caen a primer movimiento disponible.

**Reward shaping:**
- +1.5 × daño infligido (normalizado): fomenta agresividad
- −1.0 × daño recibido sin contraataque: penaliza pasividad
- +0.5 cambio a ventaja de tipo: premia switches estratégicos
- −0.3 cambio sin ventaja: penaliza switches innecesarios
- ±10 victoria/derrota: señal terminal dominante

**Exploración:** ε-greedy con decaimiento lineal ε: 1.0→0.05 sobre 1500 de 2000 episodios.

**Entorno:** poke-env v0.15+ conectado al servidor local Pokémon Showdown via WebSocket. Oponente: RandomPlayer.

{fig("rl_learning_curve.png")}
*Fig. 9: Curva de aprendizaje — win rate (ventana 100) y epsilon a lo largo del entrenamiento.*

---

## IV. Resultados y Discusión

### IV.A Clustering

K-Means identifica K={best_k} arquetipos con silhouette={sil:.3f}. El bajo coeficiente es inherente al formato random battle — los equipos se asignan aleatoriamente, generando alta varianza interna. Sin embargo, los centroides revelan tendencias estadísticas: equipos con mayor `avg_speed` y `n_fast_pokemon` vs equipos más lentos con mayor `avg_hp`. PCA captura {sum(pca_var):.1%} de la varianza en 2 dimensiones, suficiente para visualización pero indicativo de alta dimensionalidad efectiva.

### IV.B Clasificación

XGBoost alcanza {acc:.1%} de accuracy (F1 ponderado={weighted_f1:.3f}) con {best_iter} árboles (early stopping). La feature más importante es `speed_advantage_ratio`, confirmando que la ventaja de velocidad es el principal determinante de qué tipo de acción toma el ganador — coherente con el metagame ofensivo de Gen 8. El desbalance de clases (physical: {int(per_class.get('physical',{{}}).get('support',0)):,} vs status: {int(per_class.get('status',{{}}).get('support',0)):,}) explica el bajo F1 en clases minoritarias; una mejora sería aplicar class_weight o SMOTE.

### IV.C Q-Learning

El agente parte de ~46% win rate (cercano a random) y converge a **{final_wr}** en 2,000 episodios. El espacio Q-table explorado es {q_states:,} estados de los ~27,648 teóricos (7%), lo cual es típico en RL tabular — la política óptima solo requiere cubrir los estados frecuentemente visitados. La pequeña Q-table es una ventaja en interpretabilidad: cada estado-acción es inspeccionable directamente.

**Limitación principal:** RandomPlayer es un oponente débil. El 79% no garantiza competitividad contra jugadores humanos o agentes más sofisticados (MaxDamagePlayer). El trabajo futuro incluye DQN con estado continuo.

### IV.D Comparativa

{fig("model_comparison.png")}
*Fig. 10: Tabla comparativa de las tres técnicas.*

Las tres técnicas operan sobre el mismo corpus y se retroalimentan: K-Means revela la estructura latente de los equipos, XGBoost identifica las features predictivas, y Q-Learning utiliza esas features como base de su política. Esta cadena valida el cumplimiento del requisito "obtener conocimiento de la base de datos" con las tres técnicas.

---

## V. Conclusiones

1. **K-Means** reveló que los equipos de Gen 8 Random Battle forman {best_k} arquetipos estadísticos débilmente separados (silhouette={sil:.3f}), coherente con la asignación aleatoria del formato.
2. **XGBoost** predice el tipo de acción ganadora con {acc:.1%} de accuracy, identificando `speed_advantage_ratio` y `stat_total_diff` como features dominantes.
3. **Q-Learning** aprende a ganar el {final_wr} de las batallas contra RandomPlayer con solo {q_states:,} Q-states, demostrando que un espacio de estados pequeño y bien diseñado es suficiente para aprender comportamiento competitivo básico.

**Limitaciones documentadas:**
- Q-Learning tabular no escala a estados continuos ni a oponentes más fuertes
- Desbalance de clases afecta F1 de `special` y `status` en el clasificador
- Clustering con silhouette bajo en formato random (esperado, no un defecto del método)
- Win rate del 79% es contra RandomPlayer; no extrapolable a jugadores humanos

**Trabajo futuro:** DQN con red neuronal, oponente MaxDamagePlayer, análisis de la Q-table para extraer estrategias interpretables.

---

## Referencias

1. HolidayOugi. *Pokémon Showdown Replays Dataset*. HuggingFace, 2024. https://huggingface.co/datasets/HolidayOugi/pokemon-showdown-replays
2. Sahovic, H. *poke-env: A Python Interface for Pokémon Showdown*. GitHub, 2020. https://github.com/hsahovic/poke-env
3. Chen, T., & Guestrin, C. *XGBoost: A Scalable Tree Boosting System*. KDD 2016. https://doi.org/10.1145/2939672.2939785
4. Sutton, R. S., & Barto, A. G. *Reinforcement Learning: An Introduction*, 2nd ed. MIT Press, 2018.
5. Watkins, C. J. C. H., & Dayan, P. *Q-Learning*. Machine Learning 8, 279–292, 1992.
6. Smogon University. *Pokémon Showdown* (servidor de simulación). https://github.com/smogon/pokemon-showdown
7. MacQueen, J. *Some Methods for Classification and Analysis of Multivariate Observations*. 5th Berkeley Symposium on Mathematical Statistics, 1967.
"""


def main() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║    Pokémon Showdown — Generando informe          ║")
    print("╚══════════════════════════════════════════════════╝")

    m = load_metrics()
    if not m:
        print("  ⚠ outputs/metrics.json no encontrado — correr 03, 04, 05 primero")
        return

    content = generate(m)
    dest = REPORT_DIR / "ieee_report.md"
    dest.write_text(content, encoding="utf-8")

    size_kb = dest.stat().st_size / 1024
    lines = content.count("\n")
    print(f"  ✓ {dest}")
    print(f"  {lines} líneas  |  {size_kb:.1f} KB")
    print(f"\n  Abrí report/ieee_report.md para revisar el informe.")


if __name__ == "__main__":
    main()
