# Resultados de la evaluación de MeDRA

Generado con `python -m eval.run` el 2026-11-25, commit 3894b35. Anotaciones: 30 (30 corregidas). Trazas en inglés: 22 de DeepSeek y 8 de OpenThoughts (DeepSeek-R1).

Referencia: 13.9 tramos por traza, 9.4 frases por tramo de media. Tamaño fijo = 10 frases (media de la referencia en dev).

## Segmentación (todas las trazas)

| Método | Pk ↓ | WindowDiff ↓ | Precisión | Cobertura | F1 (±1 frase) | Tramos/traza |
|---|---|---|---|---|---|---|
| Tamaño fijo | 0.497 | 0.509 | 0.29 | 0.25 | 0.26 | 13.7 |
| Solo párrafos | 0.269 | 0.380 | 0.54 | 0.84 | 0.62 | 26.0 |
| Solo marcadores | 0.446 | 0.542 | 0.30 | 0.38 | 0.26 | 19.1 |
| TextTiling | 0.534 | 0.668 | 0.32 | 0.74 | 0.44 | 33.5 |
| MeDRA (por defecto) | 0.463 | 0.539 | 0.38 | 0.62 | 0.45 | 22.8 |

### Solo DeepSeek (22 trazas)

| Método | Pk ↓ | WindowDiff ↓ | Precisión | Cobertura | F1 (±1 frase) | Tramos/traza |
|---|---|---|---|---|---|---|
| Tamaño fijo | 0.518 | 0.530 | 0.23 | 0.22 | 0.22 | 14.4 |
| Solo párrafos | 0.217 | 0.308 | 0.60 | 0.82 | 0.67 | 21.5 |
| Solo marcadores | 0.445 | 0.479 | 0.31 | 0.20 | 0.21 | 9.3 |
| TextTiling | 0.534 | 0.674 | 0.32 | 0.75 | 0.44 | 35.7 |
| MeDRA (por defecto) | 0.458 | 0.523 | 0.38 | 0.55 | 0.43 | 21.3 |

### Solo OpenThoughts (8 trazas)

| Método | Pk ↓ | WindowDiff ↓ | Precisión | Cobertura | F1 (±1 frase) | Tramos/traza |
|---|---|---|---|---|---|---|
| Tamaño fijo | 0.439 | 0.454 | 0.44 | 0.35 | 0.39 | 11.8 |
| Solo párrafos | 0.410 | 0.578 | 0.41 | 0.88 | 0.50 | 38.2 |
| Solo marcadores | 0.449 | 0.717 | 0.26 | 0.87 | 0.39 | 46.1 |
| TextTiling | 0.535 | 0.652 | 0.33 | 0.71 | 0.44 | 27.5 |
| MeDRA (por defecto) | 0.475 | 0.585 | 0.39 | 0.83 | 0.52 | 26.8 |

## Segmentación en test (11 trazas)

Parámetros ajustados en dev con `python -m eval.tune`: `{'window': 2, 'climb': 3, 'marker_scale': 1.0, 'paragraph_weight': 2.0, 'threshold': 1.8, 'min_sentences': 8}`.

«Párrafos + mín.»: un corte en cada línea en blanco, descartando los que quedan a menos de 8 frases del anterior (mínimo elegido en dev). Es la ablación del segmentador ajustado: la misma regla sin cohesión ni marcadores.

| Método | Pk ↓ | WindowDiff ↓ | Precisión | Cobertura | F1 (±1 frase) | Tramos/traza |
|---|---|---|---|---|---|---|
| Tamaño fijo | 0.517 | 0.527 | 0.27 | 0.22 | 0.24 | 12.5 |
| Solo párrafos | 0.269 | 0.369 | 0.60 | 0.81 | 0.64 | 26.5 |
| Solo marcadores | 0.434 | 0.550 | 0.36 | 0.38 | 0.26 | 22.0 |
| TextTiling | 0.529 | 0.618 | 0.34 | 0.70 | 0.45 | 29.9 |
| MeDRA (por defecto) | 0.447 | 0.510 | 0.42 | 0.62 | 0.48 | 22.4 |
| Párrafos + mín. 8 frases | 0.280 | 0.297 | 0.76 | 0.49 | 0.59 | 10.7 |
| MeDRA (ajustado) | 0.304 | 0.320 | 0.69 | 0.45 | 0.54 | 10.6 |

