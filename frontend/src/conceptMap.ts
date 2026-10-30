// Concept map: one bubble per Node and one line per Edge from the presenter.
// The presenter decides which bubbles and edges exist and their sizes; this
// file only runs the physics (d3-force), draws, and reports clicks/hovers.
import * as d3 from "d3";
import type { Edge, Node } from "./contracts";

const W = 800;
const H = 480;
const PALETTE = 6;

interface Bubble extends d3.SimulationNodeDatum {
  id: string;
  node: Node;
}

interface Link extends d3.SimulationLinkDatum<Bubble> {
  id: string;
  edge: Edge;
}

export class ConceptMap {
  onSelect: (id: string) => void = () => {};
  onHover: (id: string | null) => void = () => {};

  private edgeLayer: d3.Selection<SVGGElement, unknown, null, undefined>;
  private nodeLayer: d3.Selection<SVGGElement, unknown, null, undefined>;
  private bubbles = new Map<string, Bubble>();
  private links = new Map<string, Link>();
  private sim: d3.Simulation<Bubble, Link>;

  constructor(svgEl: SVGSVGElement) {
    const svg = d3.select(svgEl).attr("viewBox", `0 0 ${W} ${H}`);
    this.edgeLayer = svg.append("g");
    this.nodeLayer = svg.append("g");
    this.sim = d3
      .forceSimulation<Bubble, Link>([])
      .force("charge", d3.forceManyBody<Bubble>().strength(-20))
      .force("collide", d3.forceCollide<Bubble>((d) => d.node.radius + 4).strength(0.9))
      .force("link", d3.forceLink<Bubble, Link>([]).id((d) => d.id).distance((l) => linkDistance(l)).strength(0.15))
      // Each bubble is pulled towards its topic's sector (the presenter's seed
      // position), so topics form groups. Targets are re-read whenever
      // sim.nodes() is called, i.e. on every update.
      .force("x", d3.forceX<Bubble>((d) => (d.node.seed_xy?.[0] ?? 0.5) * W).strength(0.06))
      .force("y", d3.forceY<Bubble>((d) => (d.node.seed_xy?.[1] ?? 0.5) * H).strength(0.09))
      .on("tick", () => this.tick());
  }

  reset(): void {
    this.bubbles.clear();
    this.links.clear();
    this.render();
  }

  /** Apply one ViewUpdate's node and edge changes. */
  update(nodes: Node[], removedNodes: string[], edges: Edge[], removedEdges: string[]): void {
    for (const id of removedNodes) this.bubbles.delete(id);
    const grown: string[] = [];
    for (const node of nodes) {
      const existing = this.bubbles.get(node.id);
      if (existing) {
        if (node.count > existing.node.count) grown.push(node.id);
        existing.node = node;
      } else {
        // Start near the presenter's seed position, or near the centre.
        const [sx, sy] = node.seed_xy ?? [0.5, 0.5];
        this.bubbles.set(node.id, { id: node.id, node, x: sx * W + (Math.random() - 0.5) * 80, y: sy * H + (Math.random() - 0.5) * 80 });
      }
    }
    for (const id of removedEdges) this.links.delete(id);
    for (const edge of edges) this.links.set(edge.id, { id: edge.id, edge, source: edge.a, target: edge.b });
    // An edge can only exist between bubbles on screen.
    for (const [id, l] of this.links) {
      if (!this.bubbles.has(l.edge.a) || !this.bubbles.has(l.edge.b)) this.links.delete(id);
    }
    this.render();
    for (const id of grown) this.pulse(id);
  }

  /** Highlight one bubble and its neighbours, or the bubbles of one topic; dim the rest. */
  setActive(id: string | null, neighbours: Set<string>, selected: string | null, topic: string | null = null): void {
    const lit = (d: Bubble) => (id ? d.id === id || neighbours.has(d.id) : !topic || d.node.topic_id === topic);
    this.nodeLayer
      .selectAll<SVGGElement, Bubble>("g.node")
      .classed("sel", (d) => d.id === selected)
      .classed("hover", (d) => d.id === id && id !== selected)
      .classed("dim", (d) => !lit(d));
    const topicOf = (bid: string) => this.bubbles.get(bid)?.node.topic_id;
    this.edgeLayer
      .selectAll<SVGLineElement, Link>("line.edge")
      .classed("on", (l) => (id ? l.edge.a === id || l.edge.b === id : !!topic && topicOf(l.edge.a) === topic && topicOf(l.edge.b) === topic))
      .classed("dim", (l) => (id ? l.edge.a !== id && l.edge.b !== id : !!topic && (topicOf(l.edge.a) !== topic || topicOf(l.edge.b) !== topic)));
  }

