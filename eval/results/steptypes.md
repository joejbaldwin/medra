# Clasificador de tipo de paso (2026-11-25, commit d11d9eb)

## Tipo de paso (en las fronteras de la referencia)

Clasificador: TF-IDF (palabras iniciales, palabras del tramo, marcador del léxico, primer tramo) y regresión logística, entrenada con los 257 pasos de dev más 5023 pasos de 272 trazas anotadas solo para entrenar (eval/train/); C = 1, pesos de clase balanced, elegidos por validación cruzada agrupada por traza en dev. «Solo dev»: el mismo modelo entrenado solo con dev (C = 1, pesos balanced). Regla: el marcador que abre el tramo, «development» si no hay.

| Método | Test: exactitud | Test: F1 macro |
|---|---|---|
| Clasificador (dev + 272 trazas) | 0.71 | 0.69 |
| Clasificador (solo dev) | 0.61 | 0.57 |
| Regla de marcadores | 0.28 | 0.25 |
| Siempre «development» | 0.22 | 0.07 |

Test: 161 pasos de 11 trazas. Dejando una traza fuera (cada una de las 30 trazas de evaluación con un modelo entrenado con las otras 29 más las trazas extra; 418 pasos): clasificador 0.70 de exactitud y 0.62 de F1 macro; regla 0.28 y 0.20.

Curva de aprendizaje (test, con más trazas extra en el entrenamiento):

| Trazas extra | Pasos de entrenamiento | Exactitud | F1 macro |
|---|---|---|---|
| 0 | 257 | 0.61 | 0.57 |
| 25 | 663 | 0.64 | 0.63 |
| 50 | 1134 | 0.61 | 0.59 |
| 100 | 1965 | 0.68 | 0.66 |
| 150 | 2912 | 0.66 | 0.64 |
| 200 | 3863 | 0.66 | 0.64 |
| 272 | 5280 | 0.71 | 0.69 |

Por tipo, en test:

| Tipo | Clasificador P | R | F1 | Solo dev F1 | Regla F1 | Casos |
|---|---|---|---|---|---|---|
| alternative | 0.40 | 0.53 | 0.46 | 0.27 | 0.30 | 15 |
| conclusion | 0.86 | 0.81 | 0.83 | 0.74 | 0.29 | 31 |
| development | 0.60 | 0.69 | 0.64 | 0.53 | 0.37 | 36 |
| planning | 0.77 | 0.74 | 0.76 | 0.65 | 0.11 | 23 |
| verification | 0.83 | 0.70 | 0.76 | 0.66 | 0.19 | 56 |

Confusión del clasificador en test (referencia → predicción): alternative->alternative: 8, alternative->development: 2, alternative->verification: 5, conclusion->alternative: 1, conclusion->conclusion: 25, conclusion->development: 3, conclusion->planning: 2, development->alternative: 4, development->backtrack: 1, development->conclusion: 2, development->development: 25, development->planning: 2, development->verification: 2, planning->alternative: 1, planning->conclusion: 1, planning->development: 3, planning->planning: 17, planning->verification: 1, verification->alternative: 6, verification->conclusion: 1, verification->development: 9, verification->planning: 1, verification->verification: 39

## Selección en dev (validación cruzada agrupada, 5 particiones)

| C | Pesos de clase | Exactitud | F1 macro |
|---|---|---|---|
| 0.3 | ninguno | 0.70 | 0.53 |
| 0.3 | balanced | 0.68 | 0.61 |
| 1 | ninguno | 0.71 | 0.56 |
| 1 | balanced | 0.68 | 0.62 |
| 3 | ninguno | 0.69 | 0.55 |
| 3 | balanced | 0.70 | 0.57 |
| 10 | ninguno | 0.70 | 0.57 |
| 10 | balanced | 0.71 | 0.58 |
| 30 | ninguno | 0.68 | 0.54 |
| 30 | balanced | 0.69 | 0.55 |
| 100 | ninguno | 0.67 | 0.54 |
| 100 | balanced | 0.68 | 0.61 |

## Rasgos con más peso (modelo entrenado en dev + trazas extra)

o1: primera palabra; o: palabras iniciales; b: palabras del tramo; m: marcador del léxico.

- **alternative**: `b:maybe`, `o:if`, `b:could`, `o:maybe`, `b:alternatively`, `b:remainders`, `m:alternative`, `o1:if`
- **backtrack**: `b:wait`, `o1:wait`, `m:backtrack`, `o:no`, `o:wait_no`, `o:wait`, `b:earlier`, `o:earlier`
- **conclusion**: `b:answer`, `m:conclusion`, `b:final`, `o1:so`, `o:so`, `b:therefore`, `o:final`, `o1:therefore`
- **development**: `b:#`, `b:since`, `b:first`, `b:w`, `b:because`, `b:compute`, `b:now`, `b:x`
- **planning**: `b:need`, `pos:first`, `o:need`, `o:we_need`, `o1:okay`, `o:okay`, `b:find`, `o1:we`
- **verification**: `b:yes`, `b:good`, `o:check`, `b:correct`, `b:#`, `b:check`, `o:but_wait`, `b:verify`

## Modelo instalado

Entrenado en 28 trazas de evaluación (todas salvo las dos de la prueba con usuarios: en-log-pets, en-log-knights) más las 272 trazas extra, 5415 pasos, con los ajustes elegidos en dev. Archivo: backend/medra/mining/models/step_types_en.json.
