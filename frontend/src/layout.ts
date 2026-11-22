// Dashboard pages as data: each page is a 2 × 2 grid of cells holding a
// window id or nothing. Kept free of DOM code so the move rules can be unit
// tested. A window fills one cell, a whole column (listed in both cells of
// that column) or a whole row. The chat is expanded when it fills its column.
// Visualizations take one cell; enlarging one is a temporary view on top
// (`Expanded`, below) that leaves the page itself unchanged.
// Every rule here keeps all windows: a move swaps, it never overwrites.
//
// Cell numbering is column-major, which is also the reading order:
//   0 | 2
//   1 | 3

export type VizKind = "map" | "timeline" | "steps";
export type WindowId = VizKind | "chat";
export type Cell = number;
/** How much of the grid a window fills. */
export type Span = "cell" | "column" | "row";

export interface Page {
  cells: (WindowId | null)[]; // length 4
}

export const CELLS = 4;
export const colOf = (c: Cell): number => c >> 1;
export const rowOf = (c: Cell): number => c & 1;
export const cellAt = (col: number, row: number): Cell => col * 2 + row;
/** The other cell in the same column. */
export const sibling = (c: Cell): Cell => c ^ 1;
/** The other cell in the same row. */
export const across = (c: Cell): Cell => c ^ 2;

/** The first page (Joe, 2026-11-02): the chat fills the right column and
 *  both slots on the left are empty, for the user to choose views. */
export function firstPage(): Page {
  return { cells: [null, null, "chat", "chat"] };
}

export function emptyPage(): Page {
  return { cells: [null, null, null, null] };
}

export function cellsOf(page: Page, id: WindowId): Cell[] {
  return page.cells.flatMap((w, c) => (w === id ? [c] : []));
}

export function spanOf(page: Page, id: WindowId): Span {
  const at = cellsOf(page, id);
  if (at.length < 2) return "cell";
  return colOf(at[0]) === colOf(at[1]) ? "column" : "row";
}

export function chatExpanded(page: Page): boolean {
  return spanOf(page, "chat") === "column";
}

function swapCols(cells: Page["cells"], a: number, b: number): void {
  for (const row of [0, 1]) {
    const x = cellAt(a, row);
    const y = cellAt(b, row);
    [cells[x], cells[y]] = [cells[y], cells[x]];
  }
}

function swapRows(cells: Page["cells"], a: number, b: number): void {
  for (const col of [0, 1]) {
    const x = cellAt(col, a);
    const y = cellAt(col, b);
    [cells[x], cells[y]] = [cells[y], cells[x]];
  }
}

/** Windows on the page in reading order, each with the cells it covers. */
export function windowsOf(page: Page): { id: WindowId; cells: Cell[] }[] {
  const seen = new Set<WindowId>();
  const out: { id: WindowId; cells: Cell[] }[] = [];
  for (const w of page.cells) {
    if (w && !seen.has(w)) {
      seen.add(w);
      out.push({ id: w, cells: cellsOf(page, w) });
    }
  }
  return out;
}

/** Move the window in cell `from` to cell `to`, swapping with whatever is there.
 *  A window that fills a column moves as a whole column (a row, as a whole
 *  row). A one-cell window dropped on a column-filling window trades columns
 *  with it, taking its column neighbour along, and lands where it was dropped. */
export function move(page: Page, from: Cell, to: Cell): Page {
  const cells = [...page.cells];
  const a = cells[from];
  const b = cells[to];
  if (!a || from === to || a === b) return page;
  const spanA = spanOf(page, a);
  const spanB = b ? spanOf(page, b) : "cell";
  if (spanA === "column") {
    if (colOf(from) === colOf(to)) return page;
    swapCols(cells, colOf(from), colOf(to));
  } else if (spanA === "row") {
    if (rowOf(from) === rowOf(to)) return page;
    swapRows(cells, rowOf(from), rowOf(to));
  } else if (spanB === "column") {
    swapCols(cells, colOf(from), colOf(to));
    // `a` is now in the target column, in its old row: put it in the dropped row.
    if (rowOf(from) !== rowOf(to)) [cells[to], cells[sibling(to)]] = [cells[sibling(to)], cells[to]];
  } else if (spanB === "row") {
    swapRows(cells, rowOf(from), rowOf(to));
    if (colOf(from) !== colOf(to)) [cells[to], cells[across(to)]] = [cells[across(to)], cells[to]];
  } else {
    [cells[from], cells[to]] = [b, a];
  }
  return { cells };
}

/** Put a visualization in an empty cell, or move it there if the page already shows it. */
export function place(page: Page, cell: Cell, kind: VizKind): Page {
  const at = page.cells.indexOf(kind);
  if (at >= 0) return move(page, at, cell);
  if (page.cells[cell] !== null) return page;
  const cells = [...page.cells];
  cells[cell] = kind;
  return { cells };
}

