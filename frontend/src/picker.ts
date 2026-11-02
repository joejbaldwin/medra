// "Añadir visualización": the modal that fills an empty slot. A native
// <dialog> opened with showModal() makes the rest of the page inert and closes
// on Escape; Tab is also kept inside it, and focus goes back to the control
// that opened it. The previews are fixed drawings, labelled «Ejemplo», so they
// are not mistaken for analysis of the current trace.
import type { VizKind } from "./layout";
import { esc, fold } from "./util";

type Category = "Conceptos" | "Temas" | "Pasos";

interface Item {
  kind: VizKind;
  title: string;
  description: string;
  category: Category;
  keywords: string; // extra search terms
  preview: string; // inline SVG
}

const ITEMS: Item[] = [
  {
    kind: "map",
    title: "Mapa de conceptos",
    description: "Explora los términos, sus menciones y las relaciones entre ellos.",
    category: "Conceptos",
    keywords: "burbujas términos coocurrencia grafo palabras",
    preview: mapPreview(),
  },
  {
    kind: "timeline",
    title: "Línea de temas",
    description: "Observa cómo cambia la presencia de cada tema a lo largo de la traza.",
    category: "Temas",
    keywords: "temas tiempo densidad curva gráfico evolución",
    preview: timelinePreview(),
  },
  {
    kind: "steps",
    title: "Pasos del agente",
    description: "Recorre los tramos del razonamiento y sus conexiones.",
    category: "Pasos",
    keywords: "tramos segmentos marcadores retoma grafo",
    preview: stepsPreview(),
  },
];

export interface PickerRequest {
  present: Set<VizKind>; // already on this page: offered as "move here"
  origin: HTMLElement; // gets focus back when the picker closes without adding
  onSelect(kind: VizKind): void;
}

export class Picker {
  private search: HTMLInputElement;
  private chips: HTMLButtonElement[];
  private cards: HTMLElement;
  private empty: HTMLElement;
  private category = "";
  private request: PickerRequest | null = null;
  private chosen = false;

  constructor(private dialog: HTMLDialogElement) {
    this.search = dialog.querySelector<HTMLInputElement>(".picker-search input")!;
    this.chips = [...dialog.querySelectorAll<HTMLButtonElement>(".chips button")];
    this.cards = dialog.querySelector<HTMLElement>(".cards")!;
    this.empty = dialog.querySelector<HTMLElement>(".picker-empty")!;
    this.search.addEventListener("input", () => this.filter());
    for (const chip of this.chips) {
      chip.addEventListener("click", () => {
        this.category = chip.dataset.cat ?? "";
        this.filter();
      });
    }
    dialog.querySelector(".picker-close")!.addEventListener("click", () => dialog.close());
    // A click on the dimmed backdrop lands on the <dialog> itself.
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) dialog.close();
    });
    dialog.addEventListener("keydown", (e) => this.trapTab(e));
    dialog.addEventListener("close", () => {
      const req = this.request;
      this.request = null;
      if (req && !this.chosen && req.origin.isConnected) req.origin.focus();
    });
  }

  open(request: PickerRequest): void {
    this.request = request;
    this.chosen = false;
    this.category = "";
    this.search.value = "";
    this.renderCards();
    this.filter();
    this.dialog.showModal();
    this.search.focus();
  }

  private renderCards(): void {
    const present = this.request?.present ?? new Set();
    this.cards.replaceChildren(
      ...ITEMS.map((item) => {
        const card = document.createElement("article");
        card.className = "viz-card";
        card.role = "listitem";
        card.dataset.kind = item.kind;
        const moving = present.has(item.kind);
        const action = moving ? "Mover aquí" : "Añadir";
        card.innerHTML =
          `<div class="preview" aria-hidden="true">${item.preview}<span class="preview-tag">Ejemplo</span></div>` +
          `<h3>${esc(item.title)}</h3><p>${esc(item.description)}</p>` +
          (moving ? `<p class="card-note">Ya está en esta página: se moverá a este espacio.</p>` : "") +
          `<button class="add-btn" type="button" aria-label="${action}: ${esc(item.title)}">` +
          `<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M8 2.5v11M2.5 8h11" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>` +
          `${action}</button>`;
        card.querySelector("button")!.addEventListener("click", () => this.choose(item.kind));
        return card;
      }),
    );
  }

  private filter(): void {
    const q = fold(this.search.value.trim());
    let shown = 0;
    for (const card of this.cards.querySelectorAll<HTMLElement>(".viz-card")) {
      const item = ITEMS.find((i) => i.kind === card.dataset.kind)!;
      const haystack = fold(`${item.title} ${item.description} ${item.category} ${item.keywords}`);
      const ok = (!this.category || item.category === this.category) && (!q || q.split(/\s+/).every((w) => haystack.includes(w)));
      card.hidden = !ok;
      shown += ok ? 1 : 0;
    }
    this.empty.hidden = shown > 0;
    for (const chip of this.chips) chip.setAttribute("aria-pressed", String((chip.dataset.cat ?? "") === this.category));
  }

  private choose(kind: VizKind): void {
    const req = this.request;
    this.chosen = true;
    this.dialog.close();
    req?.onSelect(kind);
  }

  /** Keep Tab and Shift+Tab cycling inside the dialog. */
  private trapTab(e: KeyboardEvent): void {
    if (e.key !== "Tab") return;
    const focusable = [...this.dialog.querySelectorAll<HTMLElement>("button, input, [tabindex]:not([tabindex='-1'])")].filter(
      (el) => !el.closest("[hidden]") && !(el as HTMLButtonElement).disabled,
    );
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }
}

