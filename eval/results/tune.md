# Ajuste de parámetros del segmentador

`python -m eval.tune`, 2026-11-25, commit 3894b35. Búsqueda en rejilla: 89424 configuraciones × 30 trazas en 186.5 s. Objetivo: mean WindowDiff on dev (ties: Pk, then closest to defaults).

Dev (19): en-cod-brackets, en-cod-intervals, en-cod-lru, en-cod-palindrome, en-log-hats, en-log-knights, en-log-league, en-log-schedule, en-mat-clock, en-mat-coins, en-mat-dice, en-mat-digits, en-mat-ladder, en-mat-trains, ot-cod-tasks, ot-log-board, ot-log-krakozyabrs, ot-mat-plums, ot-mat-trail.  
Test (11): en-cod-anagrams, en-cod-dedupe, en-cod-search, en-log-liars, en-log-pets, en-mat-powers, en-mat-semicircle, en-mat-square, ot-cod-yen, ot-log-calculator, ot-sci-enthalpy.

| Parámetro | Por defecto | Ajustado |
|---|---|---|
| window | 3 | 2 |
| climb | 2 | 3 |
| marker_scale | 1.0 | 1.0 |
| paragraph_weight | 0.25 | 2.0 |
| threshold | 0.5 | 1.8 |
| min_sentences | 2 | 8 |

| | WindowDiff dev | Pk dev | WindowDiff test | Pk test | WindowDiff LOOCV | Pk LOOCV |
|---|---|---|---|---|---|---|
| Por defecto | 0.556 | 0.472 | 0.510 | 0.447 | 0.539 | 0.463 |
| Ajustado | 0.293 | 0.274 | 0.320 | 0.304 | 0.309 | 0.274 |

LOOCV: para cada traza, se ajusta con las demás y se evalúa en ella; la columna «Por defecto» es la media de los parámetros por defecto en las mismas trazas.

## Sensibilidad (mejor WindowDiff en dev fijando cada valor, el resto libre)

- **window**: 2 → 0.293, 3 → 0.294, 4 → 0.297
- **climb**: 1 → 0.298, 2 → 0.297, 3 → 0.293
- **marker_scale**: 0.0 → 0.298, 0.5 → 0.293, 1.0 → 0.293, 1.5 → 0.293, 2.0 → 0.293, 3.0 → 0.294
- **paragraph_weight**: 0.0 → 0.428, 0.25 → 0.397, 0.5 → 0.348, 0.75 → 0.326, 1.0 → 0.308, 1.5 → 0.298, 2.0 → 0.293, 3.0 → 0.293, 4.0 → 0.293
- **threshold**: 0.3 → 0.398, 0.4 → 0.355, 0.5 → 0.344, 0.6 → 0.334, 0.7 → 0.324, 0.8 → 0.314, 0.9 → 0.310, 1.0 → 0.308, 1.1 → 0.303, 1.2 → 0.302, 1.3 → 0.298, 1.4 → 0.298, 1.5 → 0.298, 1.6 → 0.297, 1.7 → 0.297, 1.8 → 0.293, 1.9 → 0.295, 2.0 → 0.295, 2.1 → 0.295, 2.2 → 0.295, 2.3 → 0.294, 2.4 → 0.294, 2.5 → 0.294
- **min_sentences**: 2 → 0.332, 3 → 0.313, 4 → 0.298, 5 → 0.305, 6 → 0.297, 8 → 0.293, 10 → 0.297, 12 → 0.334
