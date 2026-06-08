# Guión completo — "¿Puede una máquina aprender a jugar Pokémon sola?"

> **Formato:** narración estilo Veritasium. Narrador único.
> **Idioma:** 100 % español.
> **Objetivo:** que cualquier persona, sin saber nada de programación ni de estadística, entienda *exactamente* qué hicimos y por qué.
> **Convenciones de este guión:**
> - 🎙️ = texto que se narra en voz alta.
> - 🎬 = sugerencia de apoyo visual (qué se ve en pantalla mientras se narra).
> - 💡 = nota de producción o aclaración (no se narra).

---

## PARTE 0 — El gancho (≈1 min)

🎬 *Pantalla negra. Aparece un combate de Pokémon Showdown en marcha: dos equipos, barras de vida, un turno resolviéndose en cámara lenta.*

🎙️ Cada vez que dos personas juegan una partida de Pokémon online, pasa algo que casi nadie nota: la partida queda **grabada**. Cada movimiento, cada cambio, cada decisión... guardada para siempre en un archivo de texto público.

🎙️ Eso significa que existe un registro gigantesco de seres humanos tomando decisiones bajo presión, sin saber qué va a hacer su rival. Y cuando digo gigantesco, hablo de **treinta y un millones** de partidas.

🎬 *Contador subiendo rápido hasta "31.700.000 partidas".*

🎙️ Nosotros tomamos un pedazo de ese tesoro —**484.130 batallas reales**— y nos hicimos tres preguntas muy distintas:

🎬 *Tres tarjetas aparecen una por una:*
- *"¿Hay tipos de equipos? 🔍"*
- *"¿Se puede predecir cómo gana alguien? 🎯"*
- *"¿Puede una máquina aprender a jugar... sola? 🤖"*

🎙️ Para responder cada una usamos una rama distinta del aprendizaje de máquinas. Y al final, las tres se conectan de una forma elegante. Vamos por partes.

💡 *Tono: curiosidad, no épica. Veritasium promete una sorpresa y la sostiene. La nuestra: "los números salieron modestos, y eso es justo lo interesante".*

---

## PARTE 1 — ¿Qué es "aprendizaje de máquinas"? (≈1.5 min)

🎬 *Animación simple: a la izquierda, programación clásica. A la derecha, machine learning.*

🎙️ Antes de nada, aclaremos la palabra de moda: *machine learning*, o aprendizaje de máquinas.

🎙️ En la programación normal, tú le das a la computadora **reglas** y ella te da **respuestas**. Le dices "si el Pokémon enemigo es de fuego, usa un ataque de agua", y obedece.

🎬 *Diagrama: REGLAS + DATOS → RESPUESTAS.*

🎙️ En el aprendizaje de máquinas, le das **datos** y **respuestas**, y ella descubre **las reglas sola**. Le muestras mil batallas ganadas y mil perdidas, y ella deduce qué tienen en común las victorias.

🎬 *Diagrama: DATOS + RESPUESTAS → REGLAS. Las flechas literalmente se invierten respecto al anterior.*

🎙️ Eso es todo. No hay magia. Hay un programa buscando patrones en montañas de ejemplos.

🎙️ Y hay tres grandes familias de este aprendizaje. Resulta que nosotros usamos **una de cada familia**. Piénsalo como tres detectives con métodos opuestos investigando el mismo crimen.

🎬 *Tres siluetas de detective con etiquetas:*
- *Detective 1 — "Agrupar": no sabe qué busca, ordena por parecido.*
- *Detective 2 — "Clasificar": tiene ejemplos resueltos, aprende a etiquetar.*
- *Detective 3 — "Reforzar": aprende a base de premios y castigos.*

🎙️ Guarda estas tres caras. Volveremos a ellas.

---

## PARTE 2 — El terreno de juego: Pokémon como problema matemático (≈1.5 min)

🎬 *Pantalla dividida: a la izquierda el juego bonito, a la derecha los mismos datos como números fríos en una tabla.*

🎙️ ¿Por qué Pokémon? Porque debajo de las criaturas adorables hay un problema matemático casi perfecto.

🎙️ Cada Pokémon tiene seis estadísticas: **vida**, **ataque**, **defensa**, **ataque especial**, **defensa especial** y **velocidad**. Tiene uno o dos **tipos** —fuego, agua, planta, y así hasta dieciocho— y hasta cuatro movimientos.

