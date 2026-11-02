// The visualizations a dashboard window can hold. A panel wraps one of the D3
// views with its captions and selection details. Any number of panels can be
// open at once (the same view on two pages): each is filled from the session's
// ViewState when it opens and then follows the ViewUpdate diffs, so closing a
// window never loses analysis data. Panels make no visual decisions of their
// own: those come from the presenter, and selection is decided in main.ts.
import { ConceptMap } from "./conceptMap";
import type { ViewUpdate } from "./contracts";
import type { VizKind } from "./layout";
import type { ViewState } from "./state";
import { StepGraph, stepTypeEs } from "./stepGraph";
import { TimelineChart, type Segmenting, type TimelineSelection } from "./timeline";
import { cap, esc } from "./util";

export type Selection = { kind: "node"; id: string } | { kind: "topic"; id: string } | { kind: "step"; id: number } | null;

/** What is selected or hovered right now, worked out once for every panel. */
export interface Active {
  node: string | null; // the hovered bubble, else the selected one
  neighbours: Set<string>; // bubbles linked to `node`
  selectedNode: string | null;
  hovered: string | null;
  topic: string | null;
  step: number | null;
  chart: TimelineSelection;
}

/** What panels can read from the session and do to it. */
export interface Session {
  state: ViewState;
  text(): string; // the reasoning received so far
  live(): boolean;
  segmenting(): Segmenting;
  select(sel: Selection, scroll: boolean): void;
  hover(nodeId: string | null): void;
}

export interface Panel {
  readonly kind: VizKind;
  readonly el: HTMLElement;
  /** Apply one view update (the state has already applied it). */
  sync(view: ViewUpdate): void;
  /** Redraw from the state (the stream ended). */
  refresh(): void;
  /** A new session starts. */
  reset(): void;
  setActive(a: Active): void;
  destroy(): void;
}

export function createPanel(kind: VizKind, session: Session): Panel {
  if (kind === "map") return new MapPanel(session);
  if (kind === "timeline") return new TimelinePanel(session);
  return new StepsPanel(session);
}

/** Call `fn` with the element's size whenever it changes (also when its page is shown). */
function observeSize(el: Element, fn: (w: number, h: number) => void): ResizeObserver {
  const ro = new ResizeObserver(([entry]) => fn(entry.contentRect.width, entry.contentRect.height));
  ro.observe(el);
  return ro;
}

function html(markup: string): HTMLElement {
  const t = document.createElement("template");
  t.innerHTML = markup.trim();
  return t.content.firstElementChild as HTMLElement;
}

// ---------------------------------------------------------------- concept map

class MapPanel implements Panel {
  readonly kind = "map";
  readonly el = html(`
    <div class="panel panel-map">
      <div class="map"><svg role="img" aria-label="Mapa de conceptos"></svg></div>
      <p class="hint map-info" aria-live="polite" hidden></p>
    </div>`);
  private map: ConceptMap;
  private info = this.el.querySelector<HTMLParagraphElement>(".map-info")!;
  private ro: ResizeObserver;

  constructor(private s: Session) {
    this.map = new ConceptMap(this.el.querySelector("svg")!);
    this.map.onSelect = (id) => s.select({ kind: "node", id }, true);
    this.map.onHover = (id) => s.hover(id);
    const box = this.el.querySelector(".map")!;
    this.ro = observeSize(box, (w, h) => this.map.resize(w, h));
    // Everything mined so far, so the window is full as soon as it opens.
    this.map.update([...s.state.nodes.values()], [], [...s.state.edges.values()], []);
  }

  sync(view: ViewUpdate): void {
    if (view.kind === "snapshot") this.map.reset();
    this.map.update(view.nodes, view.removed.nodes, view.edges, view.removed.edges);
  }

  refresh(): void {}

  reset(): void {
    this.map.reset();
  }

  setActive(a: Active): void {
    this.map.setActive(a.node, a.neighbours, a.selectedNode, a.hovered ? null : a.topic);
    this.renderInfo(a.node, a.topic);
  }

  destroy(): void {
    this.ro.disconnect();
    this.map.destroy();
  }

  private renderInfo(nodeId: string | null, topicId: string | null): void {
    const { state } = this.s;
    const node = nodeId ? state.nodes.get(nodeId) : undefined;
    const topic = topicId ? state.topics.get(topicId) : undefined;
    if (node) {
      const spans = state.nodeSpans(node.id);
      const text = this.s.text();
      const forms = [...new Set(spans.map(([a, b]) => text.slice(a, b)))];
      const tramos = tramosOf(state, spans);
      const co = [...state.neighbours(node.id)].map((n) => state.nodes.get(n)?.label ?? n);
      const topicName = node.topic_id ? state.topics.get(node.topic_id)?.name : null;
      this.info.innerHTML =
        `<span class="sw" style="--c: var(--c${node.colour_slot % 6})">${esc(node.label)}</span> · ` +
        `<b>${node.count}</b> ${node.count === 1 ? "mención" : "menciones"}` +
        (tramos.length ? ` en ${tramos.length === 1 ? "el tramo" : "los tramos"} ${tramos.join(", ")}` : "") +
        (topicName ? ` · tema «${esc(topicName)}»` : "") +
        (forms.length ? ` · formas: ${forms.map((f) => `«${esc(f)}»`).join(", ")}` : "") +
        (co.length ? ` · coaparece con ${co.map(esc).join(", ")}` : "");
      this.info.hidden = false;
      return;
    }
    if (topic) {
      const concepts = [...state.nodes.values()].filter((n) => n.topic_id === topic.id).map((n) => n.label);
      const tramos = state.orderedParagraphs().flatMap((p, i) => (p.topic_id === topic.id ? [i + 1] : []));
      this.info.innerHTML =
        `Tema <span class="sw" style="--c: var(--c${topic.colour_slot % 6})">${esc(topic.name)}</span>` +
        (concepts.length ? ` · conceptos: ${concepts.map(esc).join(", ")}` : "") +
        (tramos.length ? ` · domina ${tramos.length === 1 ? "el tramo" : "los tramos"} ${tramos.join(", ")}` : "");
      this.info.hidden = false;
      return;
    }
    // Nothing selected: no line at all (how to read the map is the window title's tooltip).
    this.info.hidden = true;
    this.info.textContent = "";
  }
}

