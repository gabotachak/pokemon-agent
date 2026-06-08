# Guión resumido — Video del proyecto (máx 6 minutos)

> **Formato:** narración estilo Veritasium, ajustada al límite de 6 min del entregable.
> **Idioma:** 100 % español. Narrador único.
> **Versión extendida:** ver `script_complete.md`.
> 🎙️ = narración · 🎬 = apoyo visual · ⏱️ = referencia de tiempo acumulado.

---

## 0 · Gancho — ⏱️ 0:00–0:40

🎬 *Un combate de Pokémon Showdown en marcha. Contador subiendo a "31.700.000 partidas".*

🎙️ Cada partida de Pokémon online queda **grabada**: un registro público de humanos decidiendo bajo presión, sin saber qué hará el rival. Existen treinta y un millones de ellas.

🎙️ Tomamos **484.130 batallas reales** y nos hicimos tres preguntas, una por cada gran familia del aprendizaje de máquinas.

🎬 *Tres tarjetas:* *"¿Hay tipos de equipo? 🔍" · "¿Se predice cómo gana alguien? 🎯" · "¿Puede una máquina aprender a jugar sola? 🤖"*

---

## 1 · Idea base + el terreno — ⏱️ 0:40–1:30

🎬 *Diagrama: programación normal (REGLAS→RESPUESTAS) vs ML (DATOS+RESPUESTAS→REGLAS), flechas invirtiéndose.*

🎙️ En programación normal tú das las reglas. En aprendizaje de máquinas das ejemplos y la máquina **descubre las reglas sola**.

🎬 *Triángulo agua→fuego→planta y un medidor de velocidad.*

🎙️ En Pokémon mandan dos cosas: la **ventaja de tipo** —el agua hace doble daño al fuego, mitad a la planta— y la **velocidad** —el más rápido golpea primero. Y elegimos un formato donde los equipos se reparten **al azar**: así, todo el mérito está en **cómo juegas**, no en cómo armaste el equipo. Recuerda esto.

🎙️ El trabajo invisible: convertir muros de texto de cada batalla en una tabla limpia de números. El 80 % del esfuerzo, y sin él nada funciona. Son datos reales: la mayoría de batallas dura unos 20 turnos.

![Duración de batallas](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/battle_duration.png)

---

## 2 · Técnica 1: K-Means (agrupar) — ⏱️ 1:30–2:30

🎬 *"Detective 1 — Agrupar". Nube de puntos; cada punto, un equipo.*

🎙️ Primera pregunta: **¿hay tipos de equipo?** Sin darle respuestas, le pedimos a la máquina que agrupe equipos por parecido. Esto es **K-Means**: pone banderas, cada equipo se une a la más cercana, las banderas se recentran, y se repite hasta que nada se mueve.

🎬 *Animación de 2 banderas convergiendo. Luego aparece* $J = \sum_k \sum_{x \in C_k} \|x - \mu_k\|^2$ *con un solo subrayado.*

🎙️ La fórmula solo mide una cosa: la **distancia total** de cada equipo a su bandera. K-Means la hace lo más pequeña posible: grupos compactos.

🎬 *Mostrar Figura 4 (clusters) y Figura 5 (radar). El número 0,136 grande en una barra de 0 a 1.*

![Arquetipos de equipo en PCA](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/clusters_pca.png)

![Radar de centroides](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/clusters_radar.png)

🎙️ ¿Resultado? Dos grupos, uno ofensivo y otro defensivo... pero **apenas distinguibles**, con una calidad de separación de 0,136, pegada a cero. ¿Fracaso? No: **es lo esperado**. Si los equipos salen de la misma bolsa al azar, claro que se parecen. Primera pista: **el estilo no está en el equipo**.

---

## 3 · Técnica 2: XGBoost (predecir) — ⏱️ 2:30–3:50

🎬 *"Detective 2 — Clasificar". Cuatro iconos de estilo de victoria: 💥 físico, ✨ especial, 🌀 estado, 🔄 cambio.*

🎙️ Segunda pregunta, ahora **con** respuestas: **¿el perfil de un equipo delata cómo va a ganar?** La herramienta es **XGBoost**: cientos de pequeños cuestionarios de sí/no —árboles de decisión— donde **cada uno corrige los errores del anterior**.

🎬 *Fila de árboles; cada uno parchea la zona roja del previo.* *Aparece* $\hat{y} = \sum_{t=1}^{T} f_t(x)$.

🎙️ La predicción final es **la suma de todos los árboles**. Eso dice la fórmula: y-con-sombrerito es el total de lo que vota cada árbol.

🎬 *Alerta "FUGA DE INFORMACIÓN". Un tubo lleva la respuesta a la pregunta; unas tijeras lo cortan.*

