// "Temas a lo largo de la traza": one density curve per topic over the word
// position (computed by the presenter), with the segment boundaries as dashed
// lines. Hover shows the values at that point; clicking a curve or a legend
// entry selects the topic. A selected step is shown as a band, a selected
// concept as ticks at its mentions.
import * as d3 from "d3";
import type { Timeline, Topic } from "./contracts";

const W = 1000;
const H = 240;
const X0 = 58;
const X1 = 972;
const Y0 = 14;
const Y1 = 190;
const PALETTE = 6;

export interface Segmenting {
  starts: number[]; // first word of each segment, in order
  current: number; // words received so far
}

export type TimelineSelection =
  | { kind: "topic"; id: string }
  | { kind: "step"; start: number; end: number; slot: number }
  | { kind: "node"; words: number[]; slot: number }
  | null;

export class TimelineChart {
  onSelectTopic: (id: string | null) => void = () => {};

  private svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
  private grid: d3.Selection<SVGGElement, unknown, null, undefined>;
  private band: d3.Selection<SVGRectElement, unknown, null, undefined>;
  private areas: d3.Selection<SVGGElement, unknown, null, undefined>;
  private rug: d3.Selection<SVGGElement, unknown, null, undefined>;
  private hoverLine: d3.Selection<SVGLineElement, unknown, null, undefined>;
  private peak: d3.Selection<SVGGElement, unknown, null, undefined>;
  private timeline: Timeline | null = null;
  private topics: Topic[] = [];
  private segs: Segmenting = { starts: [], current: 0 };
  private selection: TimelineSelection = null;
  private x = d3.scaleLinear().range([X0, X1]);
  private y = d3.scaleLinear().range([Y1, Y0]);

  constructor(
    svgEl: SVGSVGElement,
    private tip: HTMLElement,
    private legend: HTMLElement,
  ) {
    this.svg = d3.select(svgEl).attr("viewBox", `0 0 ${W} ${H}`);
    this.grid = this.svg.append("g");
    this.band = this.svg.append("rect").attr("class", "c-band").attr("y", Y0).attr("height", Y1 - Y0).attr("width", 0);
    this.areas = this.svg.append("g");
    this.rug = this.svg.append("g").attr("class", "c-rug");
    this.hoverLine = this.svg.append("line").attr("class", "c-hover").attr("y1", Y0).attr("y2", Y1).attr("visibility", "hidden");
    this.peak = this.svg.append("g").attr("class", "c-peak").attr("visibility", "hidden");
    this.peak.append("line");
    this.peak.append("circle").attr("r", 6);
    this.peak.append("rect").attr("rx", 7).attr("height", 26);
    this.peak.append("text").attr("text-anchor", "middle");
    this.svg.on("pointermove", (e: PointerEvent) => this.hover(e));
    this.svg.on("pointerleave", () => {
      this.tip.hidden = true;
      this.hoverLine.attr("visibility", "hidden");
    });
    this.svg.on("click", (e: MouseEvent) => this.click(e));
    this.render();
  }

  reset(): void {
    this.timeline = null;
    this.topics = [];
    this.segs = { starts: [], current: 0 };
    this.selection = null;
    this.render();
  }

  update(timeline: Timeline | null, topics: Topic[], segs: Segmenting): void {
    this.timeline = timeline;
    this.topics = topics;
    this.segs = segs;
    this.render();
  }

  select(selection: TimelineSelection): void {
    this.selection = selection;
    this.renderSelection();
  }

  private series(): { topic: Topic; points: [number, number][] }[] {
    const byId = new Map(this.topics.map((t) => [t.id, t]));
    return (this.timeline?.series ?? []).flatMap((s) => {
      const topic = byId.get(s.topic_id);
      return topic ? [{ topic, points: s.points }] : [];
    });
  }

