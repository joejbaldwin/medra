// Concept map: one bubble per Node and one line per Edge from the presenter.
// The presenter decides which bubbles and edges exist and their sizes; this
// file only runs the physics (d3-force), draws, and reports clicks/hovers.
import * as d3 from "d3";
import type { Edge, Node } from "./contracts";

const W = 800;
const H = 480;
const PALETTE = 6;
// Spacing: empty space kept around each bubble, and extra length of an edge
// beyond the two radii, so the lines between bubbles stay visible.
const PAD = 16;
const LINK_GAP = 80;
// The view zooms out to fit the bubbles, but never below this scale.
const MIN_SCALE = 0.6;
const MARGIN = 12;
// Animation timing, in ms so it is the same at any screen refresh rate.
// Growing: the radius covers 1 - e^(-dt/GROW_TAU) of the remaining distance
// each frame (an ease-out, ~95% after 3 * GROW_TAU). Leaving or merging: a
// fixed ease-in-out tween of LEAVE_MS.
const GROW_TAU = 160;
const LEAVE_MS = 650;

interface Bubble extends d3.SimulationNodeDatum {
  id: string;
  node: Node;
  // Radius on screen, eased towards node.radius (or towards 0 when leaving).
  // The physics uses it too, so a growing bubble nudges its neighbours aside
  // gradually instead of shoving them.
  r: number;
  // Set while the bubble shrinks away: when it started and from where.
  leaving: { t: number; x: number; y: number; r: number } | null;
  // Bubble a leaving bubble glides into, e.g. "odd" into "odd number".
  into: string | null;
}

interface Link extends d3.SimulationLinkDatum<Bubble> {
  id: string;
  edge: Edge;
}

export class ConceptMap {
  onSelect: (id: string) => void = () => {};
  onHover: (id: string | null) => void = () => {};

  private content: d3.Selection<SVGGElement, unknown, null, undefined>;
  private edgeLayer: d3.Selection<SVGGElement, unknown, null, undefined>;
  private nodeLayer: d3.Selection<SVGGElement, unknown, null, undefined>;
  private bubbles = new Map<string, Bubble>();
  private links = new Map<string, Link>();
  private sim: d3.Simulation<Bubble, Link>;
  // Current view transform (eased each tick towards the fit of the bubbles).
  private view = { x: 0, y: 0, k: 1 };
  // Runs while any radius or merge is still easing.
  private timer: d3.Timer | null = null;

  constructor(svgEl: SVGSVGElement) {
    const svg = d3.select(svgEl).attr("viewBox", `0 0 ${W} ${H}`);
    this.content = svg.append("g");
    this.edgeLayer = this.content.append("g");
    this.nodeLayer = this.content.append("g");
    this.sim = d3
      .forceSimulation<Bubble, Link>([])
      .velocityDecay(0.55) // more friction than the default 0.4: calmer motion
      // distanceMin caps the push between bubbles that start almost on top of
      // each other (a new bubble at its seed), which would otherwise fling them.
      .force("charge", d3.forceManyBody<Bubble>().strength(-260).distanceMin(40).distanceMax(500))
      .force("collide", d3.forceCollide<Bubble>(collideRadius).strength(0.9))
      .force("link", d3.forceLink<Bubble, Link>([]).id((d) => d.id).distance(linkDistance).strength(0.1))
      // Each bubble is pulled towards its topic's sector (the presenter's seed
      // position), so topics form groups. Targets are re-read whenever
      // sim.nodes() is called, i.e. on every update.
      // Weak, so the repulsion can spread a topic's bubbles apart.
      .force("x", d3.forceX<Bubble>((d) => (d.node.seed_xy?.[0] ?? 0.5) * W).strength(0.03))
      .force("y", d3.forceY<Bubble>((d) => (d.node.seed_xy?.[1] ?? 0.5) * H).strength(0.05))
      .on("tick", () => this.draw());
  }

  reset(): void {
    this.timer?.stop();
    this.timer = null;
    this.bubbles.clear();
    this.links.clear();
    this.view = { x: 0, y: 0, k: 1 };
    this.content.attr("transform", null);
    this.render();
  }

