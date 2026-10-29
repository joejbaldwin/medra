// Concept map: one bubble per Node from the presenter. The presenter decides
// which bubbles exist and how big they are; this file only runs the physics
// (d3-force) and draws them.
import * as d3 from "d3";
import type { Node } from "./contracts";

const W = 800;
const H = 480;

interface Bubble extends d3.SimulationNodeDatum {
  id: string;
  node: Node;
}

export class ConceptMap {
  private svg: d3.Selection<SVGSVGElement, unknown, null, undefined>;
  private layer: d3.Selection<SVGGElement, unknown, null, undefined>;
  private bubbles = new Map<string, Bubble>();
  private sim: d3.Simulation<Bubble, undefined>;

  constructor(svgEl: SVGSVGElement) {
    this.svg = d3.select(svgEl).attr("viewBox", `0 0 ${W} ${H}`);
    this.layer = this.svg.append("g");
    this.sim = d3
      .forceSimulation<Bubble>([])
      .force("charge", d3.forceManyBody<Bubble>().strength(-20))
      .force("collide", d3.forceCollide<Bubble>((d) => d.node.radius + 4).strength(0.9))
      .force("x", d3.forceX<Bubble>(W / 2).strength(0.04))
      .force("y", d3.forceY<Bubble>(H / 2).strength(0.07))
      .on("tick", () => this.tick());
  }

  reset(): void {
    this.bubbles.clear();
    this.render();
  }

  /** Apply one ViewUpdate's node changes (upserts + removals). */
  update(upserts: Node[], removed: string[]): void {
    for (const id of removed) this.bubbles.delete(id);
    const grown: string[] = [];
    for (const node of upserts) {
      const existing = this.bubbles.get(node.id);
      if (existing) {
        if (node.count > existing.node.count) grown.push(node.id);
        existing.node = node;
      } else {
        // Start near the presenter's seed position, or near the centre.
        const [sx, sy] = node.seed_xy ?? [0.5, 0.5];
        this.bubbles.set(node.id, {
          id: node.id,
          node,
          x: sx * W + (Math.random() - 0.5) * 60,
          y: sy * H + (Math.random() - 0.5) * 60,
        });
      }
    }
    this.render();
    for (const id of grown) this.pulse(id);
  }

  private render(): void {
    const data = [...this.bubbles.values()];
    const groups = this.layer
      .selectAll<SVGGElement, Bubble>("g.node")
      .data(data, (d) => d.id)
      .join(
        (enter) => {
          const g = enter.append("g").attr("class", "node");
          g.append("circle").attr("class", "pulse");
          g.append("circle").attr("class", "body").attr("r", 0);
          g.append("text").attr("class", "lbl");
          g.append("title");
          return g;
        },
        (update) => update,
        (exit) => exit.transition().duration(250).style("opacity", 0).remove(),
      );
    groups.style("--c", (d) => `var(--c${d.node.colour_slot % 6})`);
    groups.select<SVGCircleElement>("circle.body").transition().duration(350).attr("r", (d) => d.node.radius);
    groups.select<SVGCircleElement>("circle.pulse").attr("r", (d) => d.node.radius);
    groups
      .select<SVGTextElement>("text.lbl")
      .style("font-size", (d) => `${fontSize(d.node.label, d.node.radius)}px`)
      .text((d) => fitLabel(d.node.label, d.node.radius));
    groups.select("title").text((d) => `${d.node.label}: ${d.node.count} menciones`);

    this.sim.nodes(data);
    this.sim.alpha(Math.max(this.sim.alpha(), 0.4)).restart();
  }

  private tick(): void {
    for (const b of this.bubbles.values()) {
      const r = b.node.radius;
      b.x = Math.max(r, Math.min(W - r, b.x ?? W / 2));
      b.y = Math.max(r, Math.min(H - r, b.y ?? H / 2));
    }
    this.layer.selectAll<SVGGElement, Bubble>("g.node").attr("transform", (d) => `translate(${d.x},${d.y})`);
  }

  private pulse(id: string): void {
    const ring = this.layer
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

// Average glyph width as a fraction of the font size (Figtree, semibold).
const GLYPH = 0.56;
const MIN_FONT = 10;

/** Largest font (up to a size set by the radius) at which the label fits inside the bubble. */
function fontSize(label: string, r: number): number {
  const byRadius = Math.min(20, r * 0.42);
  const toFit = (2 * r - 10) / (GLYPH * Math.max(1, label.length));
  return Math.max(MIN_FONT, Math.min(byRadius, toFit));
}

/** Truncate only when the label doesn't fit even at the minimum font size. */
function fitLabel(label: string, r: number): string {
  const maxChars = Math.floor((2 * r - 10) / (MIN_FONT * GLYPH));
  return label.length <= maxChars ? label : `${label.slice(0, Math.max(1, maxChars - 1))}…`;
}