### Test, solo DeepSeek (8 trazas)

| Método | Pk ↓ | WindowDiff ↓ | Precisión | Cobertura | F1 (±1 frase) | Tramos/traza |
|---|---|---|---|---|---|---|
| Tamaño fijo | 0.531 | 0.537 | 0.25 | 0.19 | 0.22 | 11.8 |
| Solo párrafos | 0.209 | 0.278 | 0.67 | 0.80 | 0.70 | 19.5 |
| Solo marcadores | 0.437 | 0.470 | 0.42 | 0.20 | 0.23 | 7.0 |
| TextTiling | 0.531 | 0.618 | 0.37 | 0.76 | 0.49 | 29.2 |
| MeDRA (por defecto) | 0.445 | 0.487 | 0.44 | 0.56 | 0.48 | 18.4 |
| Párrafos + mín. 8 frases | 0.242 | 0.259 | 0.81 | 0.51 | 0.62 | 9.8 |
| MeDRA (ajustado) | 0.257 | 0.272 | 0.78 | 0.49 | 0.59 | 9.6 |

### Test, solo OpenThoughts (3 trazas)

| Método | Pk ↓ | WindowDiff ↓ | Precisión | Cobertura | F1 (±1 frase) | Tramos/traza |
|---|---|---|---|---|---|---|
| Tamaño fijo | 0.479 | 0.500 | 0.30 | 0.28 | 0.29 | 14.7 |
| Solo párrafos | 0.429 | 0.614 | 0.42 | 0.81 | 0.47 | 45.0 |
| Solo marcadores | 0.428 | 0.765 | 0.21 | 0.87 | 0.34 | 62.0 |
| TextTiling | 0.523 | 0.619 | 0.26 | 0.53 | 0.35 | 31.7 |
| MeDRA (por defecto) | 0.454 | 0.574 | 0.35 | 0.78 | 0.48 | 33.0 |
| Párrafos + mín. 8 frases | 0.379 | 0.400 | 0.61 | 0.45 | 0.51 | 13.3 |
| MeDRA (ajustado) | 0.430 | 0.447 | 0.46 | 0.35 | 0.39 | 13.3 |

## Tipo de paso (en las fronteras de la referencia)

418 pasos. MeDRA: exactitud 0.28, F1 macro 0.20. Línea base (siempre «development»): exactitud 0.23, F1 macro 0.06.

| Tipo | Precisión | Cobertura | F1 | Casos |
|---|---|---|---|---|
| alternative | 0.50 | 0.10 | 0.17 | 40 |
| backtrack | 0.05 | 0.50 | 0.08 | 2 |
| conclusion | 0.56 | 0.18 | 0.27 | 85 |
| development | 0.24 | 0.83 | 0.38 | 96 |
| planning | 0.24 | 0.08 | 0.12 | 64 |
| verification | 1.00 | 0.10 | 0.18 | 131 |

Confusión (referencia → MeDRA): alternative->alternative: 4, alternative->backtrack: 2, alternative->conclusion: 1, alternative->development: 33, backtrack->backtrack: 1, backtrack->development: 1, conclusion->alternative: 1, conclusion->conclusion: 15, conclusion->development: 68, conclusion->planning: 1, development->backtrack: 1, development->conclusion: 4, development->development: 80, development->planning: 11, planning->conclusion: 5, planning->development: 54, planning->planning: 5, verification->alternative: 3, verification->backtrack: 18, verification->conclusion: 2, verification->development: 91, verification->planning: 4, verification->verification: 13

## Conceptos clave (burbujas)

