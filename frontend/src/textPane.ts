// "Texto original": the live text as paragraph blocks (one per segment), with
// the mentions of each bubble underlined. The pending tail (not yet analysed)
// is grey with a caret. Clicking a mention selects its bubble.
import type { Paragraph } from "./contracts";
import { marksIn, splitByMarks, type Mark } from "./spans";

export class TextPane {
  onSelect: (nodeId: string) => void = () => {};

  private text = "";
  private committedUpto = 0;
  private paragraphs: Paragraph[] = [];
  private marks: Mark[] = []; // all mention spans, sorted by start
  private blocks = new Map<number, { el: HTMLDivElement; key: string }>();
  private pendingBlock: HTMLDivElement;
  private pending: HTMLSpanElement;
  private caret: HTMLSpanElement;
  private active: string | null = null;

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
  setView(text: string, committedUpto: number, paragraphs: Paragraph[], marks: Mark[]): void {
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
      block.el.dataset.label = `Tramo ${i + 1}${p.label ? ` · ${p.label}` : ""}`;
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

  /** Highlight the mentions of one bubble (or none). */
  setActive(nodeId: string | null): void {
    this.active = nodeId;
    this.applyActive();
  }

  scrollToFirst(nodeId: string): void {
    const hit = [...this.root.querySelectorAll<HTMLElement>(".m")].find((m) => idsOf(m).includes(nodeId));
    hit?.scrollIntoView({ block: "center", behavior: "smooth" });
  }

  private renderRange(start: number, end: number, marks: Mark[]): Node[] {
    return splitByMarks(start, end, marks).map((piece) => {
      const t = this.text.slice(piece.start, piece.end);
      if (!piece.ids.length) return document.createTextNode(t);
      const m = span("m");
      m.textContent = t;
      // JSON, not space-separated: n-gram ids contain spaces ("odd number").
      m.dataset.ids = JSON.stringify(piece.ids);
      m.dataset.start = String(piece.start); // character offsets, for traceability checks
      m.dataset.end = String(piece.end);
      return m;
    });
  }

  private applyActive(): void {
    for (const m of this.root.querySelectorAll<HTMLElement>(".m")) {
      m.classList.toggle("hl", !!this.active && idsOf(m).includes(this.active));
    }
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
