// User study page (estudio.html): runs the protocol of studyPlan.ts for one
// participant and posts the results to the backend (POST /study/results).
//
//   estudio.html?p=P3      the facilitator sends each participant their code
//
// Conditions: "texto" shows the trace as one block of text, like a chat;
// "medra" embeds the real dashboard in an iframe (index.html?estudio=1&...),
// which replays the trace at once and reports back with postMessage when it
// is ready and whenever the participant selects something in a view.
// Each task is timed from the moment the trace is on screen to "Siguiente".
import "./styles.css";
import "./study.css";
import {
  type Block,
  blocksFor,
  CONDITION_LABEL,
  designFor,
  PRACTICE_TRACE,
  type Step,
  stepsFor,
  SUS_ITEMS,
  susScore,
  TASKS,
} from "./studyPlan";
import { esc } from "./util";

const BACKEND = (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "";
const CODE = /^[A-Za-z0-9_-]{1,32}$/;

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const card = $<HTMLElement>("card");
const materialEl = $<HTMLElement>("material");
const progressEl = $<HTMLElement>("progress");
const whoEl = $<HTMLElement>("who");
const mainEl = $<HTMLElement>("main");

// ---------------------------------------------------------------- results

interface TaskResult {
  id: string;
  question: string;
  answer: string;
  started_at: string;
  ms: number;
}
interface StudyEvent {
  t_ms: number; // since the block's trace was ready
  task: string | null;
  event: string;
  kind?: string;
}
interface BlockResult {
  condition: Block["condition"];
  trace: string;
  material_ready_ms: number | null; // how long the trace took to appear
  tasks: TaskResult[];
  events: StudyEvent[];
  sus: (number | null)[];
  sus_score: number | null;
}
interface Result {
  version: 1;
  participant: string;
  test: boolean;
  design: { first: string; medra_trace: string };
  started_at: string;
  finished_at: string | null;
  user_agent: string;
  viewport: { width: number; height: number };
  practice_ms: number | null;
  blocks: BlockResult[];
  final: { preference: string | null; reason: string; comments: string };
}

let participant = new URLSearchParams(location.search).get("p")?.trim() ?? "";
let blocks: [Block, Block];
let steps: Step[] = [{ kind: "intro" }];
let result: Result;
let at = 0;
let submitted = false;

function setup(code: string): void {
  participant = code;
  const { design, test } = designFor(code);
  blocks = blocksFor(design);
  steps = stepsFor(blocks);
  result = {
    version: 1,
    participant: code,
    test,
    design: { first: design.first, medra_trace: design.medraTrace },
    started_at: new Date().toISOString(),
    finished_at: null,
    user_agent: navigator.userAgent,
    viewport: { width: innerWidth, height: innerHeight },
    practice_ms: null,
    blocks: blocks.map((b) => ({
      condition: b.condition,
      trace: b.trace,
      material_ready_ms: null,
      tasks: [],
      events: [],
      sus: Array(10).fill(null),
      sus_score: null,
    })),
    final: { preference: null, reason: "", comments: "" },
  };
  whoEl.textContent = test ? `${code} (ensayo)` : code;
}

// ---------------------------------------------------------------- material

// The trace shown next to the tasks. One at a time: the practice dashboard,
// then each block's plain text or dashboard, kept alive across its tasks.
interface Material {
  key: string;
  el: HTMLElement;
  requested: number;
  readyAt: number | null;
  onReady: (() => void)[];
}
let material: Material | null = null;

function markReady(m: Material): void {
  if (m.readyAt !== null) return;
  m.readyAt = performance.now();
  for (const f of m.onReady.splice(0)) f();
}

/** The dashboard replaying `trace` at once; `guide` opens the guided tour first. */
function dashboardFrame(trace: string, guide = false): HTMLIFrameElement {
  const url = new URL("index.html", location.href);
  url.search = new URLSearchParams({ estudio: "1", traza: trace, velocidad: "0", ...(guide ? { guia: "1" } : {}) }).toString();
  const frame = document.createElement("iframe");
  frame.className = "study-frame";
  frame.title = "Panel de MeDRA";
  frame.src = url.toString();
  return frame;
}

async function plainText(trace: string, m: Material): Promise<void> {
  try {
    const res = await fetch(`${BACKEND}/study/traces/${encodeURIComponent(trace)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const t = (await res.json()) as { prompt: string; reasoning: string; answer: string };
    m.el.innerHTML = `
      <article class="plain">
        <h2 class="plain-label">Pregunta</h2>
        <div class="plain-prompt">${esc(t.prompt)}</div>
        <h2 class="plain-label">Razonamiento del modelo</h2>
        <div class="plain-text">${esc(t.reasoning)}</div>
        <h2 class="plain-label">Respuesta</h2>
        <div class="plain-text">${esc(t.answer)}</div>
      </article>`;
    markReady(m);
  } catch (err) {
    m.el.innerHTML = `<p class="study-error">No se pudo cargar la traza (${esc((err as Error).message)}). Avisa a la persona que dirige la prueba.</p>`;
  }
}

/** Show (or keep) the material for `key`; `veiled` keeps it laid out but hidden. */
function showMaterial(key: string, make: (m: Material) => void, veiled: boolean): Material {
  if (material?.key !== key) {
    const el = document.createElement("div");
    el.className = "study-material-inner";
    materialEl.replaceChildren(el);
    material = { key, el, requested: performance.now(), readyAt: null, onReady: [] };
    make(material);
  }
  materialEl.hidden = false;
  materialEl.classList.toggle("veiled", veiled);
  mainEl.classList.add("with-material");
  return material!;
}

function hideMaterial(): void {
  materialEl.hidden = true;
  mainEl.classList.remove("with-material");
}

function blockMaterial(block: number, veiled: boolean): Material {
  const b = blocks[block];
  return showMaterial(
    `block-${block}`,
    (m) => {
      if (b.condition === "medra") m.el.append(dashboardFrame(b.trace));
      else void plainText(b.trace, m);
    },
    veiled,
  );
}

// The dashboard in the iframe reports "done" when the replay ends, "select"
// when a concept, topic or step is clicked, and "tour-done" when the practice's
// guided tour closes (main.ts, study mode).
let onTourDone: (() => void) | null = null;
window.addEventListener("message", (e: MessageEvent) => {
  if (e.origin !== location.origin) return;
  const data = e.data as { source?: string; event?: string; kind?: string };
  if (data?.source !== "medra-study" || !material) return;
  if (data.event === "done") markReady(material);
  if (data.event === "tour-done") onTourDone?.();
  const step = steps[at];
  if (data.event === "select" && step && (step.kind === "task" || step.kind === "blockIntro") && material.readyAt !== null) {
    result.blocks[step.block].events.push({
      t_ms: Math.round(performance.now() - material.readyAt),
      task: step.kind === "task" ? TASKS[step.task].id : null,
      event: "select",
      kind: data.kind,
    });
  }
});

// ---------------------------------------------------------------- steps

function go(next: number): void {
  at = next;
  const step = steps[at];
  progressEl.style.setProperty("--done", String(at / Math.max(1, steps.length - 1)));
  progressEl.setAttribute("aria-valuenow", String(at + 1));
  progressEl.setAttribute("aria-valuemax", String(steps.length));
  if (step.kind !== "task" && step.kind !== "blockIntro" && step.kind !== "practice") hideMaterial();
  ({
    intro: renderIntro,
    practice: renderPractice,
    blockIntro: () => renderBlockIntro((step as { block: number }).block),
    task: () => renderTask((step as { block: number; task: number }).block, (step as { task: number }).task),
    sus: () => renderSus((step as { block: number }).block),
    final: renderFinal,
    submit: () => void submit(),
  })[step.kind]();
  card.scrollTop = 0;
  card.querySelector<HTMLElement>("[autofocus], input, textarea, button.primary")?.focus();
}

function renderIntro(): void {
  card.innerHTML = `
    <h1>Prueba de MeDRA</h1>
    <p>Gracias por participar. Vas a probar una herramienta para leer el razonamiento de los modelos de IA.
       Evaluamos la herramienta, no a ti, y tus respuestas son anónimas.</p>
    <label class="field-row" ${participant ? "hidden" : ""}>
      <span>Código de participante</span>
      <input id="code" type="text" autocomplete="off" spellcheck="false" placeholder="P1" value="${esc(participant)}">
    </label>
    <label class="check"><input id="consent" type="checkbox"> Acepto participar.</label>
    <div class="actions"><button class="primary" id="next" type="button" disabled>Empezar</button></div>`;
  const code = $<HTMLInputElement>("code");
  const consent = $<HTMLInputElement>("consent");
  const next = $<HTMLButtonElement>("next");
  const check = () => (next.disabled = !(consent.checked && CODE.test(code.value.trim())));
  code.addEventListener("input", check);
  consent.addEventListener("change", check);
  next.addEventListener("click", () => {
    setup(code.value.trim());
    go(1);
  });
}

// The practice: the dashboard's guided tour runs first, with this card greyed
// out like the rest of the page; then the participant explores freely.
function renderPractice(): void {
  const started = performance.now();
  const m = showMaterial("practice", (mat) => mat.el.append(dashboardFrame(PRACTICE_TRACE, true)), false);
  const frame = m.el.querySelector("iframe")!;
  card.innerHTML = `
    <p class="eyebrow">Práctica</p>
    <h1>Explora MeDRA</h1>
    <p>Pulsa una burbuja, un paso y una palabra subrayada para ver cómo se enlazan. Aquí no se mide nada.</p>
    <div class="actions">
      <button id="again" type="button">Ver la guía otra vez</button>
      <button class="primary" id="next" type="button">Continuar</button>
    </div>`;
  const touring = (on: boolean) => {
    card.classList.toggle("dimmed", on);
    card.inert = on;
  };
  touring(true);
  onTourDone = () => touring(false);
  $<HTMLButtonElement>("again").addEventListener("click", () => {
    touring(true);
    frame.contentWindow?.postMessage({ source: "medra-study-page", event: "tour" }, location.origin);
  });
  $<HTMLButtonElement>("next").addEventListener("click", () => {
    onTourDone = null;
    card.classList.remove("dimmed");
    card.inert = false;
    result.practice_ms = Math.round(performance.now() - started);
    go(at + 1);
  });
}

function renderBlockIntro(block: number): void {
  const b = blocks[block];
  const m = blockMaterial(block, true); // load now, show when the tasks start
  const how =
    b.condition === "medra"
      ? "Verás el razonamiento en MeDRA. Puedes usar el texto y todas las vistas como quieras."
      : "Verás el razonamiento como un bloque de texto, igual que en un chat normal.";
  card.innerHTML = `
    <p class="eyebrow">Bloque ${block + 1} de 2</p>
    <h1>${CONDITION_LABEL[b.condition]}</h1>
    <p>${how} Responde a ${TASKS.length} preguntas sobre él, tan rápido como puedas sin perder precisión,
       y piensa en voz alta mientras buscas.</p>
    <p class="muted">Si no encuentras una respuesta, déjala en blanco.</p>
    <div class="actions"><button class="primary" id="next" type="button">Empezar el bloque</button></div>`;
  $<HTMLButtonElement>("next").addEventListener("click", () => {
    if (m.readyAt !== null) result.blocks[block].material_ready_ms = Math.round(m.readyAt - m.requested);
    go(at + 1);
  });
}

function renderTask(block: number, task: number): void {
  const t = TASKS[task];
  const m = blockMaterial(block, false);
  const field = t.multiline
    ? `<textarea id="answer" rows="4" disabled></textarea>`
    : `<input id="answer" type="text" autocomplete="off" disabled>`;
  card.innerHTML = `
    <p class="eyebrow">Bloque ${block + 1} de 2 · ${CONDITION_LABEL[blocks[block].condition]} · pregunta ${task + 1} de ${TASKS.length}</p>
    <h1 class="question">${esc(t.question)}</h1>
    <label class="field-row"><span>${esc(t.hint)}</span>${field}</label>
    <p class="muted" id="wait">Cargando la traza…</p>
    <div class="actions"><button class="primary" id="next" type="button" disabled>Siguiente</button></div>`;
  const answer = $<HTMLInputElement | HTMLTextAreaElement>("answer");
  const next = $<HTMLButtonElement>("next");
  let start = 0;
  let startedAt = "";
  const begin = () => {
    if (result.blocks[block].material_ready_ms === null) result.blocks[block].material_ready_ms = Math.round(m.readyAt! - m.requested);
    start = performance.now();
    startedAt = new Date().toISOString();
    $<HTMLElement>("wait").hidden = true;
    answer.disabled = false;
    next.disabled = false;
    answer.focus();
  };
  if (m.readyAt !== null) begin();
  else m.onReady.push(begin);
  if (!t.multiline) answer.addEventListener("keydown", (e) => (e as KeyboardEvent).key === "Enter" && next.click());
  next.addEventListener("click", () => {
    result.blocks[block].tasks[task] = {
      id: t.id,
      question: t.question,
      answer: answer.value.trim(),
      started_at: startedAt,
      ms: Math.round(performance.now() - start),
    };
    go(at + 1);
  });
}

function renderSus(block: number): void {
  const label = CONDITION_LABEL[blocks[block].condition];
  const answers = result.blocks[block].sus;
  const rows = SUS_ITEMS.map(
    (item, i) => `
      <fieldset class="sus-row">
        <legend>${i + 1}. ${esc(item)}</legend>
        <div class="scale">
          <span class="end">Totalmente en desacuerdo</span>
          ${[1, 2, 3, 4, 5]
            .map((v) => `<label><input type="radio" name="sus-${i}" value="${v}" ${answers[i] === v ? "checked" : ""}><span>${v}</span></label>`)
            .join("")}
          <span class="end">Totalmente de acuerdo</span>
        </div>
      </fieldset>`,
  ).join("");
  card.innerHTML = `
    <p class="eyebrow">Bloque ${block + 1} de 2 · valoración</p>
    <h1>¿Qué te ha parecido: ${label}?</h1>
    <p>Piensa solo en la herramienta que acabas de usar (${label}) y marca tu grado de acuerdo con cada frase.
       Responde rápido, con tu primera impresión.</p>
    <form id="sus">${rows}</form>
    <div class="actions"><button class="primary" id="next" type="button" disabled>Continuar</button></div>`;
  const next = $<HTMLButtonElement>("next");
  const update = () => {
    SUS_ITEMS.forEach((_, i) => {
      const c = card.querySelector<HTMLInputElement>(`input[name="sus-${i}"]:checked`);
      answers[i] = c ? Number(c.value) : null;
    });
    result.blocks[block].sus_score = susScore(answers);
    next.disabled = result.blocks[block].sus_score === null;
  };
  $<HTMLFormElement>("sus").addEventListener("change", update);
  update();
  next.addEventListener("click", () => go(at + 1));
}

function renderFinal(): void {
  const options = [
    ["texto", "Texto sin procesar"],
    ["medra", "MeDRA"],
    ["igual", "Me da igual"],
  ];
  card.innerHTML = `
    <p class="eyebrow">Para terminar</p>
    <h1>¿Con cuál preferirías leer el razonamiento de un modelo?</h1>
    <fieldset class="choice">
      <legend class="sr-only">Preferencia</legend>
      ${options.map(([v, l]) => `<label class="check"><input type="radio" name="pref" value="${v}"> ${l}</label>`).join("")}
    </fieldset>
    <label class="field-row"><span>¿Por qué?</span><textarea id="reason" rows="3"></textarea></label>
    <label class="field-row"><span>¿Algo que te haya confundido o que cambiarías en MeDRA? (opcional)</span>
      <textarea id="comments" rows="3"></textarea></label>
    <div class="actions"><button class="primary" id="next" type="button" disabled>Enviar resultados</button></div>`;
  const next = $<HTMLButtonElement>("next");
  card.querySelectorAll<HTMLInputElement>('input[name="pref"]').forEach((r) => r.addEventListener("change", () => (next.disabled = false)));
  next.addEventListener("click", () => {
    result.final = {
      preference: card.querySelector<HTMLInputElement>('input[name="pref"]:checked')?.value ?? null,
      reason: $<HTMLTextAreaElement>("reason").value.trim(),
      comments: $<HTMLTextAreaElement>("comments").value.trim(),
    };
    go(at + 1);
  });
}

function download(): void {
  const blob = new Blob([JSON.stringify(result, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `medra-estudio-${result.participant}.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}

async function submit(): Promise<void> {
  result.finished_at ??= new Date().toISOString();
  card.innerHTML = `<h1>Enviando…</h1>`;
  let saved: string | null = null;
  let error = "";
  try {
    const res = await fetch(`${BACKEND}/study/results`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(result),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    saved = ((await res.json()) as { saved: string }).saved;
    submitted = true;
  } catch (err) {
    error = (err as Error).message;
  }
  card.innerHTML = saved
    ? `<h1>¡Gracias!</h1>
       <p>Tus resultados se han guardado. Ya puedes cerrar esta pestaña.</p>
       <p class="muted">Referencia: ${esc(saved)}</p>
       <div class="actions"><button id="copy" type="button">Descargar una copia</button></div>`
    : `<h1>No se pudieron enviar los resultados</h1>
       <p class="study-error">Error: ${esc(error)}. No cierres la pestaña: descarga el archivo y envíaselo a la persona
          que dirige la prueba, o vuelve a intentarlo.</p>
       <div class="actions"><button id="copy" type="button">Descargar resultados</button>
         <button class="primary" id="retry" type="button">Reintentar</button></div>`;
  $<HTMLButtonElement>("copy").addEventListener("click", download);
  $("retry")?.addEventListener("click", () => void submit());
}

// Leaving mid-session would lose the answers (they are only sent at the end).
addEventListener("beforeunload", (e) => {
  if (at > 0 && !submitted) e.preventDefault();
});

// Same theme as the dashboard (its toggle saves the choice).
try {
  const saved = localStorage.getItem("medra-theme");
  if (saved === "light" || saved === "dark") document.documentElement.dataset.theme = saved;
} catch {
  /* storage unavailable: keep the default */
}

go(0);
