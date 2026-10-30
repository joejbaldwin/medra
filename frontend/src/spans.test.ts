import { describe, expect, it } from "vitest";
import { marksIn, splitByMarks, type Mark } from "./spans";

describe("splitByMarks", () => {
  it("covers the range exactly, in order", () => {
    const pieces = splitByMarks(0, 20, [{ start: 5, end: 9, id: "a" }]);
    expect(pieces.map((p) => [p.start, p.end, p.ids])).toEqual([
      [0, 5, []],
      [5, 9, ["a"]],
      [9, 20, []],
    ]);
  });

  it("handles overlapping marks (two n-grams sharing a word)", () => {
    // "arithmetic series formula": [0,17) arithmetic series, [11,25) series formula
    const marks: Mark[] = [
      { start: 0, end: 17, id: "arithmetic series" },
      { start: 11, end: 25, id: "series formula" },
    ];
    const pieces = splitByMarks(0, 25, marks);
    expect(pieces.map((p) => [p.start, p.end, p.ids])).toEqual([
      [0, 11, ["arithmetic series"]],
      [11, 17, ["arithmetic series", "series formula"]], // longest mark first
      [17, 25, ["series formula"]],
    ]);
  });

  it("clips marks to the range", () => {
    const pieces = splitByMarks(10, 20, [{ start: 5, end: 12, id: "a" }]);
    expect(pieces[0]).toEqual({ start: 10, end: 12, ids: ["a"] });
    expect(pieces.at(-1)!.end).toBe(20);
  });
});

describe("marksIn", () => {
  const sorted: Mark[] = [
    { start: 0, end: 4, id: "a" },
    { start: 10, end: 30, id: "long" },
    { start: 12, end: 15, id: "b" },
    { start: 40, end: 44, id: "c" },
  ];

  it("finds marks overlapping a range, including ones that start before it", () => {
    expect(marksIn(sorted, 20, 41).map((m) => m.id)).toEqual(["long", "c"]);
    expect(marksIn(sorted, 0, 5).map((m) => m.id)).toEqual(["a"]);
    expect(marksIn(sorted, 31, 39)).toEqual([]);
  });
});