  private render(): void {
    const series = this.series();
    const xMax = Math.max(1, this.timeline?.x_max ?? 1);
    const yMax = Math.max(1, Math.ceil(d3.max(series, (s) => d3.max(s.points, (p) => p[1])) ?? 0) + 0.15);
    this.x.domain([0, xMax]);
    this.y.domain([0, Math.ceil(yMax)]);

    // Grid, y labels, and a dashed line at each segment boundary.
    const ticks = d3.range(0, Math.ceil(yMax) + 1, Math.ceil(yMax) > 6 ? 2 : 1);
    this.grid.selectAll("*").remove();
    for (const v of ticks) {
      this.grid.append("line").attr("class", "c-grid").attr("x1", X0).attr("x2", X1).attr("y1", this.y(v)).attr("y2", this.y(v));
      this.grid.append("text").attr("class", "c-axis").attr("x", X0 - 12).attr("y", this.y(v)).attr("dy", "0.35em").attr("text-anchor", "end").text(v);
    }
    this.grid
      .append("text")
      .attr("class", "c-ytitle")
      .attr("transform", `translate(16 ${(Y0 + Y1) / 2}) rotate(-90)`)
      .attr("text-anchor", "middle")
      .text("Menciones");
    const starts = this.segs.starts;
    starts.forEach((w, i) => {
      if (i > 0) this.grid.append("line").attr("class", "c-tramo").attr("x1", this.x(w)).attr("x2", this.x(w)).attr("y1", Y0).attr("y2", Y1);
    });
    // x labels: the first segments by number, thinned out when there are many.
    const every = Math.max(1, Math.ceil(starts.length / 8));
    starts.forEach((w, i) => {
      if (i % every) return;
      this.grid.append("text").attr("class", "c-axis").attr("x", this.x(w) + 4).attr("y", Y1 + 22).text(i === 0 ? "Inicio" : `T${i + 1}`);
    });
    this.grid.append("text").attr("class", "c-axis").attr("x", X1).attr("y", Y1 + 44).attr("text-anchor", "end").text(`${Math.round(xMax)} palabras`);

    const area = d3.area<[number, number]>().x((p) => this.x(p[0])).y0(Y1).y1((p) => this.y(p[1])).curve(d3.curveMonotoneX);
    const line = d3.line<[number, number]>().x((p) => this.x(p[0])).y((p) => this.y(p[1])).curve(d3.curveMonotoneX);
    const groups = this.areas
      .selectAll<SVGGElement, (typeof series)[number]>("g.c-topic")
      .data(series, (s) => s.topic.id)
      .join((enter) => {
        const g = enter.append("g").attr("class", "c-topic");
        g.append("path").attr("class", "c-area");
        g.append("path").attr("class", "c-line");
        return g;
      });
    groups.style("--c", (s) => `var(--c${s.topic.colour_slot % PALETTE})`);
    groups.select("path.c-area").attr("d", (s) => area(s.points));
    groups.select("path.c-line").attr("d", (s) => line(s.points));

    this.legend.replaceChildren(
      ...this.topics.map((t) => {
        const b = document.createElement("button");
        b.type = "button";
        b.style.setProperty("--c", `var(--c${t.colour_slot % PALETTE})`);
        b.dataset.topic = t.id;
        b.innerHTML = `<span class="dot"></span>${esc(t.name)}`;
        b.addEventListener("click", () => this.onSelectTopic(t.id));
        return b;
      }),
    );
    if (!this.topics.length) this.legend.innerHTML = `<span class="muted">Los temas aparecen cuando hay términos repetidos.</span>`;
    this.renderSelection();
  }

  private renderSelection(): void {
    const sel = this.selection;
    const topicId = sel?.kind === "topic" ? sel.id : null;
    this.areas
      .selectAll<SVGGElement, { topic: Topic }>("g.c-topic")
      .classed("on", (s) => s.topic.id === topicId)
      .classed("dim", (s) => !!topicId && s.topic.id !== topicId);
    for (const b of this.legend.querySelectorAll<HTMLButtonElement>("button")) {
      b.setAttribute("aria-pressed", String(b.dataset.topic === topicId));
    }

    // Band over a selected step, or over the segment where a selected topic peaks.
    this.band.attr("width", 0);
    this.peak.attr("visibility", "hidden");
    if (sel?.kind === "step") this.showBand(sel.start, sel.end, sel.slot);
    if (sel?.kind === "topic") {
      const s = this.series().find((x) => x.topic.id === sel.id);
      const best = s ? s.points.reduce((a, b) => (b[1] > a[1] ? b : a), [0, 0] as [number, number]) : null;
      if (s && best && best[1] > 0.05) {
        const seg = this.segmentAt(best[0]);
        this.showBand(this.segs.starts[seg], this.segs.starts[seg + 1] ?? this.segs.current, s.topic.colour_slot);
        this.showPeak(best, `${s.topic.name} · Tramo ${seg + 1}`, s.topic.colour_slot);
      }
    }

    this.rug.selectAll("*").remove();
    if (sel?.kind === "node") {
      this.rug.style("--c", `var(--c${sel.slot % PALETTE})`);
      for (const w of sel.words) this.rug.append("line").attr("x1", this.x(w)).attr("x2", this.x(w)).attr("y1", Y1 - 10).attr("y2", Y1);
    }
  }