  /** Apply one ViewUpdate's node and edge changes. */
  update(nodes: Node[], removedNodes: string[], edges: Edge[], removedEdges: string[]): void {
    const before = [...this.bubbles.values()].filter((b) => !b.leaving);
    // Removed bubbles are not deleted yet: they shrink away in animate().
    const leavingNow: Bubble[] = [];
    for (const id of removedNodes) {
      const b = this.bubbles.get(id);
      if (!b || b.leaving) continue;
      b.leaving = { t: performance.now(), x: b.x!, y: b.y!, r: b.r };
      leavingNow.push(b);
    }
    const grown: string[] = [];
    for (const node of nodes) {
      const existing = this.bubbles.get(node.id);
      if (existing) {
        if (existing.leaving) {
          // Came back before it finished leaving: grow again from where it is.
          existing.leaving = null;
          existing.into = null;
          existing.vx = existing.vy = 0;
        } else if (node.count > existing.node.count) grown.push(node.id);
        existing.node = node;
      } else {
        // A merged term ("odd number" absorbing "odd") starts where the bubble
        // it absorbs is; anything else near the presenter's seed position.
        const from = before.find((b) => related(b.id, node.id));
        const [sx, sy] = node.seed_xy ?? [0.5, 0.5];
        // Inside the visible area, or fitView would snap it there in one frame.
        const x = from ? from.x : this.inView(sx * W + (Math.random() - 0.5) * 80, "x", node.radius);
        const y = from ? from.y : this.inView(sy * H + (Math.random() - 0.5) * 80, "y", node.radius);
        this.bubbles.set(node.id, { id: node.id, node, r: from ? from.r * 0.6 : 0, leaving: null, into: null, x, y });
      }
    }
    // A leaving bubble glides into the largest related bubble that stays.
    for (const b of leavingNow) {
      const targets = [...this.bubbles.values()].filter((o) => !o.leaving && related(o.id, b.id));
      b.into = targets.sort((p, q) => q.node.radius - p.node.radius)[0]?.id ?? null;
    }
    for (const id of removedEdges) this.links.delete(id);
    for (const edge of edges) this.links.set(edge.id, { id: edge.id, edge, source: edge.a, target: edge.b });
    // An edge can only exist between bubbles that stay on screen.
    const staying = (id: string) => this.bubbles.get(id)?.leaving === null;
    for (const [id, l] of this.links) {
      if (!staying(l.edge.a) || !staying(l.edge.b)) this.links.delete(id);
    }
    this.render();
    for (const id of grown) this.pulse(id);
    this.animate();
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

    // Edges fade in and out instead of popping.
    this.edgeLayer
      .selectAll<SVGLineElement, Link>("line.edge")
      .data(links, (l) => l.id)
      .join(
        (enter) =>
          enter
            .append("line")
            .attr("class", "edge")
            .style("opacity", 0)
            .call((e) => e.transition().duration(500).style("opacity", 1)),
        // An edge that comes back while fading out: cancel the fade.
        (update) => update.interrupt().style("opacity", 1),
        (exit) => exit.transition().duration(350).style("opacity", 0).remove(),
      )
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
          g.append("circle").attr("class", "body");
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
        // Leaving bubbles have already shrunk to nothing in animate().
        (exit) => exit.remove(),
      );
    groups.classed("leaving", (d) => !!d.leaving);
    groups.style("--c", (d) => `var(--c${d.node.colour_slot % PALETTE})`);
    groups.attr("aria-label", (d) => `${d.node.label}: ${d.node.count} menciones`);
    // Circles are drawn at the target radius and the group is scaled by
    // r / radius each frame, so circle and label grow and shrink together.
    groups.select<SVGCircleElement>("circle.body").attr("r", (d) => d.node.radius);
    groups.select<SVGCircleElement>("circle.pulse").attr("r", (d) => d.node.radius);
    groups.select<SVGTextElement>("text.lbl").each(function (d) {
      setLabel(this, d.node.label, d.node.radius);
    });