| Método | Precisión | Cobertura | F1 | F1 flexible |
|---|---|---|---|---|
| MeDRA (burbujas) | 0.28 | 0.59 | 0.38 | 0.54 |
| Frecuencia (top-16) | 0.29 | 0.60 | 0.39 | 0.58 |

Flexible: cuenta como acierto si las palabras de un término contienen las del otro («odd number» y «odd»).

## Temas

| Agrupación | Precisión B³ | Cobertura B³ | F1 B³ | Términos anotados encontrados |
|---|---|---|---|---|
| Louvain (MeDRA) | 0.58 | 0.66 | 0.61 | 85% |
| Aglomerativa (coseno, media) | 0.53 | 0.81 | 0.61 | 77% |

## Por traza (MeDRA por defecto)

| Traza | Fuente | Split | Frases | Tramos ref. | Tramos MeDRA | Pk | WindowDiff |
|---|---|---|---|---|---|---|---|
| en-cod-anagrams | deepseek | test | 204 | 16 | 31 | 0.475 | 0.566 |
| en-cod-brackets | deepseek | dev | 330 | 21 | 43 | 0.556 | 0.699 |
| en-cod-dedupe | deepseek | test | 158 | 24 | 18 | 0.452 | 0.465 |
| en-cod-intervals | deepseek | dev | 176 | 15 | 28 | 0.529 | 0.612 |
| en-cod-lru | deepseek | dev | 101 | 9 | 16 | 0.621 | 0.695 |
| en-cod-palindrome | deepseek | dev | 136 | 11 | 24 | 0.415 | 0.569 |
| en-cod-search | deepseek | test | 79 | 13 | 9 | 0.408 | 0.447 |
| en-log-hats | deepseek | dev | 149 | 16 | 27 | 0.382 | 0.472 |
| en-log-knights | deepseek | dev | 82 | 11 | 18 | 0.500 | 0.551 |
| en-log-league | deepseek | dev | 129 | 15 | 20 | 0.384 | 0.392 |
| en-log-liars | deepseek | test | 138 | 16 | 31 | 0.522 | 0.575 |
| en-log-pets | deepseek | test | 97 | 15 | 18 | 0.404 | 0.426 |
| en-log-schedule | deepseek | dev | 253 | 21 | 26 | 0.538 | 0.603 |
| en-mat-clock | deepseek | dev | 110 | 11 | 18 | 0.371 | 0.448 |
| en-mat-coins | deepseek | dev | 205 | 17 | 36 | 0.407 | 0.558 |
| en-mat-dice | deepseek | dev | 80 | 12 | 3 | 0.390 | 0.390 |
| en-mat-digits | deepseek | dev | 176 | 12 | 23 | 0.467 | 0.627 |
| en-mat-ladder | deepseek | dev | 121 | 18 | 22 | 0.500 | 0.500 |
| en-mat-powers | deepseek | test | 86 | 11 | 13 | 0.439 | 0.463 |
| en-mat-semicircle | deepseek | test | 76 | 10 | 12 | 0.417 | 0.472 |
| en-mat-square | deepseek | test | 79 | 9 | 15 | 0.440 | 0.480 |
| en-mat-trains | deepseek | dev | 120 | 13 | 18 | 0.461 | 0.487 |
| ot-cod-tasks | openthoughts | dev | 153 | 12 | 36 | 0.531 | 0.769 |
| ot-cod-yen | openthoughts | test | 146 | 15 | 36 | 0.482 | 0.631 |
| ot-log-board | openthoughts | dev | 62 | 10 | 19 | 0.492 | 0.525 |
| ot-log-calculator | openthoughts | test | 115 | 12 | 25 | 0.391 | 0.509 |
| ot-log-krakozyabrs | openthoughts | dev | 128 | 13 | 27 | 0.423 | 0.537 |
| ot-mat-plums | openthoughts | dev | 71 | 9 | 20 | 0.493 | 0.612 |
| ot-mat-trail | openthoughts | dev | 57 | 11 | 13 | 0.500 | 0.519 |
| ot-sci-enthalpy | openthoughts | test | 164 | 20 | 38 | 0.487 | 0.581 |
