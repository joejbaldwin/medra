import { describe, expect, it } from "vitest";
import {
  chatExpanded,
  coverOf,
  emptyPage,
  firstPage,
  move,
  moveShown,
  neighbourCell,
  place,
  remove,
  setChatExpanded,
  setSpan,
  shown,
  spanOf,
  type Expanded,
  type Page,
} from "./layout";

const p = (...cells: Page["cells"]): Page => ({ cells });

/** Every window on the page, with how many cells it fills. */
function inventory(page: Page): Record<string, number> {
  const out: Record<string, number> = {};
  for (const w of page.cells) if (w) out[w] = (out[w] ?? 0) + 1;
  return out;
}

describe("layout", () => {
  it("starts with the chat open and nothing else", () => {
    expect(firstPage().cells).toEqual([null, null, "chat", "chat"]);
    expect(chatExpanded(firstPage())).toBe(true);
    expect(emptyPage().cells.every((c) => c === null)).toBe(true);
  });

  it("moves into an empty cell and swaps occupied ones", () => {
    expect(move(p("map", null, "steps", "timeline"), 0, 1).cells).toEqual([null, "map", "steps", "timeline"]);
    expect(move(p("map", null, "steps", "timeline"), 0, 3).cells).toEqual(["timeline", null, "steps", "map"]);
  });

  it("moves an expanded chat as a whole column", () => {
    const moved = move(p("map", "timeline", "chat", "chat"), 3, 0);
    expect(moved.cells).toEqual(["chat", "chat", "map", "timeline"]);
  });

  it("swaps a window dropped on the expanded chat without losing its neighbour", () => {
    const start = p("map", "timeline", "chat", "chat");
    const moved = move(start, 1, 2); // timeline dropped on the chat's upper half
    expect(moved.cells).toEqual(["chat", "chat", "timeline", "map"]);
    expect(inventory(moved)).toEqual(inventory(start));
  });

  it("ignores moves within the chat's own column and from empty cells", () => {
    const start = p("map", null, "chat", "chat");
    expect(move(start, 2, 3)).toBe(start);
    expect(move(start, 1, 0)).toBe(start);
  });

  it("treats a collapsed chat like any other window", () => {
    expect(move(p("map", "timeline", null, "chat"), 3, 0).cells).toEqual(["chat", "timeline", null, "map"]);
  });

  it("collapses the chat to its lower cell and expands it back", () => {
    const collapsed = setChatExpanded(firstPage(), false)!;
    expect(collapsed.cells).toEqual([null, null, null, "chat"]);
    expect(setChatExpanded(collapsed, true)!.cells).toEqual(firstPage().cells);
  });

  it("moves a covered window to a free cell when the chat expands", () => {
    const page = setChatExpanded(p(null, "timeline", "map", "chat"), true)!;
    expect(page.cells).toEqual(["map", "timeline", "chat", "chat"]);
  });

  it("refuses to expand when no cell is free", () => {
    expect(setChatExpanded(p("steps", "timeline", "map", "chat"), true)).toBeNull();
  });

  it("places, moves and removes visualizations", () => {
    const placed = place(p(null, "timeline", "chat", "chat"), 0, "map");
    expect(placed.cells).toEqual(["map", "timeline", "chat", "chat"]);
    expect(place(p("map", "timeline", "steps", null), 3, "map").cells).toEqual([null, "timeline", "steps", "map"]);
    expect(remove(placed, "timeline").cells).toEqual(["map", null, "chat", "chat"]);
  });

  it("finds neighbouring cells for arrow keys", () => {
    expect(neighbourCell(0, "ArrowRight")).toBe(2);
    expect(neighbourCell(0, "ArrowDown")).toBe(1);
    expect(neighbourCell(0, "ArrowLeft")).toBeNull();
    expect(neighbourCell(3, "ArrowUp")).toBe(2);
  });

  it("lets a visualization fill its column or its row", () => {
    const column = setSpan(p("map", null, "steps", "timeline"), "map", "column")!;
    expect(column.cells).toEqual(["map", "map", "steps", "timeline"]);
    expect(spanOf(column, "map")).toBe("column");
    const row = setSpan(p("map", null, "steps", "timeline"), "map", "row")!;
    // "steps" was in the cell to the right: it moves to the free cell.
    expect(row.cells).toEqual(["map", "steps", "map", "timeline"]);
    expect(spanOf(row, "map")).toBe("row");
  });

  it("shrinks a visualization back to its first cell", () => {
    expect(setSpan(p("map", "map", "steps", null), "map", "cell")!.cells).toEqual(["map", null, "steps", null]);
    expect(setSpan(p(null, "timeline", null, "timeline"), "timeline", "cell")!.cells).toEqual([null, "timeline", null, null]);
  });

  it("switches a span from column to row in one step", () => {
    expect(setSpan(p("map", "map", null, "steps"), "map", "row")!.cells).toEqual(["map", null, "map", "steps"]);
  });

  it("refuses a span that would cover a two-cell window or has no room", () => {
    expect(setSpan(p(null, "timeline", "chat", "chat"), "timeline", "row")).toBeNull(); // the chat fills the right column
    expect(setSpan(p("map", "timeline", "steps", "chat"), "map", "column")).toBeNull(); // page full
  });

  it("moves a row-filling window as a whole row", () => {
    expect(move(p("timeline", "map", "timeline", "chat"), 0, 1).cells).toEqual(["map", "timeline", "chat", "timeline"]);
  });

  it("swaps a window dropped on a row-filling window, keeping its neighbour", () => {
    const start = p("timeline", "map", "timeline", "chat");
    const moved = move(start, 3, 0); // chat dropped on the left half of the timeline
    expect(moved.cells).toEqual(["chat", "timeline", "map", "timeline"]);
    expect(inventory(moved)).toEqual(inventory(start));
  });

  describe("enlarged visualization", () => {
    const full = p("map", "timeline", "steps", "chat");
    const ex = (id: Expanded["id"], mode: Expanded["mode"]): Expanded => ({ id, mode });

    it("covers its row, its column or the whole page, whatever is there", () => {
      expect(coverOf(full, ex("timeline", "row"))).toEqual([1, 3]);
      expect(coverOf(full, ex("steps", "column"))).toEqual([2, 3]);
      expect(coverOf(full, ex("map", "full"))).toEqual([0, 1, 2, 3]);
      expect(coverOf(full, null)).toEqual([]);
      expect(coverOf(p(null, null, "chat", "chat"), ex("map", "full"))).toEqual([]); // not on the page
    });

    it("is drawn over the page without changing it", () => {
      expect(shown(full, ex("timeline", "row")).cells).toEqual(["map", "timeline", "steps", "timeline"]);
      expect(shown(full, ex("map", "full")).cells).toEqual(["map", "map", "map", "map"]);
      // Over two-cell windows too.
      const chat = p("map", "timeline", "chat", "chat");
      expect(shown(chat, ex("map", "row")).cells).toEqual(["map", "timeline", "map", "chat"]); // chat keeps its lower half
      expect(shown(chat, ex("map", "column")).cells).toEqual(["map", "map", "chat", "chat"]);
      expect(full.cells).toEqual(["map", "timeline", "steps", "chat"]);
    });

    it("moves as a whole column, taking the hidden window along", () => {
      const page = p("map", "timeline", "chat", "chat");
      const moved = moveShown(page, ex("map", "column"), 0, 2);
      expect(moved.cells).toEqual(["chat", "chat", "map", "timeline"]);
      expect(inventory(moved)).toEqual(inventory(page));
    });

    it("moves as a whole row; a half-covered chat stays a column", () => {
      const page = p("map", "timeline", "chat", "chat");
      const moved = moveShown(page, ex("map", "row"), 0, 1);
      expect(moved.cells).toEqual(["timeline", "map", "chat", "chat"]);
      expect(shown(moved, ex("map", "row")).cells).toEqual(["timeline", "map", "chat", "map"]);
    });

    it("trades places with a window dropped on it, which lands where it was dropped", () => {
      const page = p("map", "timeline", "steps", "chat");
      const moved = moveShown(page, ex("map", "column"), 2, 1); // steps dropped on the lower half
      expect(moved.cells).toEqual(["chat", "steps", "map", "timeline"]);
      expect(inventory(moved)).toEqual(inventory(page));
    });

    it("moves the other windows as usual", () => {
      const page = p("map", "timeline", "steps", null);
      expect(moveShown(page, ex("map", "column"), 2, 3).cells).toEqual(["map", "timeline", null, "steps"]);
      expect(moveShown(page, null, 0, 3).cells).toEqual(move(page, 0, 3).cells);
    });

    it("cannot move over the whole page", () => {
      expect(moveShown(full, ex("map", "full"), 0, 3)).toBe(full);
    });
  });
});