🎬 *Ficha de un Pokémon resaltando esos seis números y los tipos.*

🎙️ Y dos cosas mandan en cada combate. La primera: la **ventaja de tipo**. Un ataque de agua le hace el **doble** de daño al fuego, pero la **mitad** a la planta.

🎬 *Triángulo clásico agua → fuego → planta → agua, con los multiplicadores ×2 y ÷2 animados.*

🎙️ La segunda: la **velocidad**. El Pokémon más rápido golpea primero. Y golpear primero puede significar noquear al rival **antes** de que él te toque siquiera.

🎙️ Hay un detalle más, que viene del formato que elegimos. Se llama **Gen 8 Random Battle**. La palabra clave es *random*: a cada jugador le reparten seis Pokémon **al azar**. Nadie arma su equipo.

🎬 *Animación de cartas barajándose y repartiéndose.*

🎙️ ¿Por qué esto es genial para nosotros? Porque si los equipos son aleatorios, **todo el mérito está en cómo juegas**, no en cómo armaste el equipo. Aísla la habilidad de la decisión. Acuérdate de esto, porque será la clave para entender por qué uno de nuestros resultados salió "decepcionante"... y por qué esa decepción es en realidad el hallazgo.

---

## PARTE 3 — De texto crudo a números: el preprocesamiento (≈2 min)

🎬 *Aparece un bloque de texto feo, lleno de símbolos `|move|...|switch|...`. Es un log real de batalla.*

🎙️ Aquí viene la parte que nadie muestra en los videos bonitos, pero que es el 80 % del trabajo real: **limpiar los datos**.

🎙️ Cada batalla viene como esto. Un muro de texto donde cada línea es un evento: "este Pokémon usó este movimiento", "este jugador cambió", "este recibió daño". Para una computadora, esto no significa nada todavía. Es solo texto.

🎬 *Zoom a una línea tipo `|move|p1a: Pikachu|Thunderbolt`. Se traduce en pantalla a "Jugador 1, Pikachu, usó Rayo".*

🎙️ Nuestro trabajo fue escribir un programa que **lee** estos muros de texto, batalla por batalla, y extrae los hechos que importan:

🎬 *Lista que se va llenando con checkmarks:*
- *✓ ¿Qué seis Pokémon tenía cada equipo?*
- *✓ ¿Quién ganó?*
- *✓ ¿Cuántos turnos duró?*
- *✓ ¿Cuántas veces atacó? ¿Cuántas veces cambió?*

🎙️ Pero los nombres de los Pokémon no nos dicen sus estadísticas. Así que cruzamos cada equipo con una base de datos de stats —de un servicio llamado PokeAPI— y calculamos los **promedios del equipo**: su vida promedio, su velocidad promedio, y así.

🎬 *Animación: seis fichas de Pokémon entran a una "licuadora" y sale una sola ficha con los promedios.*

🎙️ Y de ahí construimos características más interesantes. Por ejemplo:

🎬 *Tarjetas con icono:*
- *`diversidad de tipos` → ¿cuántos tipos distintos cubre el equipo?*
- *`ratio de velocidad` → ¿quién controla el ritmo, yo o el rival?*
- *`tasa de cambios` → ¿con qué frecuencia cambia de Pokémon el ganador?*

🎙️ Cuatrocientas ochenta y cuatro mil batallas, convertidas de texto caótico a una tabla ordenada de números. **Ahora** sí, las máquinas pueden trabajar.

🎬 *El muro de texto feo se transforma con un "barrido" en una tabla limpia de Excel.*

💡 *Apoyo visual recomendado: mostrar la Figura 1 (duración de batallas, mediana de 20 turnos) y la Figura 2 (Pokémon más frecuentes). Refuerzan que son datos reales.*

![Duración de batallas](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/battle_duration.png)

![Top 20 Pokémon más frecuentes](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/top_pokemon.png)

🎙️ Una curiosidad de los datos: la mayoría de las batallas duran entre diez y treinta turnos, con una mediana de veinte. Y si te preguntas qué Pokémon aparece más, es **Toxapex** —una pared defensiva clásica del formato.

---

## PARTE 4 — TÉCNICA 1: Agrupar con K-Means (≈3 min)

### 4.1 La pregunta

🎬 *Vuelve el "Detective 1 — Agrupar".*

