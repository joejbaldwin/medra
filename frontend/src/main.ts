// Dashboard (Layer 4). It renders what the backend sends and contains no
// mining or sizing logic: text arrives raw, visual decisions arrive as
// ViewUpdate diffs from the presenter. Two-way links: hovering or clicking a
// bubble highlights its mentions in the text; clicking a mention selects its bubble.
import "./styles.css";
import { ConceptMap } from "./conceptMap";
import type { SampleInfo, ServerMessage, SessionConfig, SessionCreated, Stats, TickerItem, ViewUpdate } from "./contracts";
import type { Mark } from "./spans";
import { ViewState } from "./state";
import { TextPane } from "./textPane";

// Same origin in development (Vite proxies to the backend). Set at build time for deployment.
const BACKEND = (import.meta.env.VITE_BACKEND_URL as string | undefined) ?? "";

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;
const els = {
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
};

const map = new ConceptMap(document.getElementById("map") as unknown as SVGSVGElement);
const text = new TextPane($<HTMLDivElement>("stream"));
const state = new ViewState();

// Session state
let ws: WebSocket | null = null;
let reasoning = "";
let answer = "";
let language: string | null = null;
let textQueued = false;
// Selection: a clicked bubble stays selected; hovering previews another one.
let selected: string | null = null;
let hovered: string | null = null;

type StatusState = "idle" | "live" | "done" | "error";
function setStatus(s: StatusState, label: string): void {
  els.status.dataset.state = s;
  els.status.textContent = label;
}

// ---------------------------------------------------------------- selection

function toggleSelect(id: string, scroll: boolean): void {
  selected = selected === id ? null : id;
  if (selected && scroll) text.scrollToFirst(selected);
  refreshActive();
}

function refreshActive(): void {
  if (selected && !state.nodes.has(selected)) selected = null;
  if (hovered && !state.nodes.has(hovered)) hovered = null;
  const active = hovered ?? selected;
  map.setActive(active, active ? state.neighbours(active) : new Set(), selected);
  text.setActive(active);
  renderInfo(active);
}

map.onSelect = (id) => toggleSelect(id, true);
map.onHover = (id) => {
  hovered = id;
  refreshActive();
};
text.onSelect = (id) => toggleSelect(id, false);

// ---------------------------------------------------------------- panels

function renderInfo(id: string | null): void {
  const node = id ? state.nodes.get(id) : undefined;
  if (!node) {
    els.mapInfo.textContent = "Selecciona un término para ver sus menciones.";
    return;
  }
  const spans = state.nodeSpans(node.id);
  const forms = [...new Set(spans.map(([a, b]) => reasoning.slice(a, b)))];
  const paragraphs = state.orderedParagraphs();
  const tramos = [...new Set(spans.map(([a]) => paragraphs.findIndex((p) => p.start <= a && a < p.end) + 1))].filter((n) => n > 0);
  const co = [...state.neighbours(node.id)].map((n) => state.nodes.get(n)?.label ?? n);
  els.mapInfo.innerHTML =
    `<span class="sw" style="--c: var(--c${node.colour_slot % 6})">${esc(node.label)}</span> · ` +
    `<b>${node.count}</b> ${node.count === 1 ? "mención" : "menciones"}` +
    (tramos.length ? ` en ${tramos.length === 1 ? "el tramo" : "los tramos"} ${tramos.join(", ")}` : "") +
    (forms.length ? ` · formas: ${forms.map((f) => `«${esc(f)}»`).join(", ")}` : "") +
    (co.length ? ` · coaparece con ${co.map(esc).join(", ")}` : "");
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
    stats.lexical_diversity != null ? `diversidad léxica ${stats.lexical_diversity.toFixed(2)}` : null,
    language ? `idioma ${language}` : null,
  ];
  els.stats.textContent = parts.filter(Boolean).join(" · ");
}

// ---------------------------------------------------------------- messages

function applyView(view: ViewUpdate): void {
  if (view.kind === "snapshot") map.reset();
  state.apply(view);
  map.update(view.nodes, view.removed.nodes, view.edges, view.removed.edges);
  const marks: Mark[] = [];
  for (const h of state.highlights.values()) {
    if (h.kind === "node") for (const [start, end] of h.spans) marks.push({ start, end, id: h.id });
  }
  text.setView(reasoning, state.committedUpto, state.orderedParagraphs(), marks);
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
    els.answer.textContent = answer;
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
      text.setStreaming(false);
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
  selected = hovered = null;
  state.reset();
  map.reset();
  text.reset();
  els.stats.textContent = "";
  els.answerBlock.hidden = true;
  renderTicker();
  refreshActive();
}

async function start(): Promise<void> {
  resetSession();
  const config: SessionConfig = {
    source: "replay",
    sample: els.sample.value,
    words_per_second: Number(els.speed.value),
    chunking: "word",
    seed: 0,
  };
  try {
    const res = await fetch(`${BACKEND}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { session_id } = (await res.json()) as SessionCreated;
    const wsBase = BACKEND ? BACKEND.replace(/^http/, "ws") : `${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`;
    const socket = new WebSocket(`${wsBase}/sessions/${session_id}`);
    ws = socket;
    socket.onopen = () => {
      text.setStreaming(true);
      setStatus("live", "En directo");
    };
    socket.onmessage = (e) => handle(JSON.parse(e.data as string) as ServerMessage);
    socket.onclose = () => {
      if (ws === socket && els.status.dataset.state === "live") setStatus("error", "Conexión cerrada");
    };
  } catch (err) {
    setStatus("error", "Sin conexión");
    els.title.textContent = `No se pudo iniciar la sesión (${(err as Error).message}).`;
  }
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

// ---------------------------------------------------------------- theme

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

function esc(s: string): string {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
}

els.start.addEventListener("click", () => void start());
initTheme();
renderTicker();
void loadSamples();