    // Leaving bubbles are out of the physics: only animate() moves them, so
    // they do not push away the bubble they are merging into.
    this.sim.nodes(data.filter((b) => !b.leaving));
    // forceLink replaces ids with bubble objects; reset them so a bubble that was
    // removed and re-added is linked to its new object, not a stale one.
    for (const l of links) {
      l.source = l.edge.a;
      l.target = l.edge.b;
    }
    this.sim.force<d3.ForceLink<Bubble, Link>>("link")!.links(links);
    this.sim.alpha(Math.max(this.sim.alpha(), 0.3)).restart();
    this.draw();
  }

  /** Ease radii and merges one frame at a time until everything has settled. */
  private animate(): void {
    if (this.timer) return;
    let last = performance.now();
    this.timer = d3.timer(() => {
      const now = performance.now();
      const k = 1 - Math.exp(-(now - last) / GROW_TAU);
      last = now;
      let moving = false;
      let gone = false;
      for (const b of this.bubbles.values()) {
        const lv = b.leaving;
        if (!lv) {
          b.r += (b.node.radius - b.r) * k;
          if (Math.abs(b.node.radius - b.r) < 0.3) b.r = b.node.radius;
          else moving = true;
          continue;
        }
        const p = Math.min(1, (now - lv.t) / LEAVE_MS);
        const e = d3.easeCubicInOut(p);
        b.r = lv.r * (1 - e);
        // Glide towards the absorbing bubble, following it if it moves.
        const into = b.into ? this.bubbles.get(b.into) : undefined;
        if (into && !into.leaving) {
          b.x = lv.x + (into.x! - lv.x) * e;
          b.y = lv.y + (into.y! - lv.y) * e;
        }
        if (p === 1) {
          this.bubbles.delete(b.id);
          gone = true;
        } else moving = true;
      }
      if (gone) {
        this.nodeLayer.selectAll<SVGGElement, Bubble>("g.node").filter((d) => this.bubbles.get(d.id) !== d).remove();
        this.sim.nodes([...this.bubbles.values()].filter((o) => !o.leaving));
      }
      // forceCollide and forceLink cache radii and distances; refresh them.
      this.sim.force<d3.ForceCollide<Bubble>>("collide")!.radius(collideRadius);
      this.sim.force<d3.ForceLink<Bubble, Link>>("link")!.distance(linkDistance);
      // Keep the physics awake while sizes change, so neighbours make room.
      if (moving && this.sim.alpha() < 0.05) this.sim.alpha(0.05).restart();
      if (this.sim.alpha() < this.sim.alphaMin()) this.draw();
      if (!moving) {
        this.timer?.stop();
        this.timer = null;
      }
    });
  }

  private draw(): void {
    this.fitView();
    this.nodeLayer
      .selectAll<SVGGElement, Bubble>("g.node")
      .attr("transform", (d) => `translate(${d.x},${d.y}) scale(${d.r / d.node.radius})`)
      .attr("opacity", (d) => (d.leaving ? (d.leaving.r ? d.r / d.leaving.r : 0) : null));
    this.edgeLayer
      .selectAll<SVGLineElement, Link>("line.edge")
      .attr("x1", (l) => (l.source as Bubble).x ?? 0)
      .attr("y1", (l) => (l.source as Bubble).y ?? 0)
      .attr("x2", (l) => (l.target as Bubble).x ?? 0)
      .attr("y2", (l) => (l.target as Bubble).y ?? 0);
  }

  /** Centre the bubbles in the view, zooming out (down to MIN_SCALE) if they
   *  do not fit. The transform is eased so the view does not jump. Bubbles
   *  that still do not fit at MIN_SCALE are kept inside the visible area. */
  private fitView(): void {
    const all = [...this.bubbles.values()];
    if (!all.length) return;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const b of all) {
      x0 = Math.min(x0, (b.x ?? 0) - b.r);
      y0 = Math.min(y0, (b.y ?? 0) - b.r);
      x1 = Math.max(x1, (b.x ?? 0) + b.r);
      y1 = Math.max(y1, (b.y ?? 0) + b.r);
    }
    const k = Math.max(MIN_SCALE, Math.min(1, (W - 2 * MARGIN) / (x1 - x0), (H - 2 * MARGIN) / (y1 - y0)));
    const target = { k, x: W / 2 - k * (x0 + x1) / 2, y: H / 2 - k * (y0 + y1) / 2 };
    const ease = 0.08;
    this.view.k += (target.k - this.view.k) * ease;
    this.view.x += (target.x - this.view.x) * ease;
    this.view.y += (target.y - this.view.y) * ease;
    // Keep every bubble inside the visible area under the current transform.
    for (const b of all) {
      if (b.leaving) continue;
      b.x = this.inView(b.x ?? W / 2, "x", b.r);
      b.y = this.inView(b.y ?? H / 2, "y", b.r);
    }
    this.content.attr("transform", `translate(${this.view.x},${this.view.y}) scale(${this.view.k})`);
  }

  /** Clamp a coordinate so a bubble of radius r at it is inside the visible area. */
  private inView(v: number, axis: "x" | "y", r: number): number {
    const size = axis === "x" ? W : H;
    const { k } = this.view;
    const lo = (MARGIN - this.view[axis]) / k + r;
    const hi = (size - MARGIN - this.view[axis]) / k - r;
    return lo > hi ? (lo + hi) / 2 : Math.max(lo, Math.min(hi, v));
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

/** Two terms are related when one's words are all in the other ("odd" and
 *  "odd number"): the presenter replaces one with the other. */
function related(a: string, b: string): boolean {
  if (a === b) return false;
  const [short, long] = a.length < b.length ? [a, b] : [b, a];
  const words = new Set(long.split(" "));
  return short.split(" ").every((w) => words.has(w));
}

function collideRadius(d: Bubble): number {
  return d.r + PAD;
}

function linkDistance(l: Link): number {
  const a = l.source as Bubble;
  const b = l.target as Bubble;
  return (a.r ?? 30) + (b.r ?? 30) + LINK_GAP;
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