/** Empty the cell of a visualization. The chat cannot be removed. */
export function remove(page: Page, kind: VizKind): Page {
  return { cells: page.cells.map((w) => (w === kind ? null : w)) };
}

/** Make a window fill one cell, its column or its row. Shrinking frees the
 *  other cell (the chat keeps its lower cell, as in the mock-up; other windows
 *  keep the upper or left one). Growing moves a one-cell window it would cover
 *  to an empty cell; when it would cover a two-cell window, or no cell is
 *  free, it returns null and the caller asks the user to make room. */
export function setSpan(page: Page, id: WindowId, span: Span): Page | null {
  const at = cellsOf(page, id);
  if (!at.length) return null;
  if (spanOf(page, id) === span) return page;
  const cells = [...page.cells];
  let home = at[0];
  if (at.length === 2) {
    home = id === "chat" ? at[1] : at[0];
    cells[home === at[0] ? at[1] : at[0]] = null;
  }
  if (span === "cell") return { cells };
  const partner = span === "column" ? sibling(home) : across(home);
  const covered = cells[partner];
  if (covered) {
    if (cells.filter((w) => w === covered).length > 1) return null;
    const free = cells.findIndex((w, c) => w === null && c !== partner && c !== home);
    if (free < 0) return null;
    cells[free] = covered;
  }
  cells[partner] = id;
  return { cells };
}

/** Collapse the chat to the lower cell of its column, or expand it to the whole column. */
export function setChatExpanded(page: Page, expand: boolean): Page | null {
  return setSpan(page, "chat", expand ? "column" : "cell");
}

// ------------------------------------------------------------ enlarging a visualization

/** How a visualization can be enlarged: across its row, down its column, or over the whole page. */
export type Expand = "row" | "column" | "full";
export interface Expanded {
  id: VizKind;
  mode: Expand;
}

/** The cells an enlarged visualization covers (none if it is not on the page).
 *  Enlarging is a view on top of the page, not a change to it: the windows it
 *  covers keep their cells and reappear when it is restored, so it always fits. */
export function coverOf(page: Page, ex: Expanded | null): Cell[] {
  const at = ex ? page.cells.indexOf(ex.id) : -1;
  if (!ex || at < 0) return [];
  if (ex.mode === "full") return [0, 1, 2, 3];
  if (ex.mode === "column") return [cellAt(colOf(at), 0), cellAt(colOf(at), 1)];
  return [cellAt(0, rowOf(at)), cellAt(1, rowOf(at))];
}

/** The page as shown: the enlarged visualization fills its cover. A window it
 *  covers completely is hidden; the chat, if half covered, shows in its other half. */
export function shown(page: Page, ex: Expanded | null): Page {
  const cover = coverOf(page, ex);
  if (!cover.length) return page;
  const cells = [...page.cells];
  for (const c of cover) cells[c] = ex!.id;
  return { cells };
}

/** `move` for a page with an enlarged visualization. The move follows the
 *  rules above on the page as shown (the enlarged window moves as a whole row
 *  or column), and the windows hidden under it travel with it, so restoring
 *  brings them back next to it. Over the whole page there is nowhere to move. */
export function moveShown(page: Page, ex: Expanded | null, from: Cell, to: Cell): Page {
  const cover = coverOf(page, ex);
  if (!cover.length) return move(page, from, to);
  if (cover.length === CELLS) return page;
  const before = shown(page, ex);
  const after = move(before, from, to);
  if (after === before) return page;
  const target = cellsOf(after, ex!.id); // the new cover, in the same order as `cover`
  const cells = after.cells.map((w) => (w === ex!.id ? null : w));
  cover.forEach((c, i) => {
    const under = page.cells[c];
    if (!under) return;
    // A half-covered chat keeps its hidden half only if that is still the other
    // cell of its column; otherwise it is left with one cell.
    const visible = cells.flatMap((w, cell) => (w === under ? [cell] : []));
    if (visible.every((v) => sibling(v) === target[i])) cells[target[i]] = under;
  });
  return { cells };
}

/** The cell an arrow key leads to from `cell`, or null at the grid's edge. */
export function neighbourCell(cell: Cell, key: string): Cell | null {
  const col = colOf(cell);
  const row = rowOf(cell);
  switch (key) {
    case "ArrowLeft": return col > 0 ? cellAt(col - 1, row) : null;
    case "ArrowRight": return col < 1 ? cellAt(col + 1, row) : null;
    case "ArrowUp": return row > 0 ? cellAt(col, row - 1) : null;
    case "ArrowDown": return row < 1 ? cellAt(col, row + 1) : null;
    default: return null;
  }
}

export const CELL_NAMES = ["arriba a la izquierda", "abajo a la izquierda", "arriba a la derecha", "abajo a la derecha"];