function tramosOf(state: ViewState, spans: [number, number][]): number[] {
  const paragraphs = state.orderedParagraphs();
  return [...new Set(spans.map(([a]) => paragraphs.findIndex((p) => p.start <= a && a < p.end) + 1))].filter((n) => n > 0);
}

// ---------------------------------------------------------------- topic timeline

class TimelinePanel implements Panel {
  readonly kind = "timeline";
  readonly el = html(`
    <div class="panel panel-timeline">
      <div class="chart-wrap"><svg class="chart" role="img" aria-label="Temas a lo largo de la traza"></svg><div class="tip" hidden></div></div>
      <div class="legend" aria-label="Temas"></div>
    </div>`);
  private chart: TimelineChart;
  private ro: ResizeObserver;

  constructor(private s: Session) {
    this.chart = new TimelineChart(this.el.querySelector("svg")!, this.el.querySelector(".tip")!, this.el.querySelector(".legend")!);
    this.chart.onSelectTopic = (id) => s.select(id ? { kind: "topic", id } : null, true);
    this.ro = observeSize(this.el.querySelector(".chart-wrap")!, (w, h) => this.chart.resize(w, h));
    this.refresh();
  }

  sync(): void {
    this.refresh();
  }

  refresh(): void {
    this.chart.update(this.s.state.timeline, this.s.state.orderedTopics(), this.s.segmenting());
  }

  reset(): void {
    this.chart.reset();
  }

  setActive(a: Active): void {
    this.chart.select(a.chart);
  }

  destroy(): void {
    this.ro.disconnect();
  }
}

// ---------------------------------------------------------------- step graph

class StepsPanel implements Panel {
  readonly kind = "steps";
  readonly el = html(`
    <div class="panel panel-steps">
      <div class="steps-wrap" data-keep-scroll><svg role="img" aria-label="Grafo de pasos"></svg></div>
      <div class="step-detail" hidden></div>
    </div>`);
  private steps: StepGraph;
  private detail = this.el.querySelector<HTMLElement>(".step-detail")!;
  private ro: ResizeObserver;

  constructor(private s: Session) {
    const wrap = this.el.querySelector<HTMLElement>(".steps-wrap")!;
    this.steps = new StepGraph(wrap.querySelector("svg")!, wrap);
    this.steps.onSelect = (id) => s.select({ kind: "step", id }, true);
    this.ro = observeSize(wrap, () => this.steps.resize());
    this.refresh();
  }

  sync(view: ViewUpdate): void {
    const { state } = this.s;
    this.steps.update(state.orderedSteps(), state.paragraphs, state.topics, this.s.live() && !view.final);
  }

  refresh(): void {
    const { state } = this.s;
    this.steps.update(state.orderedSteps(), state.paragraphs, state.topics, this.s.live());
  }

  reset(): void {
    this.steps.reset();
    this.renderDetail(null);
  }

  setActive(a: Active): void {
    this.steps.setActive(a.step, a.topic);
    this.renderDetail(a.step);
  }

  destroy(): void {
    this.ro.disconnect();
  }

  private renderDetail(segmentId: number | null): void {
    const { state } = this.s;
    const ordered = state.orderedSteps();
    const i = ordered.findIndex((s) => s.segment_id === segmentId);
    // The card shows only for a selected step.
    this.detail.hidden = i < 0;
    if (i < 0) {
      this.detail.replaceChildren();
      return;
    }
    const step = ordered[i];
    const p = state.paragraphs.get(step.segment_id);
    const topic = step.topic_id ? state.topics.get(step.topic_id) : undefined;
    const slot = state.slotOf(step.topic_id);
    const keywords = p?.label ? p.label.split(" · ") : [];
    const back = step.arcs_back_to.map((seg) => ordered.findIndex((s) => s.segment_id === seg) + 1).filter((n) => n > 0);
    const text = this.s.text();
    const excerpt = p ? text.slice(p.start, Math.min(p.end, p.start + 240)) + (p.end - p.start > 240 ? "…" : "") : "";
    this.detail.style.setProperty("--c", `var(--c${slot % 6})`);
    this.detail.innerHTML =
      `<div class="sd-head"><div class="sd-num">${i + 1}</div><div><h3>${esc(cap(stepTypeEs(step.step_type)))}</h3>` +
      `<p>tramo ${i + 1} · ${step.words} palabras${p?.provisional ? " · provisional" : ""}</p></div>` +
      (topic ? `<span class="sd-tag">${esc(topic.name)}</span>` : "") +
      `</div><div class="sd-grid"><div>` +
      `<h4>Marcador</h4><p class="sd-text">${step.marker ? `<span class="mkq">«${esc(step.marker)}»</span>` : "Ninguno: el corte viene del cambio de vocabulario."}</p>` +
      (back.length ? `<h4>Retoma</h4><p class="sd-text">Vuelve al tema del paso ${back.join(", ")}.</p>` : "") +
      `<h4>Palabras clave (TF-IDF del tramo)</h4><p class="sd-text">${keywords.map(esc).join(" · ") || "—"}</p>` +
      `</div><div><h4>Texto</h4><p class="sd-text">${esc(excerpt)}</p></div></div>`;
  }
}
