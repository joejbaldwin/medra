// "Texto original": the live text as paragraph blocks (one per segment, in its
// topic's colour), with the mentions of each bubble underlined and the
// discourse marker that opened the segment highlighted. The pending tail (not
// yet analysed) is grey with a caret. Clicking a mention selects its bubble.
import { marksIn, splitByMarks, type Mark } from "./spans";

/** A paragraph block as the pane draws it (decided in main.ts from the view). */
export interface Block {
  segment_id: number;
  start: number;
  end: number;
  label: string;
  slot: number;
  provisional: boolean;
}

export class TextPane {
  onSelect: (nodeId: string) => void = () => {};

  private text = "";
  private committedUpto = 0;
  private paragraphs: Block[] = [];
  private marks: Mark[] = []; // all mention spans, sorted by start
  private blocks = new Map<number, { el: HTMLDivElement; key: string }>();
  private pendingBlock: HTMLDivElement;
  private pending: HTMLSpanElement;
  private caret: HTMLSpanElement;
  private active: string | null = null;
  private activeSegments = new Set<number>();

  constructor(private root: HTMLElement) {
    this.pendingBlock = div("para pending-para");
    this.pending = span("pending");
    this.caret = span("caret");
    this.caret.hidden = true;
    root.addEventListener("click", (e) => {
      const m = (e.target as HTMLElement).closest<HTMLElement>(".m");
      const ids = m ? idsOf(m) : [];
      if (ids.length) this.onSelect(ids[0]); // the longest mark where mentions overlap
    });
  }

  reset(): void {
    this.text = "";
    this.committedUpto = 0;
    this.paragraphs = [];
    this.marks = [];
    this.blocks.clear();
    this.active = null;
    this.activeSegments = new Set();
    this.root.replaceChildren();
  }

  setStreaming(on: boolean): void {
    this.caret.hidden = !on;
  }

  /** New raw text arrived (cheap: only the pending tail changes). */
  setText(text: string): void {
    this.text = text;
    this.renderPending();
  }

  /** A view update: new commit frontier, paragraphs and mention spans.
   *  `text` must be the full text received so far: setText runs once per
   *  animation frame, so the pane's copy can be a frame behind, and a block
   *  rendered from it would miss its last words (and be cached that way). */
  setView(text: string, committedUpto: number, paragraphs: Block[], marks: Mark[]): void {
    const follow = this.atBottom();
    this.text = text;
    this.committedUpto = committedUpto;
    this.paragraphs = paragraphs;
    this.marks = [...marks].sort((a, b) => a.start - b.start || b.end - a.end);
    const keep = new Set<number>();
    paragraphs.forEach((p, i) => {
      keep.add(p.segment_id);
      const inside = marksIn(this.marks, p.start, p.end);
      // Re-render a block only if its text range or its mentions changed.
      const key = `${p.start}:${p.end}:${inside.map((m) => `${m.start}-${m.end}-${m.id}`).join(",")}`;
      let block = this.blocks.get(p.segment_id);
      if (!block) {
        block = { el: div("para"), key: "" };
        this.blocks.set(p.segment_id, block);
      }
      if (block.key !== key) {
        block.el.replaceChildren(...this.renderRange(p.start, p.end, inside));
        block.key = key;
      }
      block.el.dataset.seg = String(p.segment_id);
      block.el.dataset.start = String(p.start);
      block.el.dataset.end = String(p.end);
      block.el.dataset.label = p.label;
      block.el.style.setProperty("--c", `var(--c${p.slot % 6})`);
      block.el.classList.toggle("provisional", p.provisional);
      if (this.root.children[i] !== block.el) this.root.insertBefore(block.el, this.root.children[i] ?? null);
    });
    for (const [seg, block] of this.blocks) {
      if (!keep.has(seg)) {
        block.el.remove();
        this.blocks.delete(seg);
      }
    }
    this.applyActive();
    this.renderPending(follow);
  }

  /** Highlight the mentions of one bubble (or none), and the paragraphs of a
   *  selected step or topic. */
  setActive(nodeId: string | null, segments: Set<number> = new Set()): void {
    this.active = nodeId;
    this.activeSegments = segments;
    this.applyActive();
  }

  scrollToFirst(nodeId: string): void {
    const hit = [...this.root.querySelectorAll<HTMLElement>(".m")].find((m) => idsOf(m).includes(nodeId));
    hit?.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  scrollToSegment(segmentId: number): void {
    this.blocks.get(segmentId)?.el.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  private renderRange(start: number, end: number, marks: Mark[]): Node[] {
    return splitByMarks(start, end, marks).map((piece) => {
      const t = this.text.slice(piece.start, piece.end);
      if (!piece.ids.length && !piece.marker) return document.createTextNode(t);
      const m = span(piece.ids.length ? "m" : "mk");
      if (piece.ids.length && piece.marker) m.classList.add("mk");
      m.textContent = t;
      m.dataset.start = String(piece.start); // character offsets, for traceability checks
      m.dataset.end = String(piece.end);
      // JSON, not space-separated: n-gram ids contain spaces ("odd number").
      if (piece.ids.length) m.dataset.ids = JSON.stringify(piece.ids);
      return m;
    });
  }

  private applyActive(): void {
    for (const m of this.root.querySelectorAll<HTMLElement>(".m")) {
      m.classList.toggle("hl", !!this.active && idsOf(m).includes(this.active));
    }
    for (const [seg, block] of this.blocks) block.el.classList.toggle("sel", this.activeSegments.has(seg));
  }

  private renderPending(follow = this.atBottom()): void {
    const last = this.paragraphs[this.paragraphs.length - 1];
    const lastEnd = last ? last.end : 0;
    const tail = this.text.slice(Math.max(lastEnd, this.committedUpto));
    const gap = this.text.slice(lastEnd, Math.max(lastEnd, this.committedUpto)) + tail;
    // The tail continues the last paragraph unless a blank line starts a new one.
    const newParagraph = !last || /\n[ \t]*\n/.test(gap);
    this.pending.textContent = newParagraph ? tail.replace(/^\s+/, "") : tail;
    const host = newParagraph ? this.pendingBlock : this.blocks.get(last.segment_id)!.el;
    if (newParagraph && this.pendingBlock.parentElement !== this.root) this.root.append(this.pendingBlock);
    if (!newParagraph) this.pendingBlock.remove();
    host.append(this.pending, this.caret);
    if (follow) this.root.scrollTop = this.root.scrollHeight;
  }

  private atBottom(): boolean {
    return this.root.scrollHeight - this.root.scrollTop - this.root.clientHeight < 40;
  }
}

function idsOf(m: HTMLElement): string[] {
  return m.dataset.ids ? (JSON.parse(m.dataset.ids) as string[]) : [];
}

function div(cls: string): HTMLDivElement {
  const el = document.createElement("div");
  el.className = cls;
  return el;
}

function span(cls: string): HTMLSpanElement {
  const el = document.createElement("span");
  el.className = cls;
  return el;
}
