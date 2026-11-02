import { describe, expect, it } from "vitest";
import { chatExpanded, emptyPage, firstPage, move, neighbourCell, place, remove, setChatExpanded, setSpan, spanOf, type Page } from "./layout";

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
});