🎙️ Pero cazamos una trampa. Una característica —la tasa de cambios— predecía "gana cambiando" demasiado bien... porque **ambas se calculan contando lo mismo**. Era como adivinar si alguien aprobó usando su nota final. La quitamos. Las cifras que mostramos son **sin** esa trampa.

🎬 *Dos barras: 54 % base vs 59 % modelo. Mostrar Figura 6 (importancia), resaltar "número de turnos".*

![Importancia de características XGBoost](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/feature_importance.png)

🎙️ Limpio, el modelo acierta el **59 %**, apenas cinco puntos sobre el azar. Y eso es **el hallazgo**: el equipo casi no delata el estilo. Es más, lo único informativo es **cuántos turnos duró**... que solo se sabe cuando la batalla ya terminó. O sea, no predice: **explica en retrospectiva**. Misma conclusión que antes, por otro camino: **el estilo se decide jugando, no armando el equipo**.

---

## 4 · Técnica 3: Q-Learning (jugar) — ⏱️ 3:50–5:15

🎬 *"Detective 3 — Reforzar". Una libreta-tabla gigante: filas = situaciones, columnas = acciones.*

🎙️ Tercera y más ambiciosa: **¿puede una máquina aprender a jugar sola, sin que le enseñen estrategia?** Esto es **refuerzo**: como entrenar un perro, premio y castigo.

🎙️ El **Q-Learning** llena una libreta. Cada casilla guarda "qué tan buena fue esta acción en esta situación". Empieza vacía; el agente prueba, ve el resultado y **anota**.

🎬 *Aparece la fórmula, resaltando 3 trozos al narrar:*

$$Q(s,a) \leftarrow Q(s,a) + \alpha \left[r + \gamma \max_{a'} Q(s', a') - Q(s,a)\right]$$

🎙️ En una frase: **ajusta tu opinión sobre la jugada un poquito, en dirección a la sorpresa, contando el premio de ahora y las puertas que abre después.** La `r` es el premio inmediato; la parte de `max Q` es el mejor futuro posible; alfa y gamma solo gradúan cuánto aprendes y cuánto te importa el futuro.

🎬 *Tabla de recompensas: +1,5 daño · −1,0 daño recibido · ±0,5 cambio · ±10 ganar/perder. Curva de "azar" cayendo de 100 % a 5 %.*

🎙️ Le dimos ocho datos clave —vida, ventaja de tipo, velocidad— los mismos del inicio. Y lo dejamos empezar **explorando al azar** para, poco a poco, confiar en lo aprendido.

🎬 *Mostrar Figura 9 (curva de aprendizaje) animándose. 76,6 % grande.*

![Curva de aprendizaje Q-Learning](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/rl_learning_curve.png)

🎙️ Juega 2.000 partidas contra un rival que mueve al azar. Arranca perdiendo... cruza la línea... y se estabiliza en **76,6 % de victorias**. Aprendió de cero, sin una sola regla de estrategia.

🎬 *La tabla de 27.648 filas se desvanece; quedan ~2.000 iluminadas.*

🎙️ Y lo elegante: de 27.648 situaciones posibles solo visitó **2.039**, las que de verdad ocurren. Como es una tabla, la **abrimos y la leemos**: cambia ante desventaja de tipo, ataca cuando golpea primero. Táctica real, verificable con los ojos.

---

## 5 · Cierre — ⏱️ 5:15–6:00

🎬 *Tabla comparativa, tres columnas:*

| | 🔍 K-Means | 🎯 XGBoost | 🤖 Q-Learning |
|---|---|---|---|
| Hace | Describe | Explica | Actúa |
| Resultado | 2 arquetipos | 59 % | 76,6 % |

🎙️ Tres técnicas, tres miradas: una **describe**, otra **explica**, otra **actúa**. Las tres se apoyan en los mismos ejes del juego —velocidad, tipo y vida— y dos de ellas llegaron, por caminos distintos, a la misma idea: **importa cómo juegas, no el equipo que te toca**.

🎬 *Texto: "Los números son modestos. A propósito."*

🎙️ Nuestros números son modestos, y no lo escondemos: hallamos una trampa y la quitamos, vimos grupos débiles y dijimos por qué. Porque un resultado **bien entendido** vale más que un número espectacular que no puedes explicar.

🎬 *Fundido a negro: título del proyecto y nombres.*

🎙️ Cuatrocientas ochenta y cuatro mil batallas para aprender algo que ninguna pantalla llamativa te da: **a veces lo más valioso que enseña una máquina es lo poco que se podía saber de antemano.**

---

💡 *Cronometraje: leído a ritmo natural con pausas para los visuales, cae en 5:50–6:00. Si sobra tiempo, alargar la animación de la curva de aprendizaje (sección 4). Si falta, recortar la analogía del perro y la del restaurante.*
