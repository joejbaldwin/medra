// The window manager: pages of 2 × 2 slots holding the chat and the
// visualization windows. The rules for moving windows live in layout.ts; this
// file draws the pages and handles the pointer and keyboard. Windows are
// placed with CSS grid lines, so moving one never rebuilds its contents (the
// D3 views keep running and the conversation keeps its scroll position).
import {
  CELL_NAMES,
  cellsOf,
  chatExpanded,
  colOf,
  emptyPage,
  firstPage,
  move,
  neighbourCell,
  place,
  remove,
  rowOf,
  setChatExpanded,
  setSpan,
  spanOf,
  windowsOf,
  type Cell,
  type Page,
  type Span,
  type VizKind,
  type WindowId,
} from "./layout";

export const VIZ_TITLES: Record<VizKind, string> = {
  map: "Mapa de conceptos",
  timeline: "Temas a lo largo de la traza",
  steps: "Pasos del agente",
};

// How to read each view: the window title's tooltip (kept off the window itself).
const VIZ_HINTS: Record<VizKind, string> = {
  map: "Tamaño = menciones · Color = tema · Enlace = coocurrencia en la misma oración",
  timeline: "Densidad de menciones por tema (ventana de ±6 palabras)",
  steps: "Un paso por tramo; el marcador que lo abre va sobre la flecha. Arco discontinuo = vuelve a un tema anterior.",
};

const MAX_PAGES = 6;

export interface WindowContent {
  el: HTMLElement;
  destroy(): void;
}

export interface DashboardOptions {
  root: HTMLElement; // holds one <section> per page
  pager: HTMLElement; // the page tabs
  pagerAdd: HTMLButtonElement; // the "+" next to them
  chat: HTMLElement; // the chat window (static markup in index.html)
  chatToggle: HTMLButtonElement;
  createPanel(kind: VizKind): WindowContent;
  openPicker(page: number, cell: Cell, origin: HTMLElement): void;
  notify(message: string, visible?: boolean): void;
}

interface Win {
  el: HTMLElement;
  grip: HTMLButtonElement;
  content: WindowContent | null; // null for the chat
  spanButton?: HTMLButtonElement; // visualizations only: grow to two cells, or shrink back
}

export class Dashboard {
  private pages: Page[] = [firstPage(), emptyPage()];
  private active = 0;
  private sections: HTMLElement[] = [];
  private windows: Map<WindowId, Win>[] = []; // per page, by window id
  private slots: Map<Cell, HTMLElement>[] = []; // per page, empty slots by cell
  private chatWin: Win;

  constructor(private o: DashboardOptions) {
    const grip = o.chat.querySelector<HTMLButtonElement>(".grip")!;
    this.chatWin = { el: o.chat, grip, content: null };
    this.bindGrip(grip, "chat", "Conversación");
    o.chatToggle.addEventListener("click", () => this.toggleChat());
    o.pagerAdd.addEventListener("click", () => this.addPage());
    o.pager.addEventListener("keydown", (e) => this.pagerKey(e));
    this.render();
  }

  /** Visualizations on a page (the picker offers to move these rather than add them). */
  kindsOn(page: number): Set<VizKind> {
    return new Set(this.pages[page].cells.filter((w): w is VizKind => !!w && w !== "chat"));
  }

  /** Fill a slot from the picker. */
  add(page: number, cell: Cell, kind: VizKind): void {
    const moving = this.kindsOn(page).has(kind);
    this.pages[page] = place(this.pages[page], cell, kind);
    this.render();
    const win = this.windows[page].get(kind);
    win?.grip.focus();
    this.o.notify(`${VIZ_TITLES[kind]} ${moving ? "movido" : "añadido"} ${CELL_NAMES[cell]}.`);
  }

  // ------------------------------------------------------------ rendering

  private render(): void {
    this.renderPager();
    this.pages.forEach((page, i) => this.renderPage(page, i));
  }

  private renderPager(): void {
    const tabs = this.pages.map((_, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.role = "tab";
      b.id = `page-tab-${i}`;
      b.textContent = String(i + 1);
      b.setAttribute("aria-label", `Página ${i + 1}`);
      b.setAttribute("aria-selected", String(i === this.active));
      b.setAttribute("aria-controls", `page-${i}`);
      b.tabIndex = i === this.active ? 0 : -1;
      b.addEventListener("click", () => this.showPage(i));
      return b;
    });
    this.o.pager.replaceChildren(...tabs);
    this.o.pagerAdd.hidden = this.pages.length >= MAX_PAGES;
  }