🎙️ Primera técnica. Primera pregunta: **¿existen tipos de equipos?** ¿Hay equipos claramente "ofensivos" y otros claramente "defensivos"? ¿O todos son básicamente iguales?

🎙️ Aquí no tenemos respuestas. No le decimos a la máquina qué buscar. Solo le damos los equipos y le pedimos: **agrúpalos por parecido**. Esto se llama aprendizaje **no supervisado** —sin supervisor, sin respuestas correctas.

### 4.2 La intuición de K-Means

🎬 *Animación: nube de puntos dispersos en un plano. Cada punto es un equipo.*

🎙️ El algoritmo se llama **K-Means**, "K-promedios", y es sorprendentemente sencillo. Imagina cada equipo como un punto en un mapa. Equipos parecidos quedan cerca; equipos distintos, lejos.

🎙️ Le decimos: "encuentra **dos** grupos". El algoritmo hace esto:

🎬 *Animación paso a paso, narrada:*

🎙️ Uno: pone dos banderas al azar en el mapa. Son los centros provisionales.

🎬 *Dos banderas caen en posiciones aleatorias.*

🎙️ Dos: cada punto se une a la bandera más cercana. Se forman dos bandos.

🎬 *Los puntos se colorean según su bandera más cercana.*

🎙️ Tres: cada bandera se mueve al **centro exacto** de su bando.

🎬 *Las banderas se deslizan al centro de masa de su color.*

🎙️ Cuatro: y repetimos. Los puntos vuelven a elegir bandera, las banderas vuelven a recentrarse... una y otra vez, hasta que ya nada se mueve. Ahí convergió.

🎬 *El ciclo se repite acelerado hasta estabilizarse.*

### 4.3 La ecuación, desmenuzada

🎬 *Aparece la fórmula grande:* $J = \sum_k \sum_{x \in C_k} \|x - \mu_k\|^2$

🎙️ Esto que parece intimidante dice algo muy simple. Léelo de adentro hacia afuera.

🎬 *Se van resaltando los pedazos uno por uno mientras se narran.*

🎙️ Esta parte —`x − μ`— es la **distancia** entre un equipo y el centro de su grupo. Qué tan lejos está de su bandera.

🎙️ El cuadradito significa "elévalo al cuadrado", un truco para que todas las distancias sean positivas y las grandes pesen más.

🎙️ Las dos sumas grandes —los símbolos Σ— solo dicen: "haz eso para **todos** los puntos, de **todos** los grupos, y súmalo".

🎙️ Y la `J` es la cuenta total. Es el "desorden" total: qué tan lejos está cada equipo de su centro. **K-Means busca acomodar las banderas para que ese número sea lo más pequeño posible.** Grupos compactos, puntos cerquita de su bandera. Eso es todo.

### 4.4 ¿Cuántos grupos? El "codo" y la "silueta"

🎙️ Pero, ¿cómo sabemos que dos grupos es lo correcto? ¿Por qué no tres, o cinco?

🎙️ Probamos desde dos hasta diez grupos y medimos la calidad con un número llamado **silueta**.

🎬 *Aparece:* $s(i) = \dfrac{b(i) - a(i)}{\max(a(i), b(i))}$

🎙️ Otra fórmula que se desarma fácil. Para cada equipo preguntamos dos cosas:

🎬 *Diagrama: un punto, una flecha corta a su propio grupo (a), una flecha larga al grupo vecino (b).*

🎙️ La `a` es: ¿qué tan cerca estoy de mi propia gente? La `b` es: ¿qué tan lejos estoy del grupo de al lado?

🎙️ Si estoy pegadito a mi grupo y lejísimos del otro, soy un miembro feliz y bien clasificado: la silueta se acerca a **uno**. Si estoy justo en la frontera, sin saber a qué grupo pertenezco, la silueta se acerca a **cero**.

### 4.5 El resultado honesto

🎬 *Mostrar Figura 3 (curva del codo / silueta) y Figura 4 (clusters en PCA).*

![Curva del codo y silueta por K](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/elbow_curve.png)

🎙️ ¿El resultado? La mejor opción fueron **dos grupos**, con una silueta de... **0,136**.

🎬 *El número 0,136 aparece grande. Una barra que va de 0 a 1, y el marcador queda pegado al inicio.*

🎙️ Cero coma trece. Eso está **mucho** más cerca de cero que de uno. Traducción: los grupos existen, pero apenas se distinguen. Están casi pegados, solapados.

