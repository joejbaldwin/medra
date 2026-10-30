// The dashboard's copy of the view, rebuilt from ViewUpdate diffs.
// Only bookkeeping: every decision in here was made by the presenter.
import type { Edge, Highlight, Node, Paragraph, Stats, TickerItem, ViewUpdate } from "./contracts";

const TICKER_KEPT = 12;

export class ViewState {
  nodes = new Map<string, Node>();
  edges = new Map<string, Edge>();
  highlights = new Map<string, Highlight>(); // key "kind:id"
  paragraphs = new Map<number, Paragraph>();
  ticker: TickerItem[] = [];
  stats: Stats | null = null;
  committedUpto = 0;

  reset(): void {
    this.nodes.clear();
    this.edges.clear();
    this.highlights.clear();
    this.paragraphs.clear();
    this.ticker = [];
    this.stats = null;
    this.committedUpto = 0;
  }

  apply(view: ViewUpdate): void {
    if (view.kind === "snapshot") this.reset();
    this.committedUpto = view.committed_upto;
    upsert(this.nodes, view.nodes, (n) => n.id, view.removed.nodes);
    upsert(this.edges, view.edges, (e) => e.id, view.removed.edges);
    upsert(this.highlights, view.highlights, (h) => `${h.kind}:${h.id}`, view.removed.highlights);
    upsert(this.paragraphs, view.paragraphs, (p) => p.segment_id, view.removed.paragraphs);
    this.ticker = [...this.ticker, ...view.ticker].slice(-TICKER_KEPT);
    if (view.stats) this.stats = view.stats;
  }

  /** Paragraphs in text order. */
  orderedParagraphs(): Paragraph[] {
    return [...this.paragraphs.values()].sort((a, b) => a.start - b.start);
  }

  /** Bubbles linked to `id` by an edge. */
  neighbours(id: string): Set<string> {
    const out = new Set<string>();
    for (const e of this.edges.values()) {
      if (e.a === id) out.add(e.b);
      if (e.b === id) out.add(e.a);
    }
    return out;
  }

  nodeSpans(id: string): [number, number][] {
    return this.highlights.get(`node:${id}`)?.spans ?? [];
  }
}

function upsert<K, V>(map: Map<K, V>, items: V[], key: (v: V) => K, removed: K[]): void {
  for (const k of removed) map.delete(k);
  for (const item of items) map.set(key(item), item);
}