  private showPage(i: number, focusTab = false): void {
    this.active = i;
    this.render();
    if (focusTab) document.getElementById(`page-tab-${i}`)?.focus();
  }

  private addPage(): void {
    this.pages.push(emptyPage());
    this.showPage(this.pages.length - 1, true);
    this.o.notify(`Página ${this.pages.length} creada, con cuatro espacios vacíos.`);
  }

  private pagerKey(e: KeyboardEvent): void {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    this.showPage((this.active + step + this.pages.length) % this.pages.length, true);
  }

  private renderPage(page: Page, i: number): void {
    let section = this.sections[i];
    if (!section) {
      section = document.createElement("section");
      section.className = "page";
      section.id = `page-${i}`;
      section.role = "tabpanel";
      section.setAttribute("aria-labelledby", `page-tab-${i}`);
      this.o.root.append(section);
      this.sections[i] = section;
      this.windows[i] = new Map();
      this.slots[i] = new Map();
    }
    section.hidden = i !== this.active;
    const wins = this.windows[i];
    const slots = this.slots[i];

    // Close the windows that left the page (their data stays in the session).
    const present = new Set(windowsOf(page).map((w) => w.id));
    for (const [id, win] of wins) {
      if (present.has(id)) continue;
      win.content?.destroy();
      if (win !== this.chatWin) win.el.remove();
      wins.delete(id);
    }

    const order: { el: HTMLElement; cell: Cell }[] = [];
    for (const { id, cells } of windowsOf(page)) {
      let win = wins.get(id);
      if (!win) {
        win = id === "chat" ? this.chatWin : this.createWindow(i, id);
        wins.set(id, win);
      }
      placeAt(win.el, cells);
      if (win.spanButton) syncSpanButton(win.spanButton, spanOf(page, id));
      order.push({ el: win.el, cell: cells[0] });
    }
    page.cells.forEach((w, cell) => {
      if (w) {
        slots.get(cell)?.remove();
        slots.delete(cell);
        return;
      }
      let slot = slots.get(cell);
      if (!slot) {
        slot = this.createSlot(i, cell);
        slots.set(cell, slot);
      }
      placeAt(slot, [cell]);
      order.push({ el: slot, cell });
    });
    // DOM order = reading order (column by column), so Tab follows the layout.
    reorder(section, order.sort((a, b) => a.cell - b.cell).map((x) => x.el));

    if (wins.has("chat")) {
      const expanded = chatExpanded(page);
      this.o.chat.classList.toggle("collapsed", !expanded);
      this.o.chatToggle.setAttribute("aria-expanded", String(expanded));
      const label = expanded ? "Contraer el chat a un cuarto" : "Expandir el chat a toda la columna";
      this.o.chatToggle.setAttribute("aria-label", label);
      this.o.chatToggle.title = label;
    }
  }

  private createWindow(page: number, kind: VizKind): Win {
    const title = VIZ_TITLES[kind];
    const el = document.createElement("section");
    el.className = "win";
    el.dataset.win = kind;
    el.setAttribute("aria-label", title);
    el.innerHTML =
      `<header class="win-bar">${GRIP_BUTTON}<h2 class="win-title"></h2>` +
      `<button class="win-btn win-span" type="button" aria-expanded="false"></button>` +
      `<div class="span-menu" role="menu" hidden>` +
      `<button type="button" role="menuitem" data-span="column">${COLUMN_ICON}<span>Ocupar la columna<small>dos espacios en vertical</small></span></button>` +
      `<button type="button" role="menuitem" data-span="row">${ROW_ICON}<span>Ocupar la fila<small>dos espacios en horizontal</small></span></button>` +
      `</div>` +
      `<button class="win-btn win-close" type="button">${MINUS_ICON}</button></header><div class="win-body"></div>`;
    const heading = el.querySelector<HTMLElement>(".win-title")!;
    heading.textContent = title;
    heading.title = VIZ_HINTS[kind];
    const grip = el.querySelector<HTMLButtonElement>(".grip")!;
    grip.setAttribute("aria-label", `Mover ${title}`);
    const close = el.querySelector<HTMLButtonElement>(".win-close")!;
    close.setAttribute("aria-label", `Quitar ${title}`);
    close.title = "Quitar";
    close.addEventListener("click", () => this.removeViz(page, kind));
    this.bindGrip(grip, kind, title);
    const spanButton = el.querySelector<HTMLButtonElement>(".win-span")!;
    this.bindSpanMenu(page, kind, spanButton, el.querySelector<HTMLElement>(".span-menu")!);
    const content = this.o.createPanel(kind);
    el.querySelector(".win-body")!.append(content.el);
    return { el, grip, content, spanButton };
  }