🎙️ ¿Es esto un fracaso? **No.** Es exactamente lo que la lógica predecía. ¿Recuerdas que los equipos se reparten **al azar**? Pues claro que todos se parecen: ¡salen de la misma bolsa! Sería sospechoso encontrar grupos perfectamente separados.

![Arquetipos de equipo en PCA](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/clusters_pca.png)

🎬 *Mostrar Figura 5 (radar de los dos centroides).*

![Radar de centroides](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/clusters_radar.png)

🎙️ Aun así, los dos centros —el corazón de cada grupo— dibujan dos perfiles reconocibles: uno con más **velocidad y ataque**, el otro con más **vida y defensa**. El clásico equipo agresivo contra el equipo resistente. Débilmente separados, pero ahí están.

💡 *Nota de honestidad metodológica (parte del espíritu del proyecto): no inflamos el resultado. La silueta baja se presenta como confirmación de una hipótesis, no como derrota.*

---

## PARTE 5 — TÉCNICA 2: Predecir con XGBoost (≈3.5 min)

### 5.1 La pregunta

🎬 *Vuelve el "Detective 2 — Clasificar".*

🎙️ Segunda técnica. Ahora sí tenemos respuestas, y queremos que la máquina aprenda a predecir. Esto es aprendizaje **supervisado**: hay un "profesor" con las respuestas correctas.

🎙️ La pregunta: **¿el perfil de un equipo delata cómo va a ganar?** Es decir, mirando solo las estadísticas del equipo, ¿podemos adivinar **el estilo** con el que ganará?

🎙️ Definimos cuatro estilos de victoria:

🎬 *Cuatro iconos:*
- *💥 Físico — gana a punta de golpes físicos.*
- *✨ Especial — gana con ataques especiales (energía, elementos).*
- *🌀 Estado — gana envenenando, durmiendo, debilitando.*
- *🔄 Cambio — gana cambiando de Pokémon constantemente.*

### 5.2 La intuición de los árboles de decisión

🎬 *Aparece un árbol de decisión simple, tipo diagrama de "sí/no".*

🎙️ La herramienta se llama **XGBoost**, y para entenderla hay que empezar por el **árbol de decisión**, que es básicamente un cuestionario de sí o no.

🎬 *Árbol animado:* *"¿Velocidad promedio mayor a 100?" → sí/no → "¿Diversidad de tipos alta?" → sí/no → predicción.*

🎙️ "¿El equipo es rápido? Sí. ¿Tiene mucha variedad de tipos? No. Entonces... probablemente gana con ataques físicos." Pregunta tras pregunta, hasta una conclusión. Un solo árbol es simple y suele equivocarse.

### 5.3 La idea genial: muchos árboles que se corrigen

🎬 *Un árbol. Luego otro al lado. Luego otro. Una fila creciente.*

🎙️ Aquí está el truco de XGBoost. En vez de un árbol, construye **cientos**, pero no cualquier cientos: cada árbol nuevo nace para **corregir los errores del anterior**.

🎙️ El primero hace su mejor intento. El segundo mira en qué se equivocó el primero y se especializa **justo ahí**. El tercero corrige lo que aún fallaba... y así sucesivamente. Es como un equipo de revisores donde cada uno se enfoca en los errores que dejaron los demás.

🎬 *Animación: predicción imperfecta → un árbol "parchea" la zona roja de error → la zona se vuelve verde → siguiente árbol.*

🎙️ Esto se llama *gradient boosting*, "potenciación por gradiente", y la predicción final es simplemente **la suma de todos los árboles**:

🎬 *Aparece:* $\hat{y} = \sum_{t=1}^{T} f_t(x)$

🎙️ La `ŷ` —"y con sombrerito"— es la predicción final. Cada `f` es un árbol. El símbolo Σ dice "súmalos todos". Eso es la fórmula entera: la respuesta del bosque es la suma de las respuestas de cada árbol.

🎙️ Y para que no se vuelva un monstruo que memoriza en vez de aprender, hay una segunda fórmula con un freno:

🎬 *Aparece:* $\mathcal{L}^{(t)} = \sum_i \ell\!\left(y_i,\; \hat{y}_i^{(t-1)} + f_t(x_i)\right) + \Omega(f_t)$

