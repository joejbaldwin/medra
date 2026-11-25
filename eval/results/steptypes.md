# Clasificador de tipo de paso (2026-11-25, commit 1fd3a99)

## Tipo de paso (en las fronteras de la referencia)

Clasificador: TF-IDF (palabras iniciales, palabras del tramo, marcador del léxico, primer tramo) y regresión logística, C = 1, pesos de clase balanced (elegidos por validación cruzada agrupada por traza en dev, 257 pasos). Regla: el marcador que abre el tramo, «development» si no hay.

| Método | Test: exactitud | Test: F1 macro | Dejar-una-traza-fuera: exactitud | F1 macro |
|---|---|---|---|---|
| Clasificador | 0.61 | 0.57 | 0.61 | 0.48 |
| Regla de marcadores | 0.28 | 0.25 | 0.28 | 0.20 |
| Siempre «development» | 0.22 | 0.07 | 0.23 | 0.06 |

Test: 161 pasos. Dejar-una-traza-fuera: 418 pasos (la regla y la línea base no se entrenan: son las mismas trazas).

Por tipo, en test:

| Tipo | Clasificador P | R | F1 | Regla P | R | F1 | Casos |
|---|---|---|---|---|---|---|---|
| alternative | 0.27 | 0.27 | 0.27 | 0.60 | 0.20 | 0.30 | 15 |
| conclusion | 0.71 | 0.77 | 0.74 | 0.55 | 0.19 | 0.29 | 31 |
| development | 0.53 | 0.53 | 0.53 | 0.24 | 0.78 | 0.37 | 36 |
| planning | 0.62 | 0.70 | 0.65 | 0.17 | 0.09 | 0.11 | 23 |
| verification | 0.70 | 0.62 | 0.66 | 1.00 | 0.11 | 0.19 | 56 |

Confusión del clasificador en test (referencia → predicción): alternative->alternative: 4, alternative->conclusion: 2, alternative->development: 3, alternative->verification: 6, conclusion->conclusion: 24, conclusion->development: 2, conclusion->planning: 4, conclusion->verification: 1, development->alternative: 4, development->conclusion: 3, development->development: 19, development->planning: 5, development->verification: 5, planning->conclusion: 3, planning->development: 1, planning->planning: 16, planning->verification: 3, verification->alternative: 7, verification->conclusion: 2, verification->development: 11, verification->planning: 1, verification->verification: 35

## Selección en dev (validación cruzada agrupada, 5 particiones)

| C | Pesos de clase | Exactitud | F1 macro |
|---|---|---|---|
| 0.3 | ninguno | 0.48 | 0.31 |
| 0.3 | balanced | 0.56 | 0.42 |
| 1 | ninguno | 0.56 | 0.39 |
| 1 | balanced | 0.60 | 0.44 |
| 3 | ninguno | 0.58 | 0.40 |
| 3 | balanced | 0.60 | 0.42 |
| 10 | ninguno | 0.57 | 0.40 |
| 10 | balanced | 0.60 | 0.42 |
| 30 | ninguno | 0.58 | 0.40 |
| 30 | balanced | 0.59 | 0.41 |
| 100 | ninguno | 0.58 | 0.40 |
| 100 | balanced | 0.58 | 0.41 |

## Rasgos con más peso (modelo entrenado en dev)

o1: primera palabra; o: palabras iniciales; b: palabras del tramo; m: marcador del léxico.

- **alternative**: `o:#_#`, `o:#`, `o:b_#`, `b:e`, `b:dollar`, `o:#_d`, `b:not`, `o:#_b`
- **backtrack**: `b:k`, `b:variables`, `b:interval`, `b:x`, `b:tuple`, `b:intervals`, `b:sorted`, `b:d`
- **conclusion**: `b:final`, `b:answer`, `o:final`, `m:conclusion`, `o1:let's`, `o1:so`, `b:include`, `o:answer`
- **development**: `b:w`, `b:s`, `b:h`, `b:return`, `b:def`, `b:since`, `b:l`, `b:stack`
- **planning**: `b:need`, `pos:first`, `o:we_need`, `o1:we`, `o:need_answer`, `o:need`, `o:we`, `b:solve`
- **verification**: `b:#`, `o:check`, `b:wait`, `b:yes`, `b:which`, `b:check`, `o:but`, `o1:but`

## Modelo instalado

Entrenado en 28 trazas (392 pasos), todas las anotadas salvo las dos de la prueba con usuarios (en-log-pets, en-log-knights), con los ajustes de dev. Archivo: backend/medra/mining/models/step_types_en.json.