  /** The span button: on a one-cell window it opens a menu (fill the column or
   *  the row); on a two-cell window it shrinks it back to one cell. */
  private bindSpanMenu(page: number, kind: VizKind, button: HTMLButtonElement, menu: HTMLElement): void {
    const items = [...menu.querySelectorAll<HTMLButtonElement>("[role='menuitem']")];
    const outside = (e: PointerEvent) => {
      const target = e.target as Node;
      if (!menu.contains(target) && !button.contains(target)) close(false);
    };
    const close = (focusButton: boolean) => {
      menu.hidden = true;
      button.setAttribute("aria-expanded", "false");
      document.removeEventListener("pointerdown", outside, true);
      if (focusButton) button.focus();
    };
    button.addEventListener("click", () => {
      if (spanOf(this.pages[page], kind) !== "cell") {
        this.setVizSpan(page, kind, "cell");
        return;
      }
      if (!menu.hidden) {
        close(true);
        return;
      }
      // Say up front which spans fit on this page, rather than failing after the click.
      for (const item of items) {
        const fits = setSpan(this.pages[page], kind, item.dataset.span as Span) !== null;
        item.setAttribute("aria-disabled", String(!fits));
        item.title = fits ? "" : "No hay sitio: hay una ventana de dos espacios en medio o la página está llena.";
      }
      menu.hidden = false;
      button.setAttribute("aria-expanded", "true");
      document.addEventListener("pointerdown", outside, true);
      items[0].focus();
    });
    for (const item of items) {
      item.addEventListener("click", () => {
        close(false);
        this.setVizSpan(page, kind, item.dataset.span as Span);
      });
    }
    menu.addEventListener("keydown", (e) => {
      const i = items.indexOf(document.activeElement as HTMLButtonElement);
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        close(true);
      } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        items[(i + (e.key === "ArrowDown" ? 1 : items.length - 1)) % items.length].focus();
      } else if (e.key === "Tab") {
        close(false);
      }
    });
  }

  private createSlot(page: number, cell: Cell): HTMLElement {
    const slot = document.createElement("div");
    slot.className = "slot";
    slot.innerHTML = `<button class="slot-add" type="button">${PLUS_ICON}<span>Añadir visualización</span></button>`;
    const button = slot.querySelector("button")!;
    button.setAttribute("aria-label", `Añadir visualización ${CELL_NAMES[cell]}`);
    // A slot element always stands for the same cell: it is removed when the cell fills.
    button.addEventListener("click", () => this.o.openPicker(page, cell, button));
    return slot;
  }

  // ------------------------------------------------------------ actions

  private removeViz(page: number, kind: VizKind): void {
    const cell = this.pages[page].cells.indexOf(kind);
    this.pages[page] = remove(this.pages[page], kind);
    this.render();
    this.slots[page].get(cell)?.querySelector("button")?.focus();
    this.o.notify(`${VIZ_TITLES[kind]} quitado. El análisis se conserva.`);
  }

  private setVizSpan(page: number, kind: VizKind, span: Span): void {
    const next = setSpan(this.pages[page], kind, span);
    const title = VIZ_TITLES[kind];
    if (!next) {
      const what = span === "column" ? "ocupar la columna" : "ocupar la fila";
      this.o.notify(`No hay sitio para ${what}: taparía una ventana de dos espacios, o la página está llena.`, true);
      return;
    }
    this.pages[page] = next;
    this.render();
    this.windows[page].get(kind)?.spanButton?.focus();
    const done = { cell: "reducido a un espacio", column: "ampliado a toda la columna", row: "ampliado a toda la fila" }[span];
    this.o.notify(`${title} ${done}.`);
  }

  private toggleChat(): void {
    const i = this.pages.findIndex((p) => p.cells.includes("chat"));
    const expand = !chatExpanded(this.pages[i]);
    const next = setChatExpanded(this.pages[i], expand);
    if (!next) {
      this.o.notify("No hay sitio para expandir el chat: quita una visualización de esta página.", true);
      return;
    }
    this.pages[i] = next;
    this.render();
    this.o.notify(expand ? "Chat expandido a toda la columna." : "Chat contraído; el espacio de arriba queda libre.");
  }

  /** Move a window to a cell (swapping), then keep focus on its handle. */
  private moveWindow(id: WindowId, to: Cell, title: string): void {
    const i = this.active;
    const page = this.pages[i];
    const from = cellsOf(page, id)[0];
    if (from === undefined) return;
    const next = move(page, from, to);
    if (next === page) return;
    this.pages[i] = next;
    this.render();
    this.windows[i].get(id)?.grip.focus();
    const now = cellsOf(next, id);
    const span = spanOf(next, id);
    const where =
      span === "column" ? `a la columna ${colOf(now[0]) ? "derecha" : "izquierda"}`
      : span === "row" ? `a la fila de ${rowOf(now[0]) ? "abajo" : "arriba"}`
      : CELL_NAMES[now[0]];
    this.o.notify(`${title} movido ${where}.`);
  }

  // ------------------------------------------------------------ dragging

  /** The handle drags the window (pointer) or moves it one cell per arrow key. */
  private bindGrip(grip: HTMLButtonElement, id: WindowId, title: string): void {
    grip.setAttribute("aria-describedby", "move-help");
    grip.addEventListener("keydown", (e) => {
      const page = this.pages[this.active];
      const from = cellsOf(page, id);
      if (!from.length) return;
      // A two-cell window moves from its far edge (down and right start from its
      // last cell), so a move along its own span leads nowhere.
      const to = neighbourCell(e.key === "ArrowDown" || e.key === "ArrowRight" ? from[from.length - 1] : from[0], e.key);
      if (to === null && !e.key.startsWith("Arrow")) return;
      e.preventDefault();
      if (to !== null) this.moveWindow(id, to, title);
    });
    grip.addEventListener("pointerdown", (e) => this.drag(e, grip, id, title));
  }

  private drag(e: PointerEvent, grip: HTMLButtonElement, id: WindowId, title: string): void {
    if (e.button !== 0) return;
    const section = this.sections[this.active];
    const win = this.windows[this.active].get(id);
    if (!win) return;
    e.preventDefault(); // no text selection; focus is set below instead
    grip.focus();
    grip.setPointerCapture(e.pointerId);
    const x0 = e.clientX;
    const y0 = e.clientY;
    let ghost: HTMLElement | null = null;
    let target: Cell | null = null;

    const mark = (cell: Cell | null) => {
      for (const child of section.children) {
        const cells = (child as HTMLElement).dataset.cells?.split(",").map(Number) ?? [];
        child.classList.toggle("drop-target", cell !== null && child !== win.el && cells.includes(cell));
      }
    };
    const onMove = (ev: PointerEvent) => {
      if (!ghost) {
        if (Math.hypot(ev.clientX - x0, ev.clientY - y0) < 5) return;
        ghost = document.createElement("div");
        ghost.className = "drag-ghost";
        ghost.textContent = title;
        document.body.append(ghost);
        document.body.classList.add("is-dragging");
        win.el.classList.add("dragging");
      }
      ghost.style.transform = `translate(${ev.clientX + 14}px, ${ev.clientY + 10}px)`;
      target = cellAtPoint(section, ev.clientX, ev.clientY);
      mark(target);
    };
    const finish = (commit: boolean) => {
      grip.removeEventListener("pointermove", onMove);
      grip.removeEventListener("pointerup", onUp);
      grip.removeEventListener("pointercancel", onCancel);
      window.removeEventListener("keydown", onKey, true);
      if (grip.hasPointerCapture(e.pointerId)) grip.releasePointerCapture(e.pointerId);
      mark(null);
      win.el.classList.remove("dragging");
      document.body.classList.remove("is-dragging");
      const dragged = !!ghost;
      ghost?.remove();
      if (commit && dragged && target !== null) this.moveWindow(id, target, title);
    };
    const onUp = () => finish(true);
    const onCancel = () => finish(false);
    const onKey = (ev: KeyboardEvent) => {
      if (ev.key !== "Escape") return;
      ev.stopPropagation();
      finish(false);
    };
    grip.addEventListener("pointermove", onMove);
    grip.addEventListener("pointerup", onUp);
    grip.addEventListener("pointercancel", onCancel);
    window.addEventListener("keydown", onKey, true);
  }
}

