// "Pasos del agente": one node per segment, in order, coloured by its topic.
// The marker that opened the step is written on the arrow leading to it; a
// dashed arc above the track means the step returns to the topic of an
// earlier step (retoma). Long traces scroll horizontally.
import * as d3 from "d3";
import type { Paragraph, Step, Topic } from "./contracts";

// The drawing fills its window's height (at least MIN_H) and scrolls sideways
// when the steps need more width. Arcs need ~130 px above the track and the
// labels ~100 px below it.
const MIN_H = 260;
const PAD = 56;
const MIN_SPACING = 150;
const R = 26;
const PALETTE = 6;
const MARKER_CHARS = 24;
const MONO_CHAR = 7; // width of one character of .s-mk (11.5px JetBrains Mono)

export const STEP_ES: Record<string, string> = {
  planning: "planificación",
  verification: "verificación",
  backtrack: "corrección",
  alternative: "alternativa",
  conclusion: "conclusión",
};

export function stepTypeEs(type: string | null | undefined): string {
  return (type && STEP_ES[type]) || "desarrollo";
}

// Each graph needs its own arrowhead ids: url(#id) resolves to the first match
// in the document, which may be inside a hidden page, where it does not render.
let instances = 0;

interface StepView {
  step: Step;
  index: number;
  x: number;
  slot: number;
  label: string;
  provisional: boolean;
}

export class StepGraph {
  onSelect: (segmentId: number) => void = () => {};

  private svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
  private selected: number | null = null;
  private dimTopic: string | null = null;
  private last: Parameters<StepGraph["update"]> | null = null;
  private arrowId = `step-arrow-${instances++}`;

  constructor(
    svgEl: SVGSVGElement,
    private wrap: HTMLElement,
  ) {
    this.svg = d3.select(svgEl);
    const defs = this.svg.append("defs");
    for (let slot = 0; slot < PALETTE; slot++) {
      defs
        .append("marker")
        .attr("id", `${this.arrowId}-${slot}`)
        .attr("viewBox", "0 0 10 10")
        .attr("refX", 8)
        .attr("refY", 5)
        .attr("markerUnits", "userSpaceOnUse")
        .attr("markerWidth", 12)
        .attr("markerHeight", 12)
        .attr("orient", "auto-start-reverse")
        .append("path")
        .attr("d", "M0,0 L10,5 L0,10 z")
        .style("fill", `var(--c${slot})`);
    }
    this.svg.append("g").attr("class", "s-body");
  }

  /** Redraw at the window's current size (after it was resized or shown). */
  resize(): void {
    if (this.last && this.wrap.clientWidth > 0) this.update(...this.last);
  }

  reset(): void {
    this.selected = null;
    this.dimTopic = null;
    this.last = null;
    this.svg.select("g.s-body").selectAll("*").remove();
  }