  private showBand(start: number, end: number, slot: number): void {
    this.band
      .attr("x", this.x(start))
      .attr("width", Math.max(0, this.x(end) - this.x(start)))
      .style("--c", `var(--c${slot % PALETTE})`);
  }

  private showPeak([px, py]: [number, number], label: string, slot: number): void {
    const x = this.x(px);
    const y = this.y(py);
    this.peak.style("--c", `var(--c${slot % PALETTE})`).attr("visibility", "visible");
    this.peak.select("line").attr("x1", x).attr("x2", x).attr("y1", Y1).attr("y2", y);
    this.peak.select("circle").attr("cx", x).attr("cy", y);
    const text = this.peak.select<SVGTextElement>("text").text(label);
    const w = (text.node()?.getComputedTextLength() || label.length * 7.4) + 22;
    const bx = Math.min(X1 - w, Math.max(X0, x - w / 2));
    const by = Math.max(0, y - 40);
    this.peak.select("rect").attr("x", bx).attr("y", by).attr("width", w);
    text.attr("x", bx + w / 2).attr("y", by + 17.5);
  }

  private segmentAt(word: number): number {
    const i = d3.bisectRight(this.segs.starts, word) - 1;
    return Math.max(0, i);
  }

  /** The sample nearest the pointer, or null outside the plotted range. */
  private sampleAt(e: MouseEvent): { vx: number; index: number } | null {
    const rect = (this.svg.node() as SVGSVGElement).getBoundingClientRect();
    const vx = ((e.clientX - rect.left) / rect.width) * W;
    const points = this.timeline?.series[0]?.points;
    if (!points || points.length < 2 || vx < X0 || vx > X1) return null;
    const word = this.x.invert(vx);
    const index = Math.max(0, Math.min(points.length - 1, d3.bisectCenter(points.map((p) => p[0]), word)));
    return { vx, index };
  }

  private hover(e: PointerEvent): void {
    const at = this.sampleAt(e);
    const series = this.series();
    if (!at || !series.length) {
      this.tip.hidden = true;
      this.hoverLine.attr("visibility", "hidden");
      return;
    }
    const word = series[0].points[at.index][0];
    this.hoverLine.attr("x1", this.x(word)).attr("x2", this.x(word)).attr("visibility", "visible");
    const rows = series.map((s) => ({ t: s.topic, v: s.points[at.index]?.[1] ?? 0 })).sort((a, b) => b.v - a.v);
    this.tip.innerHTML =
      `<div class="t-head">Tramo ${this.segmentAt(word) + 1} · palabra ${Math.round(word)}</div>` +
      rows
        .map((r) => `<div class="t-row" style="--c:var(--c${r.t.colour_slot % PALETTE})"><span class="dot"></span><span>${esc(r.t.name)}</span><span>${r.v.toFixed(1)}</span></div>`)
        .join("");
    this.tip.hidden = false;
    this.tip.style.left = `${Math.min(86, Math.max(14, at.vx / 10))}%`;
  }

  private click(e: MouseEvent): void {
    const at = this.sampleAt(e);
    if (!at) return;
    const best = this.series()
      .map((s) => ({ id: s.topic.id, v: s.points[at.index]?.[1] ?? 0 }))
      .sort((a, b) => b.v - a.v)[0];
    this.onSelectTopic(best && best.v >= 0.2 ? best.id : null);
  }
}

function esc(s: string): string {
  return s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
}