🎙️ No te asustes. Solo dice dos cosas. La primera parte mide **cuánto se equivoca** el modelo todavía. La última parte —esa omega, Ω— es un **castigo por complejidad**: penaliza a los árboles que se vuelven demasiado enrevesados. Es como decirle a un estudiante: "sí, acierta, pero no te memorices el examen". Ese balance entre acertar y mantenerse simple es lo que evita que el modelo se **sobreajuste**.

### 5.4 Una trampa que tuvimos que cazar: la fuga de información

🎬 *Señal de alerta. Texto: "DATA LEAKAGE / FUGA DE INFORMACIÓN".*

🎙️ Y aquí viene la parte de la que estamos más orgullosos, porque es el tipo de error que arruina silenciosamente proyectos de verdad.

🎙️ Teníamos una característica llamada `tasa de cambios`: con qué frecuencia el ganador cambia de Pokémon. Al principio, el modelo predecía la categoría "gana cambiando" **espectacularmente bien**. Sospechosamente bien.

🎬 *Gráfico de "rendimiento" altísimo, con un signo de interrogación parpadeando.*

🎙️ ¿Por qué sospechoso? Porque era hacer **trampa sin querer**. Piénsalo: la categoría "gana cambiando" se calcula contando los cambios del ganador. Y la "tasa de cambios" **también** se calcula contando los cambios del ganador.

🎙️ Le estábamos preguntando "¿este gana cambiando?" mientras le dábamos como pista... ¡el número de veces que cambió! Es como predecir si alguien aprobó el examen usando como dato su nota final. La respuesta estaba escondida dentro de la pregunta. Eso se llama **fuga de información**.

🎬 *Animación: la "respuesta" se filtra por un tubo y entra directo a la "pregunta". Luego se corta el tubo con unas tijeras.*

🎙️ Así que la eliminamos. Y el rendimiento de "gana cambiando" se **desplomó**: de casi perfecto a apenas mejor que adivinar. Eso confirmó que **todo** su poder venía de la trampa, no de la batalla real. Doloroso, pero honesto. Las cifras que mostramos son **sin** esa trampa.

### 5.5 El resultado y la verdadera sorpresa

🎬 *Mostrar Figura 7 (matriz de confusión) y Figura 6 (importancia de características).*

![Matriz de confusión normalizada](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/confusion_matrix.png)

🎙️ Con todo limpio, el modelo acierta el **59 %** de las veces. La línea base —simplemente adivinar siempre el estilo más común— acierta el 54 %. Le ganamos por **cinco puntos**.

🎬 *Dos barras: 54 % base vs 59 % modelo. La diferencia es pequeña y honesta.*

🎙️ Cinco puntos. No es impresionante. Y aquí está la sorpresa, el verdadero hallazgo: **eso es interesantísimo.**

🎙️ Porque significa que el perfil estadístico de un equipo **casi no delata** cómo va a ganar. ¿Recuerdas la conclusión del K-Means —que el estilo se decide jugando, no armando el equipo? Pues esta segunda técnica, por un camino completamente distinto, dice **lo mismo**.

🎬 *Mostrar Figura 6 con el ranking de importancia resaltado.*

![Importancia de características XGBoost](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/feature_importance.png)

🎙️ Y hay un detalle revelador. La característica más importante del modelo resultó ser `número de turnos` —cuánto duró la batalla. Pero piénsalo: ¡eso solo se sabe **cuando la batalla ya terminó**! Así que el modelo no está **prediciendo** desde el inicio; está **explicando en retrospectiva**, después de ver cómo se desarrolló el combate.

🎙️ Quita esas pistas dinámicas y deja solo el equipo en bruto, y el modelo apenas le gana al azar. La conclusión es contundente: **el estilo con que ganas no está escrito en tu equipo. Está escrito en cómo juegas.**

🎬 *Opcional, para los curiosos: mostrar Figura 8 (curvas ROC). Cada curva mide qué tan bien distingue el modelo una clase del resto: más arriba a la izquierda, mejor. Nota que `switch` (verde) es la más baja y `status` (azul) la más alta.*

![Curvas ROC por clase](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/roc_curves.png)

---

## PARTE 6 — TÉCNICA 3: Aprender jugando con Q-Learning (≈4 min)

### 6.1 La pregunta

🎬 *Vuelve el "Detective 3 — Reforzar".*