  update(steps: Step[], paragraphs: Map<number, Paragraph>, topics: Map<string, Topic>, live: boolean): void {
    this.last = [steps, paragraphs, topics, live];
    const width = Math.max(this.wrap.clientWidth || 800, 2 * PAD + steps.length * MIN_SPACING);
    const H = Math.max(MIN_H, this.wrap.clientHeight);
    const SY = Math.max(140, Math.round(H / 2 + 12)); // the track
    const spacing = steps.length ? (width - 2 * PAD) / steps.length : MIN_SPACING;
    this.svg.attr("viewBox", `0 0 ${width} ${H}`).attr("width", width).attr("height", H);
    const views: StepView[] = steps.map((step, i) => {
      const p = paragraphs.get(step.segment_id);
      return {
        step,
        index: i,
        x: PAD + spacing * (i + 0.5),
        slot: step.topic_id ? (topics.get(step.topic_id)?.colour_slot ?? 5) : 5,
        label: p?.label.split(" · ").slice(0, 2).join(" · ") ?? "",
        provisional: live && i === steps.length - 1,
      };
    });
    const byId = new Map(views.map((v) => [v.step.segment_id, v]));

    const body = this.svg.select<SVGGElement>("g.s-body");
    body.selectAll("*").remove();
    if (!views.length) return;
    body.append("line").attr("class", "s-track").attr("x1", PAD).attr("x2", views[views.length - 1].x).attr("y1", SY).attr("y2", SY);
    body.append("circle").attr("class", "s-start").attr("cx", PAD - 30).attr("cy", SY).attr("r", 6);

    // Arcs first, so the nodes are drawn on top.
    views.forEach((v, k) => {
      for (const back of v.step.arcs_back_to) {
        const from = byId.get(back);
        if (!from) continue;
        const lift = 56 + 14 * (k % 3) + Math.min(40, (v.index - from.index) * 6);
        const top = SY - R - lift;
        const g = body.append("g").attr("class", "s-arc").style("--c", `var(--c${v.slot % PALETTE})`);
        g.append("path")
          .attr("d", `M${v.x},${SY - R - 4} C${v.x},${top} ${from.x},${top} ${from.x},${SY - R - 8}`)
          .attr("marker-end", `url(#${this.arrowId}-${v.slot % PALETTE})`);
        const name = v.step.topic_id ? (topics.get(v.step.topic_id)?.name ?? "") : "";
        const label = `retoma «${name}»`;
        // Highest point of the curve: a cubic Bézier with both control points at
        // `top` peaks at 0.25 * start + 0.75 * top.
        const apex = 0.25 * (SY - R - 6) + 0.75 * top;
        const text = g.append("text").attr("x", (v.x + from.x) / 2).attr("y", apex + 4.5).text(label);
        const w = (text.node()?.getComputedTextLength() || label.length * 7.2) + 18;
        g.insert("rect", "text")
          .attr("x", (v.x + from.x) / 2 - w / 2)
          .attr("y", apex - 11)
          .attr("width", w)
          .attr("height", 22)
          .attr("rx", 6);
      }
    });

    for (const v of views) {
      const prevX = v.index === 0 ? PAD - 30 + 10 : views[v.index - 1].x + R + 6;
      const g = body
        .append("g")
        .attr("class", "s-step")
        .attr("data-topic", v.step.topic_id ?? "")
        .classed("dim", !!this.dimTopic && v.step.topic_id !== this.dimTopic)
        .style("--c", `var(--c${v.slot % PALETTE})`);
      g.append("path")
        .attr("class", "s-arrow")
        .attr("d", `M${prevX},${SY} L${v.x - R - 6},${SY}`)
        .attr("marker-end", `url(#${this.arrowId}-${v.slot % PALETTE})`);
      if (v.step.marker) {
        // Above the node tops, centred on the arrow, so it can use the whole gap
        // between two nodes (monospace: ~MONO_CHAR px per character, plus the «»).
        const room = Math.min(MARKER_CHARS, Math.floor((spacing - 14) / MONO_CHAR) - 2);
        const m = shorten(v.step.marker, Math.max(3, room));
        g.append("text")
          .attr("class", "s-mk")
          .attr("x", (prevX + v.x - R) / 2)
          .attr("y", SY - R - 10)
          .text(`«${m}»`)
          .append("title")
          .text(v.step.marker);
      }
      const node = g
        .append("g")
        .attr("class", "s-node")
        .classed("sel", this.selected === v.step.segment_id)
        .classed("live", v.provisional)
        .attr("data-seg", v.step.segment_id)
        .attr("transform", `translate(${v.x},${SY})`)
        .attr("tabindex", 0)
        .attr("role", "button")
        .attr("aria-label", `Paso ${v.index + 1}: ${stepTypeEs(v.step.step_type)}`);
      node.append("circle").attr("class", "halo").attr("r", R + 5);
      node.append("circle").attr("class", "core").attr("r", R);
      node.append("text").attr("class", "num").attr("dy", "0.35em").text(v.index + 1);
      node.on("click", () => this.onSelect(v.step.segment_id)).on("keydown", (e: KeyboardEvent) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          this.onSelect(v.step.segment_id);
        }
      });
      g.append("text").attr("class", "s-name").attr("x", v.x).attr("y", SY + R + 28).text(stepTypeEs(v.step.step_type));
      g.append("text").attr("class", "s-meta").attr("x", v.x).attr("y", SY + R + 47).text(`${v.step.words} pal.`);
      if (v.label) g.append("text").attr("class", "s-kw").attr("x", v.x).attr("y", SY + R + 66).text(shorten(v.label, Math.floor(spacing / 7.5)));
    }
  }

  /** Mark a selected step and dim the steps of other topics (when a topic is selected). */
  setActive(segmentId: number | null, topicId: string | null): void {
    this.selected = segmentId;
    this.dimTopic = topicId;
    const body = this.svg.select("g.s-body");
    body.selectAll<SVGGElement, unknown>("g.s-node").classed("sel", function () {
      return segmentId !== null && this.dataset.seg === String(segmentId);
    });
    body.selectAll<SVGGElement, unknown>("g.s-step").classed("dim", function () {
      return !!topicId && this.dataset.topic !== topicId;
    });
  }

  scrollTo(segmentId: number): void {
    const node = this.svg.select<SVGGElement>(`g.s-node[data-seg="${segmentId}"]`).node();
    node?.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
  }
}

function shorten(s: string, max: number): string {
  return s.length > max ? `${s.slice(0, Math.max(1, max - 1))}…` : s;
}
