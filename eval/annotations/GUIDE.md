# Guía de anotación (evaluación de MeDRA)

Estas anotaciones son la referencia con la que se mide MeDRA: dónde empieza cada paso del
razonamiento, de qué tipo es, cuáles son los conceptos clave y qué temas hay. Si dos personas
anotan con criterios distintos, los números no significan nada, así que sigue esta guía.

Las trazas están en inglés porque así razona el modelo (DeepSeek piensa en inglés aunque se le
pregunte en español). La guía y la discusión, en español.

## Qué hay en cada fichero

`eval/annotations/<id>.md` contiene el razonamiento de la traza `eval/traces/<id>.json`, sin
cambiar nada, con una etiqueta `[[tipo]]` justo delante de la frase que empieza cada paso. Arriba,
entre `---`, están los conceptos y los temas:

```
---
trace: en-log-pets
annotator: claude-draft      # pon tu nombre al corregir
status: draft                # cámbialo a corrected cuando termines
concepts: [dog owner, parrot, house]
topics:
- [house, adjacent, neighbor]
- [cat, dog, parrot, pet]
---
[[planning]]We need answer puzzle. Need reason carefully. ...
```

**No cambies el texto**, ni un espacio. Solo se añaden, quitan o mueven etiquetas. El comprobador
lo verifica.

## 1. Pasos (fronteras)

Un paso es un tramo de frases con un solo propósito. Empieza un paso nuevo cuando el razonamiento
cambia de propósito: pasa de plantear a calcular, empieza a comprobar algo ya obtenido, se corrige,
prueba otro caso u otro enfoque, o concluye.

- La etiqueta va delante de la primera frase del paso, nunca en mitad de una frase.
- La primera frase de la traza siempre lleva etiqueta.
- No partas un cálculo o una lista en varios pasos solo porque sea largo: si el propósito es el
  mismo, es un solo paso.
- Un paso de una sola frase está bien si de verdad cambia el propósito (p. ej. «Wait, that's
  wrong.» seguido de la corrección es un paso `backtrack` que incluye la corrección).
- Las palabras como «Wait», «Alternatively», «Let me check» ayudan, pero no deciden solas: decide
  el cambio de propósito. MeDRA usa esas palabras; si la referencia también se basara solo en
  ellas, la evaluación sería circular.

Como orientación, en estas trazas un paso suele tener entre 3 y 15 frases.

## 2. Tipo de paso

| Tipo | Cuándo |
|---|---|
| `planning` | Entender o reformular el problema, decidir qué hacer o cómo abordarlo. |
| `development` | Hacer el trabajo: calcular, deducir, escribir código, analizar un caso. |
| `verification` | Comprobar un resultado ya obtenido (recalcular, probar con un ejemplo, repasar condiciones). |
| `backtrack` | Darse cuenta de un error o de una suposición falsa y corregirlo. |
| `alternative` | Probar otro enfoque, otro caso u otra interpretación del enunciado. |
| `conclusion` | Decir el resultado o decidir qué se va a responder. |

Si dudas entre dos, elige el propósito principal del paso. Un caso nuevo dentro de una enumeración
que ya se había planeado («Case 2: …») es `alternative`. Resolver otra vez con otro método para
confirmar un resultado que ya se tiene es `verification`, aunque empiece con «Alternatively»;
`alternative` es cuando el otro enfoque se prueba para avanzar, no para confirmar.

## 3. Conceptos clave (`concepts`)

Entre 5 y 10 términos que alguien necesitaría ver para saber de qué trata el razonamiento: lo que
te gustaría ver como burbuja en el mapa de conceptos.

- Sustantivos o expresiones nominales de una a tres palabras, tal como aparecen en el texto
  (`dog owner`, `binary search`, `probability`), en singular.
- Nombres propios sí, si son importantes (`Alice`).
- No palabras genéricas del razonamiento (`answer`, `step`, `case`, `need`, `problem`) ni números
  sueltos.

## 4. Temas (`topics`)

Entre 2 y 5 grupos de términos del texto que tratan del mismo asunto, de 3 a 8 términos cada uno.
Cada término en un solo grupo. No hace falta cubrir todas las palabras: solo los grupos claros.

## Cómo corregir un borrador

1. Lee la traza entera antes de tocar nada.
2. Mueve, quita o añade etiquetas y cambia los tipos donde no estés de acuerdo. **No te fíes del
   borrador**: lo ha hecho un asistente de IA y está para ahorrar tiempo, no para darlo por bueno.
3. Revisa los conceptos y los temas.
4. Pon tu nombre en `annotator` y `status: corrected`.
5. Comprueba el fichero:

   ```
   python -m eval.annotations --check
   ```

   Si una etiqueta queda en mitad de una frase, te dice dónde. Para ver cómo divide MeDRA la traza
   en frases: `python -m eval.annotations --sentences <id>`.

## Anotación doble (acuerdo entre anotadores)

Cuatro trazas las anota una segunda persona **desde cero**, sin ver el borrador ni la corrección
de la otra:

```
python -m eval.annotations --blank <id> <tu-nombre>
```

crea `eval/annotations/<id>.<tu-nombre>.md` solo con la primera etiqueta. Anótalo entero siguiendo
esta guía. Con las dos versiones se mide cuánto coinciden dos personas, que es el techo razonable
para MeDRA.
