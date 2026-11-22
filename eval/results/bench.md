# Eficiencia de MeDRA

`python -m eval.bench`, 2026-11-23, commit 43ac783 (+ cambios sin commit). Máquina: Windows-11-10.0.26300-SP0, AMD64 Family 25 Model 116 Stepping 1, AuthenticAMD, Python 3.13.7.

30844 palabras en 30844 trozos de una palabra, 4650 actualizaciones (una por trozo que cierra al menos una frase). Minero + presentador en cada actualización (sin el límite de 5 vistas/s del servidor): 1418.16 s en total, **21.7 palabras/s** sostenidas de media.

| Palabras ya recibidas | Actualizaciones | Minero p50 (ms) | Minero p95 (ms) | Total p50 (ms) | Total p95 (ms) |
|---|---|---|---|---|---|
| 1-5000 | 811 | 25.5 | 60.1 | 41.0 | 101.6 |
| 5001-10000 | 719 | 75.4 | 173.2 | 138.9 | 238.5 |
| 10001-15000 | 785 | 114.4 | 224.9 | 229.6 | 348.2 |
| 15001-20000 | 728 | 168.0 | 285.2 | 347.4 | 474.6 |
| 20001-25000 | 744 | 197.1 | 326.8 | 432.3 | 569.5 |
| 25001-30000 | 757 | 227.4 | 356.1 | 520.8 | 652.7 |
| 30001-35000 | 106 | 219.6 | 340.2 | 530.0 | 643.5 |
