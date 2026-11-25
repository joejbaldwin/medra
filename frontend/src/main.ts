// Dashboard (Layer 4). It renders what the backend sends and contains no
// mining or sizing logic: text arrives raw, visual decisions arrive as
// ViewUpdate diffs from the presenter. Links go both ways: selecting a
// concept, topic or step highlights its words and paragraphs in the text;
// clicking a mention in the text selects its concept.
//
// Layout: the chat window (prompt, reasoning, answer, composer) and the
// visualization windows sit on pages managed by dashboard.ts. Every open
// visualization is a panel (panels.ts) that follows the same session state.
import "./styles.css";
import { sourceIcon } from "./brand";
import type { SampleInfo, ServerMessage, SessionConfig, SessionCreated, SourceInfo, ViewUpdate } from "./contracts";
import { Dashboard } from "./dashboard";
import type { VizKind } from "./layout";
import { createPanel, type Active, type Panel, type Selection, type Session } from "./panels";
import { Picker } from "./picker";
import type { Mark } from "./spans";
import { ViewState } from "./state";
import { SourceMenu } from "./sourceMenu";
import { statsHtml } from "./statsView";
import { stepTypeEs } from "./stepGraph";
import { TextPane, type Block } from "./textPane";
import { Tour } from "./tour";
import type { Segmenting, TimelineSelection } from "./timeline";
import { esc } from "./util";

