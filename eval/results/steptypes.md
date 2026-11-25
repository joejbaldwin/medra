# Clasificador de tipo de paso (2026-11-25, commit 3e1e1d8)

## Tipo de paso (en las fronteras de la referencia)

Clasificador: TF-IDF (palabras iniciales, palabras del tramo, marcador del léxico, primer tramo) y regresión logística; C = 1, pesos de clase balanced, elegidos por validación cruzada agrupada por traza en train. Datos: las 302 trazas anotadas (las 30 de evaluación y las de eval/train/), divididas en train (241 trazas, 4337 pasos) y test (61 trazas, 1104 pasos): 80/20, semilla 0, estratificado por modelo de origen. Regla de marcadores: el tipo del marcador que abre el tramo, «development» si no hay (la primera versión de MeDRA).

| Método | Test: exactitud | Test: F1 macro |
|---|---|---|
| Clasificador | 0.68 | 0.62 |
| Regla de marcadores | 0.32 | 0.29 |
| Siempre «development» | 0.19 | 0.05 |

Validación cruzada de 10 particiones sobre las 302 trazas, agrupada por traza (5441 pasos): clasificador 0.71 de exactitud y 0.66 de F1 macro; regla 0.35 y 0.31; siempre «development» 0.18 y 0.05.

Test por origen:

| Origen | Trazas | Pasos | Clasificador: exactitud | F1 macro | Regla: exactitud | F1 macro |
|---|---|---|---|---|---|---|
| DeepSeek | 29 | 605 | 0.62 | 0.58 | 0.23 | 0.16 |
| OpenThoughts (DeepSeek-R1) | 32 | 499 | 0.75 | 0.67 | 0.43 | 0.40 |

Curva de aprendizaje (test, entrenando con subconjuntos aleatorios de train):

| Trazas de entrenamiento | Pasos | Exactitud | F1 macro |
|---|---|---|---|
| 25 | 464 | 0.61 | 0.53 |
| 50 | 864 | 0.63 | 0.57 |
| 100 | 1779 | 0.65 | 0.58 |
| 150 | 2695 | 0.67 | 0.61 |
| 200 | 3601 | 0.67 | 0.61 |
| 241 | 4337 | 0.68 | 0.62 |

Por tipo, en test:

| Tipo | Clasificador P | R | F1 | Regla F1 | Casos |
|---|---|---|---|---|---|
| alternative | 0.46 | 0.56 | 0.51 | 0.16 | 146 |
| backtrack | 0.29 | 0.34 | 0.31 | 0.20 | 29 |
| conclusion | 0.83 | 0.72 | 0.78 | 0.54 | 258 |
| development | 0.57 | 0.73 | 0.64 | 0.32 | 207 |
| planning | 0.77 | 0.71 | 0.74 | 0.26 | 109 |
| verification | 0.82 | 0.69 | 0.75 | 0.23 | 355 |

Confusión del clasificador en test (referencia → predicción): alternative->alternative: 82, alternative->backtrack: 4, alternative->conclusion: 6, alternative->development: 28, alternative->planning: 7, alternative->verification: 19, backtrack->alternative: 6, backtrack->backtrack: 10, backtrack->conclusion: 1, backtrack->development: 7, backtrack->verification: 5, conclusion->alternative: 23, conclusion->backtrack: 3, conclusion->conclusion: 187, conclusion->development: 28, conclusion->planning: 8, conclusion->verification: 9, development->alternative: 18, development->backtrack: 4, development->conclusion: 15, development->development: 151, development->planning: 3, development->verification: 16, planning->alternative: 6, planning->conclusion: 11, planning->development: 9, planning->planning: 77, planning->verification: 6, verification->alternative: 43, verification->backtrack: 14, verification->conclusion: 4, verification->development: 44, verification->planning: 5, verification->verification: 245

## Selección en train (validación cruzada agrupada, 5 particiones)

| C | Pesos de clase | Exactitud | F1 macro |
|---|---|---|---|
| 0.3 | ninguno | 0.68 | 0.54 |
| 0.3 | balanced | 0.68 | 0.64 |
| 1 | ninguno | 0.71 | 0.59 |
| 1 | balanced | 0.71 | 0.67 |
| 3 | ninguno | 0.72 | 0.61 |
| 3 | balanced | 0.71 | 0.67 |
| 10 | ninguno | 0.72 | 0.63 |
| 10 | balanced | 0.71 | 0.66 |
| 30 | ninguno | 0.71 | 0.63 |
| 30 | balanced | 0.71 | 0.65 |
| 100 | ninguno | 0.71 | 0.63 |
| 100 | balanced | 0.70 | 0.64 |

## Rasgos con más peso (modelo entrenado en train)

o1: primera palabra; o: palabras iniciales; b: palabras del tramo; m: marcador del léxico.

- **alternative**: `b:maybe`, `o:if`, `b:could`, `o:maybe`, `b:alternatively`, `b:remainders`, `m:alternative`, `b:perhaps`
- **backtrack**: `b:wait`, `o1:wait`, `m:backtrack`, `o:no`, `o:wait_no`, `o:wait`, `o:earlier`, `o:not`
- **conclusion**: `b:answer`, `m:conclusion`, `b:final`, `o1:so`, `o:so`, `b:therefore`, `o:final`, `o:answer`
- **development**: `b:since`, `b:#`, `b:return`, `b:o`, `b:x`, `b:w`, `b:first`, `b:m`
- **planning**: `pos:first`, `b:need`, `o:need`, `b:find`, `o:we_need`, `o1:okay`, `o:okay`, `o1:we`
- **verification**: `b:yes`, `b:good`, `b:check`, `o:check`, `b:correct`, `b:#`, `m:verification`, `o:but_wait`

## Modelo instalado

Entrenado en 300 trazas (todas salvo las dos de la prueba con usuarios: en-log-pets, en-log-knights), 5415 pasos, con los ajustes elegidos en train. Archivo: backend/medra/mining/models/step_types_en.json.

## Trazas de test

ds-cod-04, ds-cod-10, ds-cod-26, ds-cod-35, ds-cod-37, ds-cod-38, ds-cod-39, ds-log-01, ds-log-04, ds-log-07, ds-log-29, ds-log-31, ds-log-33, ds-log-36, ds-log-49, ds-mat-01, ds-mat-12, ds-mat-20, ds-mat-22, ds-mat-33, ds-mat-34, ds-mat-38, ds-mat-40, ds-mat-48, ds-mat-49, ds-mat-50, ds-sci-10, ds-sci-13, en-log-liars, ot-103583, ot-107866, ot-110833, ot-111903, ot-12638, ot-24436, ot-32416, ot-34344, ot-39482, ot-48195, ot-48760, ot-49041, ot-49802, ot-59317, ot-60145, ot-70628, ot-72092, ot-78941, ot-80204, ot-88785, ot-89808, ot-89840, ot-89845, ot-89862, ot-94355, ot-95220, ot-95243, ot-98747, ot-98751, ot-98760, ot-log-board, ot-sci-enthalpy
