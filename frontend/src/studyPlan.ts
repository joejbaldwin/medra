// User study protocol (memoria 3.11, item 5): who sees which trace in which
// condition, the tasks, the SUS questionnaire and the order of the steps.
// Pure data and functions, so it can be unit tested; study.ts draws it.

export type Condition = "texto" | "medra";

export const CONDITION_LABEL: Record<Condition, string> = {
  texto: "Texto sin procesar",
  medra: "MeDRA",
};

/** Two annotated logic traces of similar length (eval/annotations), so every
 *  answer can be scored against the group's annotation. */
export const PETS = "en-log-pets";
export const KNIGHTS = "en-log-knights";
/** Hand-written sample used to learn the dashboard before the MeDRA block. */
export const PRACTICE_TRACE = "odd-sum-en";

export interface Design {
  first: Condition; // condition of the first block
  medraTrace: string; // trace shown in the MeDRA block (the other one is plain text)
}

/** Counterbalanced for 6 participants: condition order is 3/3 and which trace
 *  gets MeDRA is 3/3. P1-P4 cover the four combinations once; with six people
 *  the trace order cannot also be 3/3 (it is 4/2), which the memoria notes. */
export const DESIGNS: Record<string, Design> = {
  P1: { first: "medra", medraTrace: PETS },
  P2: { first: "texto", medraTrace: KNIGHTS },
  P3: { first: "medra", medraTrace: KNIGHTS },
  P4: { first: "texto", medraTrace: PETS },
  P5: { first: "medra", medraTrace: PETS },
  P6: { first: "texto", medraTrace: KNIGHTS },
};

/** Codes outside P1-P6 (for example "prueba") are test runs with P1's design. */
export function designFor(participant: string): { design: Design; test: boolean } {
  const real = DESIGNS[participant];
  return { design: real ?? DESIGNS.P1, test: !real };
}

export interface Block {
  condition: Condition;
  trace: string;
}

export function blocksFor(d: Design): [Block, Block] {
  const textTrace = d.medraTrace === PETS ? KNIGHTS : PETS;
  const medra: Block = { condition: "medra", trace: d.medraTrace };
  const texto: Block = { condition: "texto", trace: textTrace };
  return d.first === "medra" ? [medra, texto] : [texto, medra];
}

export interface Task {
  id: string;
  question: string;
  hint: string;
  multiline: boolean;
}

/** The same tasks for both traces. Answers quote the start of a sentence (or
 *  list concepts), so they can be matched to the annotated boundaries. */
export const TASKS: Task[] = [
  {
    id: "verificacion",
    question: "¿En qué frase empieza el modelo a comprobar su solución por primera vez?",
    hint: "Copia o escribe las primeras palabras de esa frase.",
    multiline: false,
  },
  {
    id: "alternativas",
    question: "¿En qué momentos prueba el modelo otro enfoque u otra interpretación del problema?",
    hint: "Copia las primeras palabras de cada frase, una por línea.",
    multiline: true,
  },
  {
    id: "conclusion",
    question: "¿En qué frase llega el modelo por primera vez a una conclusión?",
    hint: "Copia o escribe las primeras palabras de esa frase.",
    multiline: false,
  },
  {
    id: "conceptos",
    question: "¿Cuáles son los conceptos principales del razonamiento?",
    hint: "Escribe entre 3 y 5, separados por comas.",
    multiline: false,
  },
];

/** System Usability Scale (Brooke, 1996), in Spanish, about "esta herramienta". */
export const SUS_ITEMS: string[] = [
  "Creo que me gustaría usar esta herramienta con frecuencia.",
  "Encontré la herramienta innecesariamente compleja.",
  "Pensé que la herramienta era fácil de usar.",
  "Creo que necesitaría ayuda de una persona con conocimientos técnicos para poder usarla.",
  "Las distintas funciones de la herramienta estaban bien integradas.",
  "Pensé que había demasiada incoherencia en la herramienta.",
  "Imagino que la mayoría de la gente aprendería a usarla muy rápido.",
  "Encontré la herramienta muy engorrosa de usar.",
  "Me sentí muy seguro/a al usar la herramienta.",
  "Necesité aprender muchas cosas antes de poder empezar a usarla.",
];

/** SUS score, 0-100: odd items count (answer - 1), even items (5 - answer),
 *  and the sum is multiplied by 2.5. Null until all ten items are answered. */
export function susScore(answers: (number | null)[]): number | null {
  if (answers.length !== 10 || answers.some((a) => a === null || a < 1 || a > 5)) return null;
  const sum = answers.reduce<number>((acc, a, i) => acc + (i % 2 === 0 ? a! - 1 : 5 - a!), 0);
  return sum * 2.5;
}

export type Step =
  | { kind: "intro" }
  | { kind: "practice" }
  | { kind: "blockIntro"; block: number }
  | { kind: "task"; block: number; task: number }
  | { kind: "sus"; block: number }
  | { kind: "final" }
  | { kind: "submit" };

/** The whole session in order. The practice comes right before the MeDRA
 *  block, wherever that block falls. */
export function stepsFor(blocks: [Block, Block]): Step[] {
  const steps: Step[] = [{ kind: "intro" }];
  blocks.forEach((b, block) => {
    if (b.condition === "medra") steps.push({ kind: "practice" });
    steps.push({ kind: "blockIntro", block });
    TASKS.forEach((_, task) => steps.push({ kind: "task", block, task }));
    steps.push({ kind: "sus", block });
  });
  steps.push({ kind: "final" }, { kind: "submit" });
  return steps;
}
