// Dashboard (Layer 4). It renders what the backend sends and contains no
// mining or sizing logic: text arrives raw, visual decisions arrive as
// ViewUpdate diffs from the presenter. Links go both ways: selecting a
// concept, topic or step highlights its words and paragraphs in the text;
// clicking a mention in the text selects its concept.
import "./styles.css";
import { ConceptMap } from "./conceptMap";
import type {
  SampleInfo,
  ServerMessage,
  SessionConfig,
  SessionCreated,
  SourceInfo,
  Stats,
  TickerItem,
  ViewUpdate,
} from "./contracts";
import type { Mark } from "./spans";
import { ViewState } from "./state";
import { StepGraph, stepTypeEs } from "./stepGraph";
import { TextPane, type Block } from "./textPane";
import { TimelineChart, type Segmenting, type TimelineSelection } from "./timeline";

// Same origin in development (Vite proxies to the backend). Set at build time for deployment.
const BACKEND = (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "";

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const els = {
  source: $<HTMLSelectElement>("source"),
  sampleField: $<HTMLLabelElement>("sample-field"),
  speedField: $<HTMLLabelElement>("speed-field"),
  inputPanel: $<HTMLElement>("input-panel"),
  pasteBox: $<HTMLDivElement>("paste-box"),
  pasteText: $<HTMLTextAreaElement>("paste-text"),
  promptBox: $<HTMLDivElement>("prompt-box"),
  promptInput: $<HTMLInputElement>("prompt-input"),
  sourceNote: $<HTMLParagraphElement>("source-note"),
  sample: $<HTMLSelectElement>("sample"),
  speed: $<HTMLSelectElement>("speed"),
  start: $<HTMLButtonElement>("start"),
  status: $<HTMLSpanElement>("status"),
  theme: $<HTMLButtonElement>("theme"),
  title: $<HTMLParagraphElement>("title"),
  prompt: $<HTMLParagraphElement>("prompt"),
  answerBlock: $<HTMLDivElement>("answer-block"),
  answer: $<HTMLParagraphElement>("answer"),
  mapInfo: $<HTMLParagraphElement>("map-info"),
  stats: $<HTMLParagraphElement>("stats"),
  ticker: $<HTMLDivElement>("ticker"),
  stepDetail: $<HTMLElement>("step-detail"),
};

const map = new ConceptMap(document.getElementById("map") as unknown as SVGSVGElement);
const chart = new TimelineChart(document.getElementById("chart") as unknown as SVGSVGElement, $("tip"), $("legend"));
const steps = new StepGraph(document.getElementById("steps") as unknown as SVGSVGElement, $("steps-wrap"));
const text = new TextPane($<HTMLDivElement>("stream"));
const state = new ViewState();

// Session state
let ws: WebSocket | null = null;
let reasoning = "";
let answer = "";
let language: string | null = null;
let live = false;
let textQueued = false;

// Selection: a clicked concept, topic or step stays selected; hovering a bubble previews it.
type Selection = { kind: "node"; id: string } | { kind: "topic"; id: string } | { kind: "step"; id: number } | null;
let selected: Selection = null;
let hovered: string | null = null;

type StatusState = "idle" | "live" | "done" | "error";
function setStatus(s: StatusState, label: string): void {
  els.status.dataset.state = s;
  els.status.textContent = label;
}

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

function refreshActive(): void {
  // Drop a selection whose item disappeared (e.g. a provisional segment merged).
  if (selected?.kind === "node" && !state.nodes.has(selected.id)) selected = null;
  if (selected?.kind === "topic" && !state.topics.has(selected.id)) selected = null;
  if (selected?.kind === "step" && !state.steps.has(selected.id)) selected = null;
  if (hovered && !state.nodes.has(hovered)) hovered = null;

  const selectedNode = selected?.kind === "node" ? selected.id : null;
  const topic = selected?.kind === "topic" ? selected.id : null;
  const step = selected?.kind === "step" ? selected.id : null;
  const activeNode = hovered ?? selectedNode;

  map.setActive(activeNode, activeNode ? state.neighbours(activeNode) : new Set(), selectedNode, hovered ? null : topic);
  const segments = new Set<number>();
  if (step !== null) segments.add(step);
  if (topic) for (const p of state.paragraphs.values()) if (p.topic_id === topic) segments.add(p.segment_id);
  text.setActive(activeNode, segments);
  steps.setActive(step, topic);

  const segs = segmenting();
  let chartSel: TimelineSelection = null;
  if (topic) chartSel = { kind: "topic", id: topic };
  if (step !== null) {
    const i = state.orderedSteps().findIndex((s) => s.segment_id === step);
    chartSel = { kind: "step", start: segs.starts[i], end: segs.starts[i + 1] ?? segs.current, slot: state.slotOf(state.steps.get(step)?.topic_id) };
  }
  if (activeNode) {
    const node = state.nodes.get(activeNode)!;
    chartSel = { kind: "node", words: state.nodeSpans(activeNode).map(([a]) => wordAt(a, segs)), slot: node.colour_slot };
  }
  chart.select(chartSel);
  renderInfo(activeNode, topic);
  renderStepDetail(step);
}

map.onSelect = (id) => select({ kind: "node", id }, true);
map.onHover = (id) => {
  hovered = id;
  refreshActive();
};
text.onSelect = (id) => select({ kind: "node", id }, false);
chart.onSelectTopic = (id) => select(id ? { kind: "topic", id } : null, true);
steps.onSelect = (id) => select({ kind: "step", id }, true);

// ---------------------------------------------------------------- panels

function tramosOf(spans: [number, number][]): number[] {
  const paragraphs = state.orderedParagraphs();
  return [...new Set(spans.map(([a]) => paragraphs.findIndex((p) => p.start <= a && a < p.end) + 1))].filter((n) => n > 0);
}

function renderInfo(nodeId: string | null, topicId: string | null): void {
  const node = nodeId ? state.nodes.get(nodeId) : undefined;
  const topic = topicId ? state.topics.get(topicId) : undefined;
  if (node) {
    const spans = state.nodeSpans(node.id);
    const forms = [...new Set(spans.map(([a, b]) => reasoning.slice(a, b)))];
    const tramos = tramosOf(spans);
    const co = [...state.neighbours(node.id)].map((n) => state.nodes.get(n)?.label ?? n);
    const topicName = node.topic_id ? state.topics.get(node.topic_id)?.name : null;
    els.mapInfo.innerHTML =
      `<span class="sw" style="--c: var(--c${node.colour_slot % 6})">${esc(node.label)}</span> · ` +
      `<b>${node.count}</b> ${node.count === 1 ? "mención" : "menciones"}` +
      (tramos.length ? ` en ${tramos.length === 1 ? "el tramo" : "los tramos"} ${tramos.join(", ")}` : "") +
      (topicName ? ` · tema «${esc(topicName)}»` : "") +
      (forms.length ? ` · formas: ${forms.map((f) => `«${esc(f)}»`).join(", ")}` : "") +
      (co.length ? ` · coaparece con ${co.map(esc).join(", ")}` : "");
    return;
  }
  if (topic) {
    const concepts = [...state.nodes.values()].filter((n) => n.topic_id === topic.id).map((n) => n.label);
    const tramos = state.orderedParagraphs().flatMap((p, i) => (p.topic_id === topic.id ? [i + 1] : []));
    els.mapInfo.innerHTML =
      `Tema <span class="sw" style="--c: var(--c${topic.colour_slot % 6})">${esc(topic.name)}</span>` +
      (concepts.length ? ` · conceptos: ${concepts.map(esc).join(", ")}` : "") +
      (tramos.length ? ` · domina ${tramos.length === 1 ? "el tramo" : "los tramos"} ${tramos.join(", ")}` : "");
    return;
  }
  els.mapInfo.textContent = "Selecciona un término para ver sus menciones.";
}

function renderStepDetail(segmentId: number | null): void {
  const ordered = state.orderedSteps();
  const i = ordered.findIndex((s) => s.segment_id === segmentId);
  if (i < 0) {
    els.stepDetail.innerHTML = `<p class="hint">Haz clic en un paso para ver su tipo, el marcador que lo abrió y sus términos con más peso.</p>`;
    return;
  }
  const step = ordered[i];
  const p = state.paragraphs.get(step.segment_id);
  const topic = step.topic_id ? state.topics.get(step.topic_id) : undefined;
  const slot = state.slotOf(step.topic_id);
  const keywords = p?.label ? p.label.split(" · ") : [];
  const back = step.arcs_back_to.map((seg) => ordered.findIndex((s) => s.segment_id === seg) + 1).filter((n) => n > 0);
  const excerpt = p ? reasoning.slice(p.start, Math.min(p.end, p.start + 240)) + (p.end - p.start > 240 ? "…" : "") : "";
  els.stepDetail.style.setProperty("--c", `var(--c${slot % 6})`);
  els.stepDetail.innerHTML =
    `<div class="sd-head"><div class="sd-num">${i + 1}</div><div><h3>${esc(cap(stepTypeEs(step.step_type)))}</h3>` +
    `<p>tramo ${i + 1} · ${step.words} palabras${p?.provisional ? " · provisional" : ""}</p></div>` +
    (topic ? `<span class="sd-tag">${esc(topic.name)}</span>` : "") +
    `</div><div class="sd-grid"><div>` +
    `<h4>Marcador</h4><p class="sd-text">${step.marker ? `<span class="mkq">«${esc(step.marker)}»</span>` : "Ninguno: el corte viene del cambio de vocabulario."}</p>` +
    (back.length ? `<h4>Retoma</h4><p class="sd-text">Vuelve al tema del paso ${back.join(", ")}.</p>` : "") +
    `<h4>Palabras clave (TF-IDF del tramo)</h4><p class="sd-text">${keywords.map(esc).join(" · ") || "—"}</p>` +
    `</div><div><h4>Texto</h4><p class="sd-text">${esc(excerpt)}</p></div></div>`;
}

const POS_ES: Record<string, string> = {
  VERB: "verbo", AUX: "auxiliar", ADV: "adverbio", ADP: "preposición", DET: "determinante",
  PRON: "pronombre", CCONJ: "conjunción", SCONJ: "conjunción", INTJ: "interjección", PART: "partícula",
};

function tickerOutcome(item: TickerItem): string {
  switch (item.outcome) {
    case "term": {
      const node = item.node_id ? state.nodes.get(item.node_id) : undefined;
      return node ? `<em>concepto «${esc(node.label)}»</em>` : "término";
    }
    case "stopword": return "descartada (stopword)";
    case "filler": return "descartada (relleno)";
    case "pos": return `descartada (${esc(POS_ES[item.pos ?? ""] ?? item.pos ?? "categoría")})`;
    case "number": return "descartada (número)";
    default: return "descartada";
  }
}

function renderTicker(): void {
  const rows = state.ticker.slice(-3).reverse();
  els.ticker.innerHTML = rows.length
    ? rows
        .map((t) => {
          const via = t.lemma !== t.form.toLowerCase() ? ` → ${esc(t.lemma)}` : "";
          return `<div>«${esc(t.form)}»${via} → ${tickerOutcome(t)}</div>`;
        })
        .join("")
    : "<div>Esperando texto…</div>";
}

function renderStats(stats: Stats): void {
  const parts = [
    `palabras ${stats.words}`,
    `oraciones ${stats.sentences}`,
    `tramos ${stats.segments}`,
    `temas ${state.topics.size}`,
    stats.lexical_diversity != null ? `diversidad léxica ${stats.lexical_diversity.toFixed(2)}` : null,
    stats.hedges_per_100w != null ? `dudas ${stats.hedges_per_100w.toFixed(1)}/100 pal.` : null,
    language ? `idioma ${language}` : null,
  ];
  els.stats.textContent = parts.filter(Boolean).join(" · ");
}

// ---------------------------------------------------------------- messages

function applyView(view: ViewUpdate): void {
  if (view.kind === "snapshot") map.reset();
  state.apply(view);
  map.update(view.nodes, view.removed.nodes, view.edges, view.removed.edges);

  const ordered = state.orderedSteps();
  const blocks: Block[] = state.orderedParagraphs().map((p, i) => {
    const step = state.steps.get(p.segment_id);
    const kind = stepTypeEs(step?.step_type);
    return {
      segment_id: p.segment_id,
      start: p.start,
      end: p.end,
      label: `Tramo ${i + 1} · ${kind}${p.label ? ` · ${p.label}` : ""}`,
      slot: state.slotOf(p.topic_id),
      provisional: p.provisional,
    };
  });
  const marks: Mark[] = [];
  for (const h of state.highlights.values()) {
    if (h.kind === "node") for (const [start, end] of h.spans) marks.push({ start, end, id: h.id });
  }
  for (const s of ordered) {
    if (s.marker_span) marks.push({ start: s.marker_span[0], end: s.marker_span[1], id: `mk:${s.segment_id}`, marker: true });
  }
  text.setView(reasoning, state.committedUpto, blocks, marks);
  chart.update(state.timeline, state.orderedTopics(), segmenting());
  steps.update(ordered, state.paragraphs, state.topics, live && !view.final);

  if (state.stats) {
    const shares = Object.entries(state.stats.extra).filter(([k]) => k.startsWith("share_"));
    if (shares.length) language = shares.sort((a, b) => b[1] - a[1])[0][0].slice(6);
    renderStats(state.stats);
  }
  renderTicker();
  refreshActive();
}

function scheduleText(): void {
  if (textQueued) return;
  textQueued = true;
  requestAnimationFrame(() => {
    textQueued = false;
    text.setText(reasoning);
    els.answer.innerHTML = renderAnswer(answer);
    els.answerBlock.hidden = answer === "";
  });
}

function handle(msg: ServerMessage): void {
  switch (msg.type) {
    case "hello":
      els.title.textContent = msg.title ?? "Sesión";
      els.prompt.textContent = msg.prompt ?? "";
      els.prompt.hidden = !msg.prompt;
      break;
    case "text":
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
      live = false;
      text.setStreaming(false);
      steps.update(state.orderedSteps(), state.paragraphs, state.topics, false);
      refreshActive();
      setStatus("done", "Terminado");
      break;
    case "error":
      setStatus("error", "Error");
      els.title.textContent = msg.message;
      break;
  }
}

// ---------------------------------------------------------------- session

function resetSession(): void {
  ws?.close();
  ws = null;
  reasoning = answer = "";
  language = null;
  live = false;
  selected = null;
  hovered = null;
  state.reset();
  map.reset();
  chart.reset();
  steps.reset();
  text.reset();
  els.stats.textContent = "";
  els.answerBlock.hidden = true;
  renderTicker();
  refreshActive();
}

function sessionConfig(): SessionConfig | string {
  const source = els.source.value as SessionConfig["source"];
  const config: SessionConfig = {
    source,
    sample: null,
    text: null,
    prompt: null,
    words_per_second: Number(els.speed.value),
    chunking: "word",
    seed: 0,
  };
  if (source === "replay") config.sample = els.sample.value;
  if (source === "paste") config.text = els.pasteText.value;
  if (source === "deepseek" || source === "ollama") config.prompt = els.promptInput.value;
  const input = config.sample ?? config.text ?? config.prompt ?? "";
  if (!input.trim()) return source === "paste" ? "Pega primero un texto." : "Escribe primero una pregunta.";
  return config;
}

async function start(): Promise<void> {
  const config = sessionConfig();
  if (typeof config === "string") {
    els.title.textContent = config;
    return;
  }
  resetSession();
  try {
    const res = await fetch(`${BACKEND}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    if (!res.ok) {
      const detail = await res.json().then((b: { detail?: unknown }) => b.detail, () => null);
      throw new Error(typeof detail === "string" ? detail : `HTTP ${res.status}`);
    }
    const { session_id } = (await res.json()) as SessionCreated;
    const wsBase = BACKEND ? BACKEND.replace(/^http/, "ws") : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
    const socket = new WebSocket(`${wsBase}/sessions/${session_id}`);
    ws = socket;
    socket.onopen = () => {
      live = true;
      text.setStreaming(true);
      setStatus("live", "En directo");
    };
    socket.onmessage = (e) => handle(JSON.parse(e.data as string) as ServerMessage);
    socket.onclose = () => {
      if (ws === socket && els.status.dataset.state === "live") setStatus("error", "Conexión cerrada");
    };
  } catch (err) {
    setStatus("error", "No iniciada");
    els.title.textContent = `No se pudo iniciar la sesión: ${(err as Error).message}`;
  }
}

// ---------------------------------------------------------------- sources

let sourceInfo: SourceInfo[] = [];

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
  showSourceInputs();
}

/** Show the inputs the chosen source needs: a sample, a text box or a question. */
function showSourceInputs(): void {
  const source = els.source.value;
  const live = source === "deepseek" || source === "ollama";
  els.sampleField.hidden = source !== "replay";
  els.speedField.hidden = live; // a live model sets its own pace
  els.inputPanel.hidden = source === "replay";
  els.pasteBox.hidden = source !== "paste";
  els.promptBox.hidden = !live;
  els.sourceNote.textContent = sourceInfo.find((s) => s.id === source)?.note ?? "";
  els.start.textContent = live ? "Preguntar" : "Reproducir";
}

async function loadSamples(): Promise<void> {
  try {
    const res = await fetch(`${BACKEND}/datasets`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const samples = (await res.json()) as SampleInfo[];
    els.sample.replaceChildren(...samples.map((s) => new Option(`${s.title} (${s.language}, ${s.words} palabras)`, s.id)));
  } catch {
    setStatus("error", "Backend no disponible");
    els.start.disabled = true;
  }
}

// ---------------------------------------------------------------- tabs and theme

function initTabs(): void {
  const tabs = [...document.querySelectorAll<HTMLButtonElement>('[role="tab"]')];
  for (const tab of tabs) {
    tab.addEventListener("click", () => {
      for (const t of tabs) {
        const on = t === tab;
        t.setAttribute("aria-selected", String(on));
        $(t.getAttribute("aria-controls")!).hidden = !on;
      }
      // The step graph sizes itself to its container, which has no width while hidden.
      if (tab.dataset.view === "pasos") {
        steps.update(state.orderedSteps(), state.paragraphs, state.topics, live);
        refreshActive();
      }
    });
  }
}

function initTheme(): void {
  let saved: string | null = null;
  try {
    saved = localStorage.getItem("medra-theme");
  } catch {
    /* storage unavailable: follow the system theme */
  }
  if (saved) document.documentElement.dataset.theme = saved;
  els.theme.addEventListener("click", () => {
    const dark =
      document.documentElement.dataset.theme === "dark" ||
      (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    const next = dark ? "light" : "dark";
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

function cap(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function esc(s: string): string {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
}

els.start.addEventListener("click", () => void start());
els.source.addEventListener("change", showSourceInputs);
els.promptInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") void start();
});
initTabs();
initTheme();
renderTicker();
showSourceInputs();
void loadSamples();
void loadSources();