🎙️ Tercera y última técnica. La más ambiciosa. Hasta ahora la máquina **miraba** partidas terminadas. Ahora queremos que **juegue**.

🎙️ La pregunta: **¿puede una máquina aprender a jugar Pokémon por prueba y error, sin que nadie le enseñe las reglas de estrategia?** Sin ejemplos, sin profesor. Solo experiencia.

🎙️ Esto es aprendizaje por **refuerzo**, la tercera familia. La misma idea con la que entrenas a un perro: premio cuando hace bien, regaño cuando hace mal. Repite lo premiado, evita lo castigado.

### 6.2 La intuición: la libreta de experiencias

🎬 *Aparece una tabla/libreta gigante en blanco. Filas = situaciones. Columnas = acciones.*

🎙️ El algoritmo se llama **Q-Learning**, y su corazón es una simple **tabla**. Imagínala como la libreta de un jugador novato.

🎙️ En las filas, **todas las situaciones posibles** en las que te puedes encontrar. En las columnas, **todas las acciones** que puedes tomar. Y en cada casilla, un número: **"qué tan buena ha resultado esta acción en esta situación"**.

🎬 *Zoom a una casilla: situación "enemigo más rápido, le tengo ventaja de tipo", acción "atacar" → número subiendo.*

🎙️ Al principio, la libreta está vacía: todos ceros. El agente no tiene ni idea. Así que prueba cosas al azar, ve qué pasa, y **anota** en la casilla correspondiente: "ataqué aquí, me fue bien, +1". "Cambié allá, me fue mal, −1". Turno a turno, partida a partida, la libreta se va llenando de sabiduría.

### 6.3 La ecuación, desmenuzada de verdad

🎬 *Aparece la fórmula, que se irá iluminando por trozos:*

