// Guided tour of the dashboard (study practice: index.html?estudio=1&guia=1).
// A welcome card over the blurred panel, then one step per area: that area
// stays sharp inside a ring, the rest is greyed and blurred, and a small tag
// next to it says what it is. Click (or Enter / →) to go on, Esc to skip.
//
// The shade is four boxes around the hole rather than one box with a cut-out,
// so backdrop-filter can blur everything except the highlighted area.
import { esc } from "./util";

export interface TourStep {
  /** The area to highlight; none for a centred card (welcome, end). */
  target?: () => Element | null;
  title: string;
  text: string;
  /** Label of the button that leaves this step. */
  next?: string;
}

const PAD = 8; // space between the area and its ring
const GAP = 14; // space between the ring and the tag
const MARGIN = 12; // the tag keeps this far from the window's edges

export class Tour {
  private root = document.createElement("div");
  private shades = [0, 1, 2, 3].map(() => document.createElement("div"));
  private ring = document.createElement("div");
  private tip = document.createElement("div");
  private at = 0;
  private ready = false;
  private readonly onResize = () => this.place();
  private readonly onKey = (e: KeyboardEvent) => {
    if (e.key === "Escape") this.end();
    else if (e.key === "Enter" || e.key === "ArrowRight") this.next();
    else if (e.key === "ArrowLeft") this.show(Math.max(0, this.at - 1));
    else return;
    e.preventDefault();
  };

  constructor(
    private steps: TourStep[],
    private onEnd: () => void,
  ) {
    this.root.className = "tour";
    for (const s of this.shades) {
      s.className = "tour-shade";
      s.addEventListener("click", () => this.next());
    }
    this.ring.className = "tour-ring";
    this.ring.addEventListener("click", () => this.next());
    this.tip.className = "tour-tip";
    this.tip.setAttribute("role", "dialog");
    this.tip.setAttribute("aria-modal", "true");
    this.root.append(...this.shades, this.ring, this.tip);
  }

  get running(): boolean {
    return this.root.isConnected;
  }

  /** Show the first step. Until `setReady`, its button waits (the panel is loading). */
  start(): void {
    document.body.append(this.root);
    addEventListener("resize", this.onResize);
    addEventListener("keydown", this.onKey, true);
    this.show(0);
  }

  setReady(): void {
    this.ready = true;
    if (this.running) this.show(this.at);
  }

  private next(): void {
    if (!this.ready) return;
    if (this.at + 1 < this.steps.length) this.show(this.at + 1);
    else this.end();
  }

  private end(): void {
    if (!this.running) return;
    removeEventListener("resize", this.onResize);
    removeEventListener("keydown", this.onKey, true);
    this.root.remove();
    this.onEnd();
  }

  private show(i: number): void {
    this.at = i;
    const step = this.steps[i];
    const last = i === this.steps.length - 1;
    const counted = this.steps.filter((s) => s.target).length;
    const n = this.steps.slice(0, i + 1).filter((s) => s.target).length;
    const label = this.ready ? (step.next ?? (last ? "Terminar" : "Siguiente")) : "Cargando…";
    this.tip.innerHTML = `
      ${step.target ? `<p class="tour-count">${n} de ${counted}</p>` : ""}
      <h2 class="tour-title">${esc(step.title)}</h2>
      <p class="tour-text">${esc(step.text)}</p>
      <div class="tour-actions">
        ${i > 0 && !last ? `<button type="button" class="tour-skip">Saltar la guía</button>` : ""}
        <button type="button" class="tour-next" ${this.ready ? "" : "disabled"}>${esc(label)}</button>
      </div>`;
    this.tip.querySelector(".tour-next")!.addEventListener("click", () => this.next());
    this.tip.querySelector(".tour-skip")?.addEventListener("click", () => this.end());
    this.place();
    // Re-trigger the tag's entrance animation.
    this.tip.classList.remove("tour-in");
    void this.tip.offsetWidth;
    this.tip.classList.add("tour-in");
    this.tip.querySelector<HTMLButtonElement>(".tour-next")?.focus({ preventScroll: true });
  }

  /** Lay the shades, the ring and the tag out around the current step's area. */
  private place(): void {
    const W = innerWidth;
    const H = innerHeight;
    const el = this.steps[this.at].target?.();
    this.root.classList.toggle("tour-centred", !el); // also if the area is gone
    const box = (s: HTMLElement, x: number, y: number, w: number, h: number) =>
      Object.assign(s.style, { left: `${x}px`, top: `${y}px`, width: `${Math.max(0, w)}px`, height: `${Math.max(0, h)}px` });

    if (!el) {
      box(this.shades[0], 0, 0, W, H);
      for (const s of this.shades.slice(1)) box(s, 0, 0, 0, 0);
      this.ring.hidden = true;
      Object.assign(this.tip.style, { left: "", top: "" });
      return;
    }

    const r = el.getBoundingClientRect();
    const x = Math.max(0, r.left - PAD);
    const y = Math.max(0, r.top - PAD);
    const w = Math.min(W, r.right + PAD) - x;
    const h = Math.min(H, r.bottom + PAD) - y;
    box(this.shades[0], 0, 0, W, y); // above
    box(this.shades[1], 0, y + h, W, H - y - h); // below
    box(this.shades[2], 0, y, x, h); // left
    box(this.shades[3], x + w, y, W - x - w, h); // right
    this.ring.hidden = false;
    box(this.ring, x, y, w, h);

    // The tag goes on whichever side of the area has the most room; if no
    // side fits it, it sits inside the area's lower edge.
    const tw = this.tip.offsetWidth;
    const th = this.tip.offsetHeight;
    const room = { right: W - (x + w), left: x, below: H - (y + h), above: y };
    const side = (Object.keys(room) as (keyof typeof room)[]).sort((a, b) => room[b] - room[a])[0];
    const clampX = (v: number) => Math.min(Math.max(MARGIN, v), W - tw - MARGIN);
    const clampY = (v: number) => Math.min(Math.max(MARGIN, v), H - th - MARGIN);
    let left: number;
    let top: number;
    const fits = side === "left" || side === "right" ? room[side] >= tw + GAP + MARGIN : room[side] >= th + GAP + MARGIN;
    if (!fits) {
      left = clampX(x + (w - tw) / 2);
      top = clampY(y + h - th - 2 * GAP);
    } else if (side === "right" || side === "left") {
      left = side === "right" ? x + w + GAP : x - tw - GAP;
      top = clampY(y + Math.min(h, H - y) / 2 - th / 2);
    } else {
      left = clampX(x + (w - tw) / 2);
      top = side === "below" ? y + h + GAP : y - th - GAP;
    }
    Object.assign(this.tip.style, { left: `${left}px`, top: `${top}px` });
  }
}