/** Grid placement through custom properties, so the narrow layout can ignore it. */
function placeAt(el: HTMLElement, cells: Cell[]): void {
  const cols = cells.map(colOf);
  const rows = cells.map(rowOf);
  el.dataset.cells = cells.join(",");
  el.dataset.span = cells.length < 2 ? "cell" : cols[0] === cols[1] ? "column" : "row";
  el.style.setProperty("--col", String(Math.min(...cols) + 1));
  el.style.setProperty("--row", String(Math.min(...rows) + 1));
  el.style.setProperty("--cols", String(new Set(cols).size));
  el.style.setProperty("--rows", String(new Set(rows).size));
}

function syncSpanButton(button: HTMLButtonElement, span: Span): void {
  const grown = span !== "cell";
  button.innerHTML = grown ? SHRINK_ICON : GROW_ICON;
  const label = grown ? "Reducir a un espacio" : "Ampliar a dos espacios";
  button.setAttribute("aria-label", label);
  button.title = label;
  if (grown) button.removeAttribute("aria-haspopup");
  else button.setAttribute("aria-haspopup", "menu");
}

/** The cell under a point, from the windows' and slots' boxes (null in a gap). */
function cellAtPoint(section: HTMLElement, x: number, y: number): Cell | null {
  for (const child of section.children) {
    const el = child as HTMLElement;
    const r = el.getBoundingClientRect();
    if (x < r.left || x > r.right || y < r.top || y > r.bottom) continue;
    const cells = el.dataset.cells?.split(",").map(Number) ?? [];
    if (cells.length < 2) return cells[0] ?? null;
    // Cells are listed in order: the second is below (a column) or to the right (a row).
    const second = el.dataset.span === "row" ? x > r.left + r.width / 2 : y > r.top + r.height / 2;
    return cells[second ? 1 : 0];
  }
  return null;
}

