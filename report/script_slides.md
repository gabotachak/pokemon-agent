# Script de slides — "¿Puede una máquina aprender a jugar Pokémon sola?"

> **Uso:** este archivo describe slide por slide el contenido visual para acompañar `script_summary.md`.
> Cada slide incluye título, layout sugerido, texto visible en pantalla e imágenes.
> Pensado para generar en Google Slides vía Gemini.
> **Total:** 20 slides · ~18 s/slide promedio · fondo oscuro (#1a1a2e o similar).

---

## SLIDE 1 — Portada ⏱️ 0:00

**Layout:** centrado, pantalla completa oscura.

**Texto principal (grande, centrado):**
> ¿Puede una máquina aprender a jugar Pokémon sola?

**Subtítulo:**
> Aprendizaje de Máquinas — Proyecto 3
> K-Means · XGBoost · Q-Learning

**Pie de página (pequeño):**
> 484.130 batallas reales · Gen 8 Random Battle

**Visual:** imagen o ícono de una Poké Ball estilizada a la izquierda, fondo muy oscuro con destellos sutiles.

---

## SLIDE 2 — El tesoro de datos ⏱️ 0:00–0:20

**Layout:** mitad izquierda texto, mitad derecha número grande.

**Encabezado:** `El dataset`

**Texto izquierda:**
- Cada partida de Pokémon online queda **grabada**
- Registro público de humanos decidiendo bajo presión
- 31 millones de partidas disponibles

**Número derecha (enorme, color acento):**
> **31.700.000**
> partidas registradas

**Visual:** contador estilo odómetro o fuente monoespaciada grande. Fondo con líneas de código/log de batalla en transparencia muy baja.

---

## SLIDE 3 — Nuestro recorte ⏱️ 0:15–0:25

**Layout:** centrado, enfocado.

**Encabezado:** `Nuestros datos`

**Número grande centrado (color dorado/amarillo):**
> **484.130**
> batallas reales

**Subtexto:** `Gen 8 Random Battle · Pokémon Showdown`

**Visual:** barra de progreso que muestra 484.130 de 31.700.000 (muy pequeña fracción), para dar escala. Icono de base de datos o tabla.

---

## SLIDE 4 — Las tres preguntas ⏱️ 0:25–0:40

**Layout:** tres tarjetas horizontales centradas, una por pregunta.

**Encabezado:** `Tres preguntas · Tres familias del ML`

**Tarjeta 1 (izquierda, azul):**
> 🔍 ¿Hay tipos de equipo?
> *Agrupación*

**Tarjeta 2 (centro, naranja):**
> 🎯 ¿Se predice cómo gana alguien?
> *Clasificación*

**Tarjeta 3 (derecha, verde):**
> 🤖 ¿Puede una máquina aprender a jugar sola?
> *Refuerzo*

**Visual:** las tres tarjetas aparecen con un ícono de "detective" o herramienta sobre cada una. Fondo oscuro, bordes de tarjetas luminosos.

---

## SLIDE 5 — ML: reglas vs. datos ⏱️ 0:40–0:58

**Layout:** dos columnas simétricas separadas por una línea vertical.

**Encabezado:** `¿Qué es el aprendizaje de máquinas?`

**Columna izquierda (programación normal):**
```
REGLAS
  +
DATOS
  ↓
RESPUESTAS
```
Etiqueta: *Programación clásica*

**Columna derecha (ML):**
```
DATOS
  +
RESPUESTAS
  ↓
REGLAS
```
Etiqueta: *Machine Learning*

**Nota central pequeña:** `Las flechas se invierten`

**Visual:** flechas animadas o coloreadas en dirección opuesta entre columnas. Minimalista, dos bloques de color contrastante.

---

## SLIDE 6 — Pokémon como problema matemático ⏱️ 0:58–1:20

**Layout:** mitad izquierda diagrama de tipos, mitad derecha estadísticas de velocidad.

**Encabezado:** `Lo que manda en cada combate`

**Bloque izquierdo — Ventaja de tipo:**
> 💧 Agua → 🔥 Fuego → 🌿 Planta → 💧
> **×2 daño** / **÷2 daño**
> (18 tipos en total)

**Bloque derecho — Velocidad:**
> ⚡ El más rápido golpea **primero**
> Golpear primero = knockear antes de recibir daño

**Pie de slide:**
> Gen 8 Random Battle: equipos **al azar** → el mérito está en **cómo juegas**

**Visual:** triángulo clásico agua-fuego-planta con multiplicadores visibles. Medidor de velocidad tipo velocímetro para el bloque derecho.

---

## SLIDE 7 — El preprocesamiento ⏱️ 1:20–1:30

**Layout:** flecha de transformación de izquierda a derecha, con imagen abajo.

**Encabezado:** `Del texto crudo a los números`

**Izquierda (texto feo, fuente monoespaciada, gris):**
```
|move|p1a: Toxapex|Scald|...
|switch|p2a: Garchomp|...
|-damage|p1a: Toxapex|...
```

**Flecha central grande** → `80 % del esfuerzo`

**Derecha (tabla limpia):**
| turns | avg_speed | type_div | winner |
|-------|-----------|----------|--------|
| 22    | 87.3      | 5        | p1     |
| 14    | 91.1      | 4        | p2     |

**Imagen abajo (ancho completo):**
![Duración de batallas](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/battle_duration.png)

**Leyenda imagen:** `Distribución de duración de batallas — mediana: 20 turnos`

---

## SLIDE 8 — K-Means: concepto ⏱️ 1:30–1:55

**Layout:** diagrama animable a la derecha, texto a la izquierda.

**Encabezado:** `Técnica 1: K-Means — Agrupar sin etiquetas`

**Texto izquierda (bullets):**
- Sin respuestas correctas → **aprendizaje no supervisado**
- Cada equipo = un punto en el espacio de estadísticas
- K-Means: pone **banderas**, agrupa por cercanía, recentra, repite

**Pasos visualizados (derecha, columna o diagrama):**
1. Dos banderas al azar
2. Cada punto → bandera más cercana
3. Banderas → centro de su grupo
4. Repetir hasta convergencia ✓

**Visual:** nube de puntos dispersos con dos banderas/centroides. Colores: puntos azules y naranjas según grupo.

---

## SLIDE 9 — K-Means: la fórmula ⏱️ 1:55–2:10

**Layout:** fórmula grande centrada, con desglose abajo.

**Encabezado:** `Lo que minimiza K-Means`

**Fórmula (grande, centrada):**
$$J = \sum_k \sum_{x \in C_k} \|x - \mu_k\|^2$$

**Desglose en tres líneas pequeñas abajo:**
| Símbolo | Significa |
|---------|-----------|
| `x − μₖ` | distancia de un equipo a su bandera |
| `‖ ‖²` | elevar al cuadrado (todo positivo, grandes pesan más) |
| `ΣΣ` | suma sobre todos los puntos y todos los grupos |

**Conclusión pequeña al pie:**
> K-Means busca la disposición de banderas que hace **J** lo más pequeño posible: grupos compactos.

**Visual:** fondo oscuro, fórmula en color claro/blanco. Tabla de desglose con fondo ligeramente más claro.

---

## SLIDE 10 — K-Means: resultados ⏱️ 2:10–2:30

**Layout:** dos imágenes lado a lado, número grande arriba.

**Encabezado:** `Resultado: dos grupos, débilmente separados`

**Número arriba centrado:**
> **Silueta = 0,136**
> *(0 = sin estructura · 1 = perfecto)*

**Imagen izquierda:**
![Arquetipos de equipo en PCA](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/clusters_pca.png)

*Leyenda:* `Equipos proyectados en 2D (PCA)`

**Imagen derecha:**
![Radar de centroides](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/clusters_radar.png)

*Leyenda:* `Perfil promedio de cada arquetipo`

**Conclusión pie (color acento):**
> ¿Fracaso? No. Equipos al azar → claro que se parecen. **Primera pista: el estilo no está en el equipo.**

---

## SLIDE 11 — XGBoost: concepto árboles ⏱️ 2:30–2:55

**Layout:** diagrama de árboles en cascada a la derecha, texto a la izquierda.

**Encabezado:** `Técnica 2: XGBoost — Predecir con ejemplos`

**Texto izquierda:**
- Ahora **sí** hay respuestas correctas → aprendizaje supervisado
- Pregunta: ¿el equipo delata **cómo** va a ganar?
- Cuatro estilos de victoria:
  - 💥 Físico · ✨ Especial · 🌀 Estado · 🔄 Cambio

**Derecha — diagrama de árboles en fila:**
```
Árbol 1 → predice
   ↓ (errores)
Árbol 2 → corrige errores de 1
   ↓ (errores restantes)
Árbol 3 → corrige errores de 2
   ...
```
**Etiqueta:** *Gradient Boosting: cada árbol parchea al anterior*

**Fórmula pequeña al pie:**
$$\hat{y} = \sum_{t=1}^{T} f_t(x)$$
> La predicción final = suma de todos los árboles

---

## SLIDE 12 — Data leakage: la trampa ⏱️ 2:55–3:20

**Layout:** slide de alerta — fondo rojo oscuro o con borde rojo, ícono de advertencia.

**Encabezado (rojo):** `⚠️ FUGA DE INFORMACIÓN — Data Leakage`

**Descripción del problema (centrado):**
> Una característica — **tasa de cambios** — predecía "gana cambiando" con precisión sospechosa.

**Diagrama circular (trampa):**
```
"¿Gana cambiando?"  ←──────────────────┐
        ↑                              │
  se calcula con                       │
  conteo de cambios ──→  "tasa de cambios"
  del ganador            (también usa conteo
                          de cambios del ganador)
```

**Solución (verde):**
> ✂️ Característica eliminada. Las cifras mostradas son **sin** esta trampa.

**Analogía pequeña al pie:**
> Como adivinar si alguien aprobó usando su nota final.

---

## SLIDE 13 — XGBoost: resultados ⏱️ 2:55–3:50

**Layout:** imagen grande, barra comparativa arriba, conclusión abajo.

**Encabezado:** `Resultado: 59 % — cinco puntos sobre el azar`

**Barra comparativa (arriba):**
```
Línea base (adivinar): ████████████████████ 54 %
Modelo XGBoost:        ████████████████████░ 59 %
```
*Diferencia: +5 puntos*

**Imagen principal:**
![Importancia de características XGBoost](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/feature_importance.png)

*Leyenda:* `Top features por ganancia — n_turns domina`

**Conclusión al pie (color acento):**
> `n_turns` solo se conoce cuando la batalla ya **terminó**. El modelo no predice: **explica en retrospectiva**.
> Misma conclusión que K-Means, por otro camino.

---

## SLIDE 14 — XGBoost: el hallazgo ⏱️ 3:35–3:50

**Layout:** slide de cierre de sección, texto centrado grande.

**Encabezado:** `El hallazgo de la clasificación`

**Texto grande centrado:**
> El estilo con que ganas no está escrito en tu equipo.
> **Está escrito en cómo juegas.**

**Tres bullets de soporte pequeños:**
- Equipo casi no predice el estilo de victoria
- La única señal fuerte (`n_turns`) es post-hoc
- Conclusión convergente con K-Means (camino completamente distinto)

**Visual:** fondo oscuro, texto blanco grande, sin imágenes — slide de impacto.

---

## SLIDE 15 — Q-Learning: concepto ⏱️ 3:50–4:15

**Layout:** tabla/libreta a la derecha, texto a la izquierda.

**Encabezado:** `Técnica 3: Q-Learning — Aprender jugando`

**Texto izquierda:**
- Sin ejemplos, sin profesor → **aprendizaje por refuerzo**
- Como entrenar un perro: premio y castigo
- El agente juega 2.000 partidas y **aprende de la experiencia**

**Diagrama derecha — la libreta Q:**
```
         | Atacar | Cambiar | Otra
---------+--------+---------+------
Situación A |  0.8   |   0.2   | -0.1
Situación B | -0.3   |   1.1   |  0.5
Situación C |  1.4   |  -0.2   |  0.7
...27.648 filas posibles
```
*Empieza vacía. Se llena con experiencia.*

**Leyenda:** `Cada casilla = "qué tan buena fue esta acción en esta situación"`

---

## SLIDE 16 — Q-Learning: la fórmula ⏱️ 4:15–4:35

**Layout:** fórmula grande arriba, desglose en tabla abajo.

**Encabezado:** `La ecuación de Bellman — en una frase`

**Fórmula (grande, centrada):**
$$Q(s,a) \leftarrow Q(s,a) + \alpha \left[r + \gamma \max_{a'} Q(s', a') - Q(s,a)\right]$$

**Desglose en tabla (abajo):**
| Símbolo | Significa | Valor usado |
|---------|-----------|-------------|
| `Q(s,a)` | valor de hacer acción `a` en situación `s` | se actualiza |
| `r` | recompensa inmediata | según tabla de premios |
| `max Q(s',a')` | mejor futuro posible desde el nuevo estado | — |
| `γ` (gamma) | cuánto importa el futuro | 0,9 |
| `α` (alfa) | velocidad de aprendizaje | 0,1 |

**Frase clave al pie (color acento):**
> Ajusta tu opinión sobre la jugada en dirección a la sorpresa, contando el premio de ahora y las puertas que abre después.

---

## SLIDE 17 — Q-Learning: diseño del agente ⏱️ 4:35–4:55

**Layout:** dos columnas — estado (izquierda) y recompensas (derecha).

**Encabezado:** `Lo que ve y lo que gana el agente`

**Columna izquierda — Estado (8 variables):**
| Variable | Valores |
|----------|---------|
| ❤️ HP propio | 4 buckets: 0–25% / 25–50% / 50–75% / 75–100% |
| 💔 HP rival | 4 buckets iguales |
| ⚖️ Ventaja de tipo | -1 / 0 / +1 |
| ⚡ ¿Soy más rápido? | Sí / No |
| 🔢 Pokémon vivos (propio) | 1–6 |
| 🔢 Pokémon vivos (rival) | 1–6 |
| 🎮 Movimientos disponibles | 1–4 |
| 🔄 ¿Puede cambiar? | Sí / No |

**Columna derecha — Tabla de recompensas:**
| Evento | Recompensa |
|--------|-----------|
| Hacer daño | **+1,5** |
| Recibir daño sin devolver | **−1,0** |
| Cambiar a ventaja de tipo | **+0,5** |
| Cambiar sin razón | **−0,3** |
| Ganar la partida | **+10** |
| Perder la partida | **−10** |

---

## SLIDE 18 — Q-Learning: resultados ⏱️ 4:55–5:15

**Layout:** imagen grande central, número de impacto arriba.

**Encabezado:** `Resultado: de cero a 76,6 % de victorias`

**Número grande arriba (color dorado):**
> **76,6 %** de victorias
> *vs. rival que juega al azar*

**Imagen principal (ancho completo):**
![Curva de aprendizaje Q-Learning](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/rl_learning_curve.png)

*Leyenda:* `Win rate y epsilon (ε) a lo largo de 2.000 episodios`

**Bullets abajo:**
- Arranca por debajo del 50 % (explora al azar)
- Cruza la línea a los ~100 episodios
- Se estabiliza sobre el 76 %
- Solo visitó **2.039 de 27.648** situaciones posibles (7 %)

---

## SLIDE 19 — Tabla comparativa ⏱️ 5:15–5:40

**Layout:** tabla grande centrada, tres columnas de color.

**Encabezado:** `Las tres técnicas — resumen`

**Tabla (colores: azul / naranja / verde por técnica):**

| | 🔍 K-Means | 🎯 XGBoost | 🤖 Q-Learning |
|---|---|---|---|
| **Familia ML** | No supervisado | Supervisado | Refuerzo |
| **Hace** | Describe | Explica | Actúa |
| **Cómo aprende** | Sin respuestas | Con respuestas | Con premios |
| **Resultado** | 2 arquetipos | 59 % acierto | 76,6 % victorias |
| **¿Interpretable?** | ✅ Sí | ⚠️ Parcial | ✅ Sí (tabla) |

**Conclusión compartida (pie, color acento):**
> Las tres se apoyan en los mismos ejes: **velocidad · tipo · vida**.
> Dos llegaron, por caminos distintos, a la misma idea.

---

## SLIDE 20 — Cierre ⏱️ 5:40–6:00

**Layout:** dos partes — texto de impacto arriba, créditos abajo.

**Encabezado:** `Lo que aprendimos`

**Texto grande centrado (primera mitad):**
> "Los números son modestos. **A propósito.**"

**Bullets de honestidad metodológica:**
- Hallamos una trampa (data leakage) → la quitamos
- Vimos grupos débiles → explicamos por qué
- El agente solo le gana al azar → lo admitimos

**Frase final (fuente grande, centrada, color claro):**
> A veces lo más valioso que enseña una máquina es **lo poco que se podía saber de antemano.**

**Pie de slide — créditos:**
> Aprendizaje de Máquinas · Proyecto 3 · 2026
> *[Nombres de los integrantes]*

**Visual:** fundido a oscuro. Sin imágenes — slide de cierre limpio.

---

## Mapa rápido de imágenes

| Slide | Imagen | URL |
|-------|--------|-----|
| 7 | Duración de batallas | `outputs/figures/battle_duration.png` |
| 10 | Clusters en PCA | `outputs/figures/clusters_pca.png` |
| 10 | Radar de centroides | `outputs/figures/clusters_radar.png` |
| 13 | Feature importance XGBoost | `outputs/figures/feature_importance.png` |
| 18 | Curva de aprendizaje RL | `outputs/figures/rl_learning_curve.png` |

Base URL: `https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/`