  private render(): void {
    const data = [...this.bubbles.values()];
    const links = [...this.links.values()];

    this.edgeLayer
      .selectAll<SVGLineElement, Link>("line.edge")
      .data(links, (l) => l.id)
      .join("line")
      .attr("class", "edge")
      .style("--c", (l) => `var(--c${l.edge.colour_slot % PALETTE})`)
      .attr("stroke-width", (l) => l.edge.width);

    const groups = this.nodeLayer
      .selectAll<SVGGElement, Bubble>("g.node")
      .data(data, (d) => d.id)
      .join(
        (enter) => {
          const g = enter
            .append("g")
            .attr("class", "node")
            .attr("data-id", (d) => d.id)
            .attr("tabindex", 0)
            .attr("role", "button");
          g.append("circle").attr("class", "pulse");
          g.append("circle").attr("class", "body").attr("r", 0);
          g.append("text").attr("class", "lbl");
          g.on("click", (_, d) => this.onSelect(d.id))
            .on("mouseenter", (_, d) => this.onHover(d.id))
            .on("mouseleave", () => this.onHover(null))
            .on("keydown", (e: KeyboardEvent, d) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                this.onSelect(d.id);
              }
            });
          return g;
        },
        (update) => update,
        (exit) => exit.transition().duration(250).style("opacity", 0).remove(),
      );
    groups.style("--c", (d) => `var(--c${d.node.colour_slot % PALETTE})`);
    groups.attr("aria-label", (d) => `${d.node.label}: ${d.node.count} menciones`);
    groups.select<SVGCircleElement>("circle.body").transition().duration(350).attr("r", (d) => d.node.radius);
    groups.select<SVGCircleElement>("circle.pulse").attr("r", (d) => d.node.radius);
    groups.select<SVGTextElement>("text.lbl").each(function (d) {
      setLabel(this, d.node.label, d.node.radius);
    });

    this.sim.nodes(data);
    // forceLink replaces ids with bubble objects; reset them so a bubble that was
    // removed and re-added is linked to its new object, not a stale one.
    for (const l of links) {
      l.source = l.edge.a;
      l.target = l.edge.b;
    }
    this.sim.force<d3.ForceLink<Bubble, Link>>("link")!.links(links);
    this.sim.alpha(Math.max(this.sim.alpha(), 0.4)).restart();
  }

  private tick(): void {
    for (const b of this.bubbles.values()) {
      const r = b.node.radius;
      b.x = Math.max(r, Math.min(W - r, b.x ?? W / 2));
      b.y = Math.max(r, Math.min(H - r, b.y ?? H / 2));
    }
    this.nodeLayer.selectAll<SVGGElement, Bubble>("g.node").attr("transform", (d) => `translate(${d.x},${d.y})`);
    this.edgeLayer
      .selectAll<SVGLineElement, Link>("line.edge")
      .attr("x1", (l) => (l.source as Bubble).x ?? 0)
      .attr("y1", (l) => (l.source as Bubble).y ?? 0)
      .attr("x2", (l) => (l.target as Bubble).x ?? 0)
      .attr("y2", (l) => (l.target as Bubble).y ?? 0);
  }

  private pulse(id: string): void {
    const ring = this.nodeLayer
      .selectAll<SVGGElement, Bubble>("g.node")
      .filter((d) => d.id === id)
      .select<SVGCircleElement>("circle.pulse")
      .node();
    if (!ring) return;
    ring.classList.remove("go");
    void ring.getBBox(); // restart the CSS animation
    ring.classList.add("go");
  }
}

function linkDistance(l: Link): number {
  const a = l.source as Bubble;
  const b = l.target as Bubble;
  return (a.node?.radius ?? 30) + (b.node?.radius ?? 30) + 30;
}

// ---------------------------------------------------------------- labels

// Average glyph width as a fraction of the font size (Figtree, semibold).
const GLYPH = 0.56;
const MIN_FONT = 10;
const MAX_FONT = 20;

/** Fit a label inside its bubble: shrink the font, then wrap at a space, then truncate. */
export function layoutLabel(label: string, r: number): { lines: string[]; size: number } {
  const width = 2 * r - 12;
  const byRadius = Math.min(MAX_FONT, r * 0.42);
  const fit = (s: string) => width / (GLYPH * Math.max(1, s.length));
  const oneLine = Math.min(byRadius, fit(label));
  if (oneLine >= MIN_FONT + 2 || !label.includes(" ")) {
    const size = Math.max(MIN_FONT, oneLine);
    const maxChars = Math.floor(width / (MIN_FONT * GLYPH));
    return { lines: [label.length <= maxChars ? label : `${label.slice(0, Math.max(1, maxChars - 1))}…`], size };
  }
  // Two lines, split at the space nearest the middle.
  const spaces = [...label].flatMap((c, i) => (c === " " ? [i] : []));
  const cut = spaces.reduce((best, i) => (Math.abs(i - label.length / 2) < Math.abs(best - label.length / 2) ? i : best));
  const lines = [label.slice(0, cut), label.slice(cut + 1)];
  const size = Math.max(MIN_FONT, Math.min(byRadius, ...lines.map(fit)));
  return { lines, size };
}

function setLabel(text: SVGTextElement, label: string, r: number): void {
  const { lines, size } = layoutLabel(label, r);
  const sel = d3.select(text).style("font-size", `${size}px`);
  sel
    .selectAll("tspan")
    .data(lines)
    .join("tspan")
    .attr("x", 0)
    .attr("dy", (_, i) => (i === 0 ? `${-(lines.length - 1) * 0.55}em` : "1.1em"))
    .text((s) => s);
}