$$Q(s,a) \leftarrow Q(s,a) + \alpha \left[r + \gamma \max_{a'} Q(s', a') - Q(s,a)\right]$$

🎙️ Esta es **la** fórmula del aprendizaje por refuerzo. Da respeto, pero te juro que cuenta una historia simple. Vamos despacio.

🎬 *Resaltar `Q(s,a)`.*

🎙️ `Q(s,a)` es el número en una casilla: el valor de hacer la acción `a` en la situación `s`. Eso es lo que queremos mejorar.

🎬 *Resaltar la flecha `←`.*

🎙️ Esta flechita significa "actualiza", "reescribe la casilla con un valor mejor".

🎬 *Resaltar `r`.*

🎙️ La `r` es la **recompensa inmediata**: lo que acabo de ganar o perder por esa acción, ahora mismo.

🎬 *Resaltar `γ max Q(s', a')`.*

🎙️ Esta parte es la genialidad. `s'` es la **nueva** situación tras mi acción. Y `max Q(s', a')` es lo mejor que puedo hacer **desde ahí en adelante**. O sea: la acción no solo vale por lo de ahora, vale por las **puertas que abre** después.

🎬 *Resaltar la `γ` (gamma).*

🎙️ La `γ`, gamma, vale 0,9 y es el **factor de descuento**: cuánto me importa el futuro frente al presente. Cercano a uno = "pienso a largo plazo". El futuro vale, pero un poquito menos que el ahora.

🎬 *Resaltar `[... - Q(s,a)]` completo.*

🎙️ Y todo el corchete es la **sorpresa**: la diferencia entre lo que esperaba que pasara y lo que realmente pasó. Si fue mejor de lo esperado, sube la casilla. Si fue peor, bájala.

🎬 *Resaltar `α` (alpha).*

🎙️ Por último, `α`, alfa, vale 0,1 y es la **velocidad de aprendizaje**: cuánto le hago caso a cada nueva experiencia. Pequeña para no volverme loco con una sola partida con suerte.

🎙️ Junta todo y la frase es: **"ajusta tu opinión sobre esta jugada un poquito, en la dirección de la sorpresa que te acabas de llevar, contando tanto el premio de ahora como las oportunidades que abre para después."** Eso es Q-Learning. Toda la fórmula, en una frase.

### 6.4 Diseñar el mundo del agente

🎙️ Para que esto funcione, tuvimos que tomar tres decisiones de diseño.

🎙️ **Primera: ¿qué ve el agente?** No le dimos la pantalla entera —sería abrumador. Le dimos ocho datos clave que resumen cualquier turno:

🎬 *Lista con iconos:*
- *❤️ Mi vida y la del rival (en cuatro niveles: casi muerto, bajo, medio, sano).*
- *⚖️ ¿Tengo ventaja de tipo, desventaja, o ninguna?*
- *⚡ ¿Soy más rápido que el rival?*
- *🔢 ¿Cuántos Pokémon vivos quedan de cada lado?*
- *🎮 ¿Cuántos movimientos tengo? ¿Puedo cambiar?*

🎙️ Fíjate que estos son **los mismos factores** que mencionamos al principio: velocidad y ventaja de tipo. No los sacamos de las técnicas anteriores; los sacamos de **cómo funciona el juego de verdad**.

🎙️ En teoría, combinando todos esos datos, hay **27.648** situaciones posibles. Suena enorme, pero ya verás el giro.

🎙️ **Segunda: ¿qué puede hacer?** Nueve acciones: cuatro movimientos y cinco posibles cambios de Pokémon.

🎙️ **Tercera, y la más delicada: ¿cómo lo premiamos?** Esto se llama **diseño de recompensas**, y es un arte. Si premias lo equivocado, el agente aprende a hacer trampa.

🎬 *Tabla de recompensas animada:*
- *+1,5 → por hacer daño.*
- *−1,0 → por recibir daño sin devolver.*
- *+0,5 → por cambiar inteligentemente (a una ventaja de tipo).*
- *−0,3 → por cambiar sin razón.*
- *±10 → el gran premio o castigo: ganar o perder la partida.*

### 6.5 El dilema explorar vs. explotar

🎬 *Una balanza: a un lado "probar cosas nuevas", al otro "usar lo que ya sé".*

🎙️ Hay un dilema profundo en todo esto, y lo vives tú también. ¿Vas siempre a tu restaurante favorito (lo seguro) o pruebas el nuevo de la esquina (lo arriesgado, que podría ser mejor)?

🎙️ Si el agente solo hace lo que ya sabe que funciona, nunca descubrirá algo mejor. Pero si solo experimenta, nunca aprovecha lo aprendido. Esto se llama **explorar contra explotar**.

🎙️ Nuestra solución: empezar **explorando al 100 %** —puro azar, pura curiosidad— y, lentamente, ir confiando cada vez más en lo aprendido. Al principio es un bebé tocando todo; al final, un jugador que ejecuta su estrategia.

🎬 *Curva descendente: "% de acciones al azar" cae de 100 % a 5 % a lo largo del entrenamiento.*

### 6.6 El resultado: ver a la máquina aprender

🎬 *Mostrar Figura 9 (curva de aprendizaje): la tasa de victorias subiendo, ε bajando.*

![Curva de aprendizaje Q-Learning](https://raw.githubusercontent.com/gabotachak/pokemon-agent/feature/gabotachak/outputs/figures/rl_learning_curve.png)

🎙️ Y ahora, lo mejor de todo: **verlo aprender en vivo.**

🎙️ El agente juega 2.000 partidas contra un rival que mueve **completamente al azar**. Mira la curva.

🎬 *La curva de victorias se anima de izquierda a derecha.*

🎙️ Al principio pierde. De hecho, arranca **por debajo del 50 %** —peor que el azar—, porque mientras explora a ciegas toma muchas acciones inválidas. Pero mira... a los cien episodios cruza la línea... y sigue subiendo... y se estabiliza en **76,6 % de victorias**.

🎬 *El número 76,6 % aparece grande.*

🎙️ Aprendió. De cero, sin que nadie le explicara una sola regla de estrategia, una máquina pasó de perder a ganar tres de cada cuatro partidas. Solo con premios, castigos y repetición.

### 6.7 El giro elegante: la libreta inteligente

🎬 *Vuelve la tabla de 27.648 filas. La mayoría se desvanecen, quedan pocas iluminadas.*

🎙️ ¿Y recuerdas las 27.648 situaciones posibles? Aquí está el detalle precioso. El agente, en 2.000 partidas, solo se encontró con **2.039** de ellas. Apenas un **7 %**.

🎙️ ¿Por qué? Porque la mayoría de esas combinaciones **nunca pasan en una partida real**. Y el agente no malgastó ni un segundo aprendiendo sobre situaciones imposibles. Solo estudió lo que de verdad ocurre.

🎙️ Y como es una simple tabla, podemos **abrirla y leerla**. A diferencia de una red neuronal, que es una caja negra, aquí podemos ver exactamente qué decidió el agente en cada situación. Y lo que vemos tiene sentido: **cambia de Pokémon cuando está en desventaja de tipo. Ataca cuando puede golpear primero.** Aprendió táctica real, y podemos verificarlo con nuestros propios ojos.

💡 *Apoyo visual potente: si hay tiempo, mostrar 2-3 filas reales de la tabla Q traducidas a lenguaje natural.*

---

## PARTE 7 — El cierre: cómo encajan las tres piezas (≈2 min)

🎬 *Las tres detectives del inicio vuelven, ahora lado a lado, mirando el mismo tablero.*

🎙️ Demos un paso atrás. Tres técnicas, tres familias del aprendizaje de máquinas, un mismo conjunto de batallas. ¿Qué encontramos?

🎬 *Tabla comparativa que se construye fila por fila (basada en la Tabla 4 del informe):*

| | 🔍 K-Means | 🎯 XGBoost | 🤖 Q-Learning |
|---|---|---|---|
| **Qué hace** | Describe | Explica | Actúa |
| **Cómo aprende** | Sin respuestas | Con respuestas | Con premios |
| **Resultado** | 2 arquetipos | 59 % acierto | 76,6 % victorias |
| **¿Se puede leer?** | Sí | Más o menos | Sí |

🎙️ La primera **describe**: hay dos tipos de equipo, ofensivo y defensivo, pero apenas distinguibles. La segunda **explica**: el equipo casi no delata el estilo de victoria. La tercera **actúa**: aprende a jugar desde cero.

🎙️ Y aquí está la conexión, lo que une todo el recorrido. Las tres se apoyan en **los mismos ejes**: velocidad, ventaja de tipo y vida. Los mismos factores que dominan el juego de verdad. Tres miradas, tres métodos opuestos, un mismo corazón.

🎙️ Y dos de ellas —el agrupamiento y la predicción— llegaron por caminos separados a la **misma conclusión**: en batallas aleatorias, lo que importa no es el equipo que te toca, sino **cómo lo juegas**.

### 7.1 La honestidad como resultado

🎬 *Texto en pantalla: "Los números son modestos. A propósito."*

🎙️ Termino con algo poco habitual en estos videos. Nuestros números son **modestos**. Una separación de grupos débil. Una predicción cinco puntos sobre el azar. Un agente que solo le gana a un rival que juega al azar.

🎙️ Y no lo escondemos. Al contrario: lo elegimos así. Porque un resultado modesto y **bien entendido** vale más que un número espectacular que no puedes explicar —o que, como vimos con la fuga de información, esconde una trampa.

🎙️ Encontramos una trampa y la quitamos. Vimos grupos débiles y dijimos por qué. Medimos al agente contra una vara baja y lo admitimos. Eso —entender de verdad lo que hiciste— es, al final, de lo que se trata el aprendizaje de máquinas.

🎬 *Fundido a negro. Título del proyecto y nombres de los integrantes.*

🎙️ Cuatrocientas ochenta y cuatro mil batallas. Tres preguntas. Una conclusión que ninguna pantalla llamativa puede darte: **a veces, lo más valioso que aprende una máquina es enseñarte lo poco que se podía saber de antemano.**

---

## Apéndice — Mapa de figuras para producción

| Momento del guión | Figura | Archivo |
|---|---|---|
| Parte 3 (datos reales) | Duración de batallas | `outputs/figures/battle_duration.png` |
| Parte 3 (datos reales) | Pokémon más frecuentes | `outputs/figures/top_pokemon.png` |
| Parte 4.4 | Codo / silueta | `outputs/figures/elbow_curve.png` |
| Parte 4.5 | Clusters en PCA | `outputs/figures/clusters_pca.png` |
| Parte 4.5 | Radar de centroides | `outputs/figures/clusters_radar.png` |
| Parte 5.5 | Importancia de características | `outputs/figures/feature_importance.png` |
| Parte 5.5 | Matriz de confusión | `outputs/figures/confusion_matrix.png` |
| Parte 5 (opcional) | Curvas ROC | `outputs/figures/roc_curves.png` |
| Parte 6.6 | Curva de aprendizaje RL | `outputs/figures/rl_learning_curve.png` |

💡 *Duración total estimada narrando con pausas: ~20-22 min. Para la versión de 6 minutos del entregable, ver `script_summary.md`.*