// ---------------------------------------------------------------- previews
// Representative drawings of each view (mock-ups, not live data). Colours come
// from the theme's palette, so they follow light and dark mode.

function mapPreview(): string {
  const bubble = (x: number, y: number, r: number, slot: number, label: string, lx: number, ly: number, anchor = "start") =>
    `<circle cx="${x}" cy="${y}" r="${r}" class="pv-b" style="--c: var(--c${slot})"/>` +
    `<text x="${lx}" y="${ly}" text-anchor="${anchor}" class="pv-t">${label}</text>`;
  return (
    `<svg viewBox="0 0 320 210" class="pv">` +
    `<g class="pv-e"><line x1="150" y1="112" x2="76" y2="68"/><line x1="150" y1="112" x2="74" y2="160"/>` +
    `<line x1="150" y1="112" x2="240" y2="64"/><line x1="150" y1="112" x2="248" y2="150"/><line x1="150" y1="112" x2="150" y2="70"/></g>` +
    bubble(76, 68, 22, 0, "sesión", 106, 64) +
    bubble(74, 160, 22, 0, "registro", 98, 190) +
    bubble(240, 64, 25, 1, "email", 270, 72) +
    bubble(248, 150, 30, 1, "contraseña", 252, 200, "middle") +
    `<circle cx="150" cy="112" r="37" class="pv-b pv-strong" style="--c: var(--c0)"/>` +
    `<text x="150" y="117" text-anchor="middle" class="pv-t pv-on">login</text></svg>`
  );
}

function timelinePreview(): string {
  const a = "M34,150 C60,150 70,40 92,40 C114,40 120,118 146,118 C172,118 180,58 204,58 C228,58 236,132 256,132 C272,132 280,104 296,104";
  const b = "M34,120 C52,120 56,76 72,76 C92,76 96,150 118,150 C140,150 150,60 170,60 C190,60 196,148 220,148 C242,148 256,120 296,140";
  return (
    `<svg viewBox="0 0 320 210" class="pv">` +
    `<g class="pv-grid"><line x1="34" x2="296" y1="40" y2="40"/><line x1="34" x2="296" y1="95" y2="95"/><line x1="34" x2="296" y1="150" y2="150"/>` +
    `<line class="pv-dash" x1="100" x2="100" y1="30" y2="150"/><line class="pv-dash" x1="166" x2="166" y1="30" y2="150"/><line class="pv-dash" x1="232" x2="232" y1="30" y2="150"/></g>` +
    `<path d="${b} L296,150 L34,150 Z" class="pv-area" style="--c: var(--c1)"/><path d="${b}" class="pv-line" style="--c: var(--c1)"/>` +
    `<path d="${a} L296,150 L34,150 Z" class="pv-area" style="--c: var(--c0)"/><path d="${a}" class="pv-line" style="--c: var(--c0)"/>` +
    `<g class="pv-t pv-small"><text x="38" y="168">T1</text><text x="104" y="168">T2</text><text x="170" y="168">T3</text><text x="236" y="168">T4</text></g>` +
    `<g class="pv-t pv-small"><circle cx="70" cy="190" r="5" style="fill: var(--c0)"/><text x="80" y="194">login · sesión</text>` +
    `<circle cx="178" cy="190" r="5" style="fill: var(--c1)"/><text x="188" y="194">contraseña · email</text></g></svg>`
  );
}

function stepsPreview(): string {
  const names = ["Planificación", "Desarrollo", "Verificación", "Conclusión"];
  const xs = [52, 124, 196, 268];
  const nodes = xs
    .map((x, i) => {
      const slot = i % 2 ? 1 : 0;
      const arrow = i ? `<path d="M${xs[i - 1] + 22},100 L${x - 26},100" class="pv-arrow"/><path d="M${x - 30},95 L${x - 23},100 L${x - 30},105" class="pv-arrow"/>` : "";
      return (
        arrow +
        `<circle cx="${x}" cy="100" r="18" style="fill: var(--c${slot})"/>` +
        `<text x="${x}" y="105" text-anchor="middle" class="pv-t pv-on">${i + 1}</text>` +
        `<text x="${x}" y="138" text-anchor="middle" class="pv-t pv-small">${names[i]}</text>`
      );
    })
    .join("");
  return (
    `<svg viewBox="0 0 320 210" class="pv">${nodes}` +
    `<path d="M196,${150} C196,175 124,175 124,152" class="pv-arc"/><path d="M119,158 L124,150 L129,158" class="pv-arc pv-arc-head"/></svg>`
  );
}