// Same origin in development (Vite proxies to the backend). Set at build time for deployment.
const BACKEND = (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "";

// Study mode (index.html?estudio=1&traza=ID&velocidad=WPS[&guia=1]): the user
// study page (estudio.html, study.ts) embeds the dashboard in an iframe. The
// trace replays by itself, the source and trace pickers and the composer are
// hidden, and the parent page hears when the replay is done and when a view
// item is selected. With guia=1 (the practice) a guided tour opens first.
const STUDY = (() => {
  const q = new URLSearchParams(location.search);
  if (q.get("estudio") !== "1") return null;
  return {
    trace: q.get("traza") ?? "",
    wordsPerSecond: Number(q.get("velocidad") ?? "15") || 0,
    tour: q.get("guia") === "1",
  };
})();
if (STUDY) document.documentElement.classList.add("study-mode");

function studyEvent(event: string, detail: Record<string, string> = {}): void {
  if (STUDY && window.parent !== window) window.parent.postMessage({ source: "medra-study", event, ...detail }, location.origin);
}

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const els = {
  source: $<HTMLSelectElement>("source"),
  sample: $<HTMLSelectElement>("sample"),
  sampleField: $<HTMLLabelElement>("sample-field"),
  theme: $<HTMLButtonElement>("theme"),
  chatScroll: $<HTMLDivElement>("chat-scroll"),
  chatEmpty: $<HTMLDivElement>("chat-empty"),
  userMsg: $<HTMLDivElement>("user-msg"),
  prompt: $<HTMLParagraphElement>("prompt"),
  reasoningBlock: $<HTMLDivElement>("reasoning-block"),
  modeBadge: $<HTMLSpanElement>("mode-badge"),
  answerBlock: $<HTMLDivElement>("answer-block"),
  answer: $<HTMLDivElement>("answer"),
  chatError: $<HTMLParagraphElement>("chat-error"),
  chatNotice: $<HTMLParagraphElement>("chat-notice"),
  progress: $<HTMLParagraphElement>("chat-progress"),
  progressText: $<HTMLSpanElement>("chat-progress-text"),
  status: $<HTMLSpanElement>("status"),
  reasoningIcon: $<HTMLSpanElement>("reasoning-icon"),
  statsOpen: $<HTMLButtonElement>("stats-open"),
  statsDialog: $<HTMLDialogElement>("stats-dialog"),
  statsBody: $<HTMLDivElement>("stats-body"),
  statsSession: $<HTMLSpanElement>("stats-session"),
  composer: $<HTMLFormElement>("composer"),
  input: $<HTMLTextAreaElement>("composer-input"),
  inputLabel: $<HTMLLabelElement>("composer-label"),
  send: $<HTMLButtonElement>("send"),
  composerSource: $<HTMLSpanElement>("composer-source"),
  speedField: $<HTMLSpanElement>("speed-field"),
  speed: $<HTMLSelectElement>("speed"),
  hint: $<HTMLSpanElement>("composer-hint"),
  announcer: $<HTMLDivElement>("announcer"),
  toast: $<HTMLDivElement>("toast"),
};

const state = new ViewState();
const text = new TextPane($<HTMLDivElement>("stream"), els.chatScroll);
const panels = new Set<Panel>();

// Session state
let ws: WebSocket | null = null;
let reasoning = "";
let answer = "";
let language: string | null = null;
let traceTitle = ""; // what the statistics popup calls the current trace
let live = false;
let textQueued = false;
// A session is running from the moment it is sent until it ends, fails or is
// stopped; meanwhile the send button is a stop button. The token tells a
// request that comes back after a stop (or a newer send) that it is stale.
let running = false;
let token = 0;

// Selection: a clicked concept, topic or step stays selected; hovering (or
// focusing) a bubble previews it.
let selected: Selection = null;
let hovered: string | null = null;

type StatusState = "idle" | "live" | "done" | "stopped" | "error";
function setStatus(s: StatusState, label: string): void {
  els.status.dataset.state = s;
  els.status.textContent = label;
}

function setRunning(on: boolean): void {
  running = on;
  els.send.classList.toggle("stop", on);
  const label = on ? "Detener" : "Enviar";
  els.send.setAttribute("aria-label", label);
  els.send.title = label;
  els.modeBadge.classList.toggle("running", on);
}

// ---------------------------------------------------------------- progress

// Before any text arrives the page can wait a while: the Cloud Run server is
// scaled to zero and takes a few seconds to start (and load spaCy) after a
// quiet spell, and a live model can take time to begin. A line in the chat
// says what it is waiting for, so the page never looks frozen. Each step is
// [delay in ms, message]: later steps replace earlier ones if the wait drags on.
let progressTimers: number[] = [];
function progress(steps: [number, string][]): void {
  for (const t of progressTimers) clearTimeout(t);
  progressTimers = [];
  els.progress.hidden = true;
  for (const [after, message] of steps) {
    const show = () => {
      els.progressText.textContent = message;
      els.progress.hidden = false;
    };
    if (after <= 0) show();
    else progressTimers.push(window.setTimeout(show, after));
  }
}

const WAKING = "Arrancando el servidor de análisis…";
const WAKING_SLOW = "Arrancando el servidor de análisis… Se apaga tras un rato sin uso y tarda unos segundos en volver.";

// ---------------------------------------------------------------- word positions

/** First word of each segment, from the step word counts (the timeline's x axis). */
function segmenting(): Segmenting {
  const starts: number[] = [];
  let total = 0;
  for (const s of state.orderedSteps()) {
    starts.push(total);
    total += s.words;
  }
  return { starts, current: total };
}

/** Approximate word position of a character offset (for the timeline's ticks). */
function wordAt(offset: number, segs: Segmenting): number {
  const ordered = state.orderedSteps();
  for (let i = 0; i < ordered.length; i++) {
    const p = state.paragraphs.get(ordered[i].segment_id);
    if (p && offset >= p.start && offset < p.end) {
      return segs.starts[i] + ((offset - p.start) / Math.max(1, p.end - p.start)) * ordered[i].words;
    }
  }
  return segs.current;
}

// ---------------------------------------------------------------- selection

function select(next: Selection, scroll: boolean): void {
  const same = selected && next && selected.kind === next.kind && selected.id === next.id;
  selected = same ? null : next;
  if (next) studyEvent("select", { kind: next.kind });
  if (selected && scroll) {
    if (selected.kind === "node") text.scrollToFirst(selected.id);
    if (selected.kind === "step") text.scrollToSegment(selected.id);
    if (selected.kind === "topic") {
      const first = state.orderedParagraphs().find((p) => p.topic_id === selected!.id);
      if (first) text.scrollToSegment(first.segment_id);
    }
  }
  refreshActive();
}

/** The selection as every view needs it. */
function active(): Active {
  const selectedNode = selected?.kind === "node" ? selected.id : null;
  const topic = selected?.kind === "topic" ? selected.id : null;
  const step = selected?.kind === "step" ? selected.id : null;
  const node = hovered ?? selectedNode;

  const segs = segmenting();
  let chart: TimelineSelection = null;
  if (topic) chart = { kind: "topic", id: topic };
  if (step !== null) {
    const i = state.orderedSteps().findIndex((s) => s.segment_id === step);
    chart = { kind: "step", start: segs.starts[i], end: segs.starts[i + 1] ?? segs.current, slot: state.slotOf(state.steps.get(step)?.topic_id) };
  }
  if (node) {
    chart = { kind: "node", words: state.nodeSpans(node).map(([a]) => wordAt(a, segs)), slot: state.nodes.get(node)!.colour_slot };
  }
  return { node, neighbours: node ? state.neighbours(node) : new Set(), selectedNode, hovered, topic, step, chart };
}

function refreshActive(): void {
  // Drop a selection whose item disappeared (e.g. a provisional segment merged).
  if (selected?.kind === "node" && !state.nodes.has(selected.id)) selected = null;
  if (selected?.kind === "topic" && !state.topics.has(selected.id)) selected = null;
  if (selected?.kind === "step" && !state.steps.has(selected.id)) selected = null;
  if (hovered && !state.nodes.has(hovered)) hovered = null;

  const a = active();
  const segments = new Set<number>();
  if (a.step !== null) segments.add(a.step);
  if (a.topic) for (const p of state.paragraphs.values()) if (p.topic_id === a.topic) segments.add(p.segment_id);
  text.setActive(a.node, segments);
  for (const p of panels) p.setActive(a);
}

text.onSelect = (id) => select({ kind: "node", id }, false);

const session: Session = {
  state,
  text: () => reasoning,
  live: () => live,
  segmenting,
  select,
  hover: (id) => {
    hovered = id;
    refreshActive();
  },
};

/** A window opened: build its panel from the session so far. */
function openPanel(kind: VizKind): { el: HTMLElement; destroy(): void } {
  const panel = createPanel(kind, session);
  panels.add(panel);
  panel.setActive(active());
  return {
    el: panel.el,
    destroy: () => {
      panels.delete(panel);
      panel.destroy();
    },
  };
}

// ---------------------------------------------------------------- statistics popup

// The popup redraws only while it is open; opening it draws the current state.
function renderStats(): void {
  if (!els.statsDialog.open) return;
  els.statsBody.innerHTML = statsHtml(state, reasoning);
  const parts = [traceTitle, language ? `idioma ${language}` : ""].filter(Boolean);
  els.statsSession.textContent = parts.length ? parts.join(" · ") : "Ninguna traza todavía.";
}

els.statsOpen.addEventListener("click", () => {
  els.statsDialog.showModal();
  renderStats();
});
els.statsDialog.querySelector(".stats-close")!.addEventListener("click", () => els.statsDialog.close());
// A click on the backdrop (the dialog element itself, outside its inner box) closes it.
els.statsDialog.addEventListener("click", (e) => {
  if (e.target === els.statsDialog) els.statsDialog.close();
});
// The browser returns focus to the opener itself; "close" arrives a task later,
// so only step in when focus was lost (and never take it from where it went since).
els.statsDialog.addEventListener("close", () => {
  if (!document.activeElement || document.activeElement === document.body) els.statsOpen.focus();
});

// ---------------------------------------------------------------- messages

function applyView(view: ViewUpdate): void {
  state.apply(view);
  for (const p of panels) p.sync(view);

  const blocks: Block[] = state.orderedParagraphs().map((p, i) => {
    const step = state.steps.get(p.segment_id);
    return {
      segment_id: p.segment_id,
      start: p.start,
      end: p.end,
      label: `Tramo ${i + 1} · ${stepTypeEs(step?.step_type)}`,
      slot: state.slotOf(p.topic_id),
      provisional: p.provisional,
    };
  });
  const marks: Mark[] = [];
  for (const h of state.highlights.values()) {
    if (h.kind === "node") for (const [start, end] of h.spans) marks.push({ start, end, id: h.id });
  }
  for (const s of state.orderedSteps()) {
    if (s.marker_span) marks.push({ start: s.marker_span[0], end: s.marker_span[1], id: `mk:${s.segment_id}`, marker: true });
  }
  text.setView(reasoning, state.committedUpto, blocks, marks);

  if (state.stats) {
    const shares = Object.entries(state.stats.extra).filter(([k]) => k.startsWith("share_"));
    if (shares.length) language = shares.sort((a, b) => b[1] - a[1])[0][0].slice(6);
  }
  renderStats();
  refreshActive();
}

function scheduleText(): void {
  if (textQueued) return;
  textQueued = true;
  requestAnimationFrame(() => {
    textQueued = false;
    const follow = text.atBottom();
    text.setText(reasoning);
    els.answer.innerHTML = renderAnswer(answer);
    els.answerBlock.hidden = answer === "";
    if (follow) els.chatScroll.scrollTop = els.chatScroll.scrollHeight;
  });
}

function handle(msg: ServerMessage): void {
  switch (msg.type) {
    case "hello":
      // A recorded trace carries its original prompt: show that one.
      if (msg.prompt) showUserMessage(msg.prompt);
      if (msg.title) traceTitle = msg.title;
      renderStats();
      break;
    case "text":
      if (!els.progress.hidden && msg.chunk.text) progress([]);
      if (msg.chunk.channel === "reasoning") reasoning += msg.chunk.text;
      else if (msg.chunk.channel === "answer") answer += msg.chunk.text;
      scheduleText();
      break;
    case "view":
      applyView(msg.view);
      break;
    case "mining":
      break; // debug channel, not shown yet
    case "end":
      finish();
      setStatus("done", "Terminado");
      break;
    case "error":
      finish();
      setStatus("error", "Error");
      showError(msg.message);
      break;
  }
}

// ---------------------------------------------------------------- chat

type Mode = "replay" | "paste" | "live";
const modeOf = (source: string): Mode => (source === "paste" ? "paste" : source === "replay" ? "replay" : "live");

function showUserMessage(s: string): void {
  els.prompt.textContent = s;
  els.userMsg.hidden = !s;
}

function showError(message: string): void {
  els.chatError.textContent = message;
  els.chatError.hidden = false;
  els.chatEmpty.hidden = true;
}

/** The stream is over (ended, failed or stopped): settle every view on what arrived. */
function finish(): void {
  progress([]);
  live = false;
  setRunning(false);
  text.setStreaming(false);
  for (const p of panels) p.refresh();
  refreshActive();
  renderStats();
  // The chat follows the stream to the end; in the study the trace must start
  // at the top, like the plain-text condition.
  if (STUDY) {
    els.chatScroll.scrollTop = 0;
    requestAnimationFrame(() => (els.chatScroll.scrollTop = 0)); // after the last render
  }
  studyEvent("done");
  tour?.setReady();
}

/** Abort the running session. Closing the socket stops a replay at the
 *  server and cancels a live model's request; what arrived so far stays. */
function stop(): void {
  if (!running) return;
  token++;
  const socket = ws;
  ws = null;
  socket?.close(1000, "stopped by the user");
  finish();
  setStatus("stopped", "Detenido");
  els.chatNotice.textContent = reasoning || answer ? "Detenido por el usuario: el análisis cubre el texto recibido hasta aquí." : "Detenido por el usuario antes de recibir texto.";
  els.chatNotice.hidden = false;
}

function resetSession(): void {
  ws?.close();
  ws = null;
  reasoning = answer = "";
  language = null;
  live = false;
  selected = null;
  hovered = null;
  state.reset();
  for (const p of panels) p.reset();
  text.reset();
  els.answer.textContent = "";
  els.answerBlock.hidden = true;
  els.chatError.hidden = true;
  els.chatNotice.hidden = true;
  showUserMessage("");
  traceTitle = "";
  renderStats();
  refreshActive();
}

function sessionConfig(): SessionConfig | string {
  const source = els.source.value as SessionConfig["source"];
  const config: SessionConfig = {
    source,
    sample: null,
    text: null,
    prompt: null,
    words_per_second: STUDY ? STUDY.wordsPerSecond : Number(els.speed.value),
    chunking: "word",
    seed: 0,
  };
  if (source === "replay") config.sample = els.sample.value;
  if (source === "paste") config.text = els.input.value;
  if (source === "deepseek") config.prompt = els.input.value;
  const input = config.sample ?? config.text ?? config.prompt ?? "";
  if (!input.trim()) return source === "paste" ? "Pega primero un texto." : source === "replay" ? "Elige primero una traza." : "Escribe primero una pregunta.";
  return config;
}

// ---------------------------------------------------------------- access code

// The deployed backend asks for an access code before a live DeepSeek session
// (it spends the group's credit). The code is kept for this tab only and sent
// in a header; the server checks it and counts the daily budget.
const CODE_KEY = "medra.accessCode";
const codeDialog = $<HTMLDialogElement>("code-dialog");
const codeInput = $<HTMLInputElement>("code-input");

function askAccessCode(): Promise<string | null> {
  return new Promise((resolve) => {
    codeInput.value = "";
    const cancel = codeDialog.querySelector<HTMLButtonElement>(".code-cancel")!;
    const onCancel = () => codeDialog.close("cancel");
    cancel.addEventListener("click", onCancel, { once: true });
    codeDialog.addEventListener(
      "close",
      () => {
        cancel.removeEventListener("click", onCancel);
        const code = codeInput.value.trim();
        resolve(codeDialog.returnValue === "ok" && code ? code : null);
      },
      { once: true },
    );
    codeDialog.returnValue = "";
    codeDialog.showModal();
    codeInput.focus();
  });
}

/** The access code for a session from `source`: undefined if none is needed, null if the user cancelled. */
async function accessCodeFor(source: string): Promise<string | null | undefined> {
  if (!sourceInfo.find((s) => s.id === source)?.needs_code) return undefined;
  const stored = sessionStorage.getItem(CODE_KEY);
  if (stored) return stored;
  const code = await askAccessCode();
  if (code) sessionStorage.setItem(CODE_KEY, code);
  return code;
}

async function start(): Promise<void> {
  const config = sessionConfig();
  if (typeof config === "string") {
    setHint(config, true);
    els.input.focus();
    return;
  }
  const code = await accessCodeFor(config.source);
  if (code === null) {
    setHint("Hace falta un código de acceso para preguntar al modelo.", true);
    return;
  }
  resetSession();
  const mine = ++token;
  setRunning(true);
  const mode = modeOf(config.source);
  // One prompt, one session: sending again replaces the conversation.
  els.chatEmpty.hidden = true;
  if (mode === "paste") {
    const words = (config.text!.match(/\S+/g) ?? []).length;
    showUserMessage(`Texto pegado · ${words.toLocaleString("es")} palabras`);
  } else showUserMessage(mode === "replay" ? (currentSample()?.prompt ?? "") : config.prompt!);
  const speed = els.speed.selectedOptions[0]?.text ?? "";
  els.modeBadge.textContent =
    mode === "live" ? sourceLabel(config.source) : `${mode === "replay" ? "traza grabada" : "texto pegado"} · ${speed}`;
  els.modeBadge.dataset.mode = mode;
  // The reasoning is signed by its author: the model's logo for DeepSeek, a sparkle otherwise.
  els.reasoningIcon.innerHTML = config.source === "deepseek" ? sourceIcon("deepseek", 22) : SPARKLE;
  traceTitle = mode === "replay" ? (currentSample()?.title ?? "Traza grabada") : mode === "paste" ? "Texto pegado" : sourceLabel(config.source);
  els.reasoningBlock.hidden = false;
  setStatus("idle", "Conectando…");
  // A warm server answers at once; if it takes longer, it is starting up.
  progress([[0, "Conectando con el servidor…"], [2000, WAKING], [9000, WAKING_SLOW]]);
  if (mode === "live") els.input.value = ""; // the question now shows as a message
  autoGrow();
  try {
    const res = await fetch(`${BACKEND}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(code ? { "X-Access-Code": code } : {}) },
      body: JSON.stringify(config),
    });
    if (!res.ok) {
      if (res.status === 401) sessionStorage.removeItem(CODE_KEY); // wrong code: ask again next time
      const detail = await res.json().then((b: { detail?: unknown }) => b.detail, () => null);
      throw new Error(typeof detail === "string" ? detail : `HTTP ${res.status}`);
    }
    const { session_id } = (await res.json()) as SessionCreated;
    if (mine !== token) return; // stopped (or replaced) while the session was being created
    const wsBase = BACKEND ? BACKEND.replace(/^http/, "ws") : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
    const socket = new WebSocket(`${wsBase}/sessions/${session_id}`);
    ws = socket;
    progress([[0, "Abriendo la sesión…"]]);
    socket.onopen = () => {
      live = true;
      text.setStreaming(true);
      if (mode === "live") {
        const model = sourceLabel(config.source);
        progress([
          [0, `Pregunta enviada a ${model}. Esperando su respuesta…`],
          [12000, `${model} todavía no ha empezado a escribir; a veces tarda cuando está saturado.`],
        ]);
      } else progress([[0, "Preparando la reproducción…"]]);
      // Recorded and pasted text is a replay; only a model generates live.
      setStatus("live", mode === "live" ? "En directo" : "Reproduciendo");
    };
    socket.onmessage = (e) => {
      if (ws === socket) handle(JSON.parse(e.data as string) as ServerMessage);
    };
    socket.onclose = () => {
      if (ws !== socket || !running) return;
      finish();
      setStatus("error", "Conexión cerrada");
    };
  } catch (err) {
    if (mine !== token) return;
    progress([]);
    setRunning(false);
    setStatus("error", "No iniciada");
    showError(`No se pudo iniciar la sesión: ${(err as Error).message}`);
  }
}

// ---------------------------------------------------------------- composer

// What the user typed for each editable mode, kept when switching sources.
const drafts: Record<"paste" | "live", string> = { paste: "", live: "" };
let shownMode: Mode | null = null;
let samples: SampleInfo[] = [];
let sourceInfo: SourceInfo[] = [];

function currentSample(): SampleInfo | undefined {
  return samples.find((s) => s.id === els.sample.value);
}

function sourceLabel(id: string): string {
  return sourceInfo.find((s) => s.id === id)?.label ?? els.source.selectedOptions[0]?.text ?? id;
}

const HINTS: Record<Mode, string> = {
  replay: "Enviar para reproducir la traza",
  paste: "Ctrl+Intro para reproducir el texto",
  live: "Intro para enviar · Mayús+Intro, nueva línea",
};

function setHint(message: string, error = false): void {
  els.hint.textContent = message;
  els.hint.classList.toggle("error", error);
}

/** Set the composer up for the chosen source: a recorded trace's prompt, a box
 *  to paste reasoning into, or a question for a live model. */
function updateComposer(): void {
  const source = els.source.value;
  const mode = modeOf(source);
  if (shownMode === "paste" || shownMode === "live") drafts[shownMode] = els.input.value;
  els.sampleField.hidden = mode !== "replay";
  els.speedField.hidden = mode === "live"; // a live model sets its own pace
  els.input.readOnly = mode === "replay";
  els.input.maxLength = mode === "paste" ? 100_000 : 4_000;
  els.input.value = mode === "replay" ? (currentSample()?.prompt || "") : drafts[mode];
  els.input.placeholder = {
    replay: samples.length ? "Esta traza no incluye su pregunta original." : "Elige una traza.",
    paste: "Pega un razonamiento (por ejemplo, el texto de <think>…</think> de un modelo). Se reproduce como si se estuviera escribiendo.",
    live: "Pregunta al modelo; verás su razonamiento mientras lo escribe.",
  }[mode];
  els.inputLabel.textContent = { replay: "Pregunta de la traza", paste: "Texto para reproducir", live: "Pregunta para el modelo" }[mode];
  els.composerSource.innerHTML = `${sourceIcon(source, 16)}<span>${esc(sourceLabel(source))}</span>`;
  // The source's note (e.g. that live questions go to a third-party API) is a tooltip, not a line of text.
  els.composerSource.title = sourceInfo.find((s) => s.id === source)?.note ?? "";
  setHint(HINTS[mode]);
  shownMode = mode;
  autoGrow();
}

function autoGrow(): void {
  const max = shownMode === "paste" ? 220 : 140;
  els.input.style.height = "auto";
  els.input.style.height = `${Math.min(max, els.input.scrollHeight)}px`;
}

els.composer.addEventListener("submit", (e) => {
  e.preventDefault();
  if (running) stop();
  else void start();
});
els.input.addEventListener("input", () => {
  autoGrow();
  if (els.hint.classList.contains("error") && shownMode) setHint(HINTS[shownMode]);
});
els.input.addEventListener("keydown", (e) => {
  // While a session runs, Enter does not send (nor stop): only the button stops.
  if (e.key !== "Enter" || e.isComposing || running) return;
  // Pasted text has line breaks of its own, so it needs Ctrl+Enter.
  const send = shownMode === "paste" ? e.ctrlKey || e.metaKey : !e.shiftKey;
  if (!send) return;
  e.preventDefault();
  els.composer.requestSubmit();
});
els.source.addEventListener("change", updateComposer);
els.sample.addEventListener("change", updateComposer);

// ---------------------------------------------------------------- sources

const sourceMenu = new SourceMenu($("source-menu"), els.source, "source-label");

const SPARKLE =
  `<svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true"><path d="M10 3.5l1.6 4.6a3 3 0 0 0 1.8 1.8L18 11.5l-4.6 1.6a3 3 0 0 0-1.8 1.8L10 19.5l-1.6-4.6a3 3 0 0 0-1.8-1.8L2 11.5l4.6-1.6a3 3 0 0 0 1.8-1.8z" fill="currentColor"/>` +
  `<path d="M18.5 2l.7 1.8 1.8.7-1.8.7-.7 1.8-.7-1.8-1.8-.7 1.8-.7zM19 15.5l.6 1.4 1.4.6-1.4.6-.6 1.4-.6-1.4-1.4-.6 1.4-.6z" fill="currentColor"/></svg>`;

async function loadSources(): Promise<void> {
  try {
    const res = await fetch(`${BACKEND}/sources`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    sourceInfo = (await res.json()) as SourceInfo[];
  } catch {
    return; // keep the two built-in options; loadSamples reports the backend as unavailable
  }
  // Rebuilding the menu resets it to the first option: keep the user's choice if it still exists.
  const chosen = els.source.value;
  els.source.replaceChildren(
    ...sourceInfo.map((s) => {
      const option = new Option(s.available ? s.label : `${s.label} (no disponible)`, s.id);
      option.disabled = !s.available;
      return option;
    }),
  );
  if (sourceInfo.some((s) => s.id === chosen && s.available)) els.source.value = chosen;
  els.source.dataset.loaded = "true";
  sourceMenu.refresh();
  updateComposer();
}

// The trace selected on load (Joe, 2026-11-02): «Sum of the first 100 odd numbers».
const DEFAULT_SAMPLE = "odd-sum-en";

async function loadSamples(): Promise<void> {
  // The first request after a quiet spell wakes the server: say so if it is slow.
  progress([[800, WAKING], [8000, WAKING_SLOW]]);
  try {
    const res = await fetch(`${BACKEND}/datasets`);
    progress([]);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    samples = (await res.json()) as SampleInfo[];
    els.sample.replaceChildren(...samples.map((s) => new Option(`${s.title} (${s.language}, ${s.words} palabras)`, s.id)));
    if (samples.some((s) => s.id === DEFAULT_SAMPLE)) els.sample.value = DEFAULT_SAMPLE;
    updateComposer();
    if (STUDY && samples.some((s) => s.id === STUDY.trace)) {
      els.source.value = "replay";
      els.sample.value = STUDY.trace;
      updateComposer();
      void start();
    }
  } catch {
    progress([]);
    setStatus("error", "Backend no disponible");
    showError("No se puede conectar con el servidor de análisis. Comprueba que el backend está en marcha.");
    els.send.disabled = true;
  }
}

// ---------------------------------------------------------------- dashboard, theme

let toastTimer = 0;
function notify(message: string, visible = false): void {
  // Re-set the text so a repeated message is announced again.
  els.announcer.textContent = "";
  requestAnimationFrame(() => (els.announcer.textContent = message));
  if (!visible) return;
  els.toast.textContent = message;
  els.toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => (els.toast.hidden = true), 4500);
}

const picker = new Picker($<HTMLDialogElement>("picker"));
const dashboard: Dashboard = new Dashboard({
  root: $("pages"),
  pager: $("pager"),
  pagerAdd: $<HTMLButtonElement>("pager-add"),
  chat: $("chat-win"),
  chatToggle: $<HTMLButtonElement>("chat-toggle"),
  createPanel: openPanel,
  notify,
  openPicker: (page, cell, origin) =>
    picker.open({ present: dashboard.kindsOn(page), origin, onSelect: (kind) => dashboard.add(page, cell, kind) }),
});
// In the study every participant starts from the same layout: concept map and
// step graph next to the chat, the topic timeline on page 2.
if (STUDY) dashboard.openViews([["map", "steps"], ["timeline"]]);

// The practice's guided tour: welcome, then the text, the two views next to it
// and the page bar. The study page can ask for it again ("Ver la guía otra vez").
const onPage = (selector: string) => () => document.querySelector(`.page:not([hidden]) ${selector}`);
const tour = STUDY?.tour
  ? new Tour(
      [
        {
          title: "Te damos la bienvenida a MeDRA",
          text: "MeDRA ordena el razonamiento de un modelo de IA en conceptos, pasos y temas, todos enlazados con el texto. Te lo enseñamos en un momento.",
          next: "Empezar",
        },
        {
          target: () => $("chat-win"),
          title: "El razonamiento",
          text: "La pregunta, lo que el modelo piensa y su respuesta. El texto va en tramos, cada uno con su tipo de paso. Las palabras subrayadas son conceptos.",
        },
        {
          target: onPage("[data-win='map']"),
          title: "Mapa de conceptos",
          text: "Cada burbuja es un concepto: cuanto más grande, más aparece. Pulsa una y verás dónde se menciona en el texto.",
        },
        {
          target: onPage("[data-win='steps']"),
          title: "Cadena de razonamiento",
          text: "Los pasos del modelo en orden, uno por tramo. Pulsa un paso para ir a ese tramo del texto.",
        },
        {
          target: () => document.querySelector(".pager"),
          title: "Más vistas",
          text: "En la página 2 está la línea de temas. Con + puedes abrir otra página y añadir la visualización que quieras.",
        },
        {
          title: "Ahora prueba tú",
          text: "Pulsa una burbuja, un paso y una palabra subrayada. Tómate un par de minutos.",
          next: "Explorar",
        },
      ],
      () => studyEvent("tour-done"),
    )
  : null;
tour?.start();
addEventListener("message", (e: MessageEvent) => {
  const data = e.data as { source?: string; event?: string };
  if (e.origin !== location.origin || data?.source !== "medra-study-page") return;
  if (data.event === "tour" && tour && !tour.running) {
    dashboard.openViews([["map", "steps"], ["timeline"]]); // back to the layout the tour points at
    tour.start();
  }
});

function initTheme(): void {
  let saved: string | null = null;
  try {
    saved = localStorage.getItem("medra-theme");
  } catch {
    /* storage unavailable: use the default */
  }
  // Light unless the user picked dark before (the system setting is not followed).
  document.documentElement.dataset.theme = saved === "dark" ? "dark" : "light";
  els.theme.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("medra-theme", next);
    } catch {
      /* ignore */
    }
  });
}

/** The answer as the model wrote it, with Markdown bold rendered (the text is escaped first). */
function renderAnswer(s: string): string {
  return esc(s).replace(/\*\*([^*\n]+)\*\*/g, "<b>$1</b>");
}

initTheme();
els.reasoningIcon.innerHTML = SPARKLE;
updateComposer();
void loadSamples();
void loadSources();
