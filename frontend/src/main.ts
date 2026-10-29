// Dashboard (Layer 4). It renders what the backend sends and contains no
// mining or sizing logic: text arrives raw, visual decisions arrive as
// ViewUpdate diffs from the presenter.
import "./styles.css";
import { ConceptMap } from "./conceptMap";
import type { SampleInfo, ServerMessage, SessionConfig, SessionCreated, Stats, ViewUpdate } from "./contracts";

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
  stream: $<HTMLDivElement>("stream"),
  committed: $<HTMLSpanElement>("committed"),
  pending: $<HTMLSpanElement>("pending"),
  caret: $<HTMLSpanElement>("caret"),
  answerBlock: $<HTMLDivElement>("answer-block"),
  answer: $<HTMLParagraphElement>("answer"),
  stats: $<HTMLParagraphElement>("stats"),
};

const map = new ConceptMap(document.getElementById("map") as unknown as SVGSVGElement);

// Session state
let ws: WebSocket | null = null;
let reasoning = "";
let answer = "";
let committedUpto = 0;
let language: string | null = null;
let renderQueued = false;

type StatusState = "idle" | "live" | "done" | "error";
function setStatus(state: StatusState, label: string): void {
  els.status.dataset.state = state;
  els.status.textContent = label;
}

// ---------------------------------------------------------------- text pane

function scheduleRender(): void {
  if (renderQueued) return;
  renderQueued = true;
  requestAnimationFrame(() => {
    renderQueued = false;
    // Keep following the stream unless the user scrolled up to read.
    const s = els.stream;
    const atBottom = s.scrollHeight - s.scrollTop - s.clientHeight < 40;
    els.committed.textContent = reasoning.slice(0, committedUpto);
    els.pending.textContent = reasoning.slice(committedUpto);
    els.answer.textContent = answer;
    els.answerBlock.hidden = answer === "";
    if (atBottom) s.scrollTop = s.scrollHeight;
  });
}

function renderStats(stats: Stats): void {
  const parts = [
    `palabras ${stats.words}`,
    `oraciones ${stats.sentences}`,
    stats.lexical_diversity != null ? `diversidad léxica ${stats.lexical_diversity.toFixed(2)}` : null,
    language ? `idioma ${language}` : null,
  ];
  els.stats.textContent = parts.filter(Boolean).join(" · ");
}

// ---------------------------------------------------------------- messages

function applyView(view: ViewUpdate): void {
  if (view.kind === "snapshot") map.reset();
  committedUpto = view.committed_upto;
  map.update(view.nodes, view.removed.nodes);
  if (view.stats) renderStats(view.stats);
  scheduleRender();
}

function handle(msg: ServerMessage): void {
  switch (msg.type) {
    case "hello":
      els.title.textContent = msg.title ?? "Sesión";
      els.prompt.textContent = msg.prompt ?? "";
      els.prompt.hidden = !msg.prompt;
      language = msg.language;
      break;
    case "text":
      if (msg.chunk.channel === "reasoning") reasoning += msg.chunk.text;
      else if (msg.chunk.channel === "answer") answer += msg.chunk.text;
      scheduleRender();
      break;
    case "view":
      applyView(msg.view);
      break;
    case "mining":
      break; // debug channel, not shown yet
    case "end":
      els.caret.hidden = true;
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
  committedUpto = 0;
  language = null;
  map.reset();
  els.stats.textContent = "";
  scheduleRender();
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
      els.caret.hidden = false;
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
    els.sample.replaceChildren(
      ...samples.map((s) => new Option(`${s.title} (${s.language}, ${s.words} palabras)`, s.id)),
    );
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

els.start.addEventListener("click", () => void start());
initTheme();
void loadSamples();