/** Put the children in this order. Moving a node resets its scroll positions and
 *  drops focus inside it, so both are restored afterwards. */
function reorder(parent: HTMLElement, wanted: HTMLElement[]): void {
  const current = [...parent.children];
  if (current.length === wanted.length && wanted.every((el, i) => current[i] === el)) return;
  const scrolls = [...parent.querySelectorAll<HTMLElement>("[data-keep-scroll]")].map((el) => [el, el.scrollTop, el.scrollLeft] as const);
  const focused = document.activeElement as HTMLElement | null;
  parent.append(...wanted);
  for (const [el, top, left] of scrolls) {
    el.scrollTop = top;
    el.scrollLeft = left;
  }
  if (focused && focused !== document.activeElement && parent.contains(focused)) focused.focus({ preventScroll: true });
}

export const GRIP_ICON = `<svg viewBox="0 0 12 18" width="12" height="18" aria-hidden="true"><g fill="currentColor"><circle cx="3" cy="3" r="1.6"/><circle cx="9" cy="3" r="1.6"/><circle cx="3" cy="9" r="1.6"/><circle cx="9" cy="9" r="1.6"/><circle cx="3" cy="15" r="1.6"/><circle cx="9" cy="15" r="1.6"/></g></svg>`;
const GRIP_BUTTON = `<button class="grip" type="button">${GRIP_ICON}</button>`;
const MINUS_ICON = `<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M3 8h10" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`;
const GROW_ICON = `<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M9.5 2.5h4v4M6.5 13.5h-4v-4M13.5 2.5L9 7M2.5 13.5L7 9" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const SHRINK_ICON = `<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true"><path d="M13.5 6.5h-4v-4M2.5 9.5h4v4M9.5 6.5L14 2M6.5 9.5L2 14" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
const COLUMN_ICON = `<svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><rect x="2.5" y="2.5" width="6.5" height="15" rx="1.5" fill="currentColor"/><rect x="11" y="2.5" width="6.5" height="6.5" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.3"/><rect x="11" y="11" width="6.5" height="6.5" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>`;
const ROW_ICON = `<svg viewBox="0 0 20 20" width="20" height="20" aria-hidden="true"><rect x="2.5" y="2.5" width="15" height="6.5" rx="1.5" fill="currentColor"/><rect x="2.5" y="11" width="6.5" height="6.5" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.3"/><rect x="11" y="11" width="6.5" height="6.5" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.3"/></svg>`;
const PLUS_ICON = `<svg class="slot-plus" viewBox="0 0 48 48" width="56" height="56" aria-hidden="true"><path d="M24 6v36M6 24h36" stroke="currentColor" stroke-width="4" stroke-linecap="round"/></svg>`;
