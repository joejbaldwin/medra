import { describe, expect, it } from "vitest";
import type { Node, ViewUpdate } from "./contracts";
import { layoutLabel } from "./conceptMap";
import { ViewState } from "./state";

const node = (id: string, count: number): Node => ({
  id, label: id, count, radius: 20 + count, topic_id: null, colour_slot: 0, seed_xy: null, emphasis: 0,
});

function view(kind: "snapshot" | "diff", partial: Partial<ViewUpdate>): ViewUpdate {
  return {
    schema_version: "1.1", session_id: "s", seq: 0, t: 0, kind, committed_upto: 0, final: false,
    nodes: [], edges: [], topics: [], paragraphs: [], highlights: [], timeline: null, steps: [], ticker: [],
    stats: null, removed: { nodes: [], edges: [], topics: [], paragraphs: [], highlights: [], steps: [] },
    ...partial,
  };
}

describe("ViewState", () => {
  it("applies upserts and removals, and a snapshot starts over", () => {
    const s = new ViewState();
    s.apply(view("snapshot", { nodes: [node("a", 1), node("b", 1)] }));
    s.apply(view("diff", {
      nodes: [node("a", 2)],
      edges: [{ id: "a|c", a: "a", b: "c", width: 2, colour_slot: 0 }],
      removed: { nodes: ["b"], edges: [], topics: [], paragraphs: [], highlights: [], steps: [] },
    }));
    expect([...s.nodes.keys()]).toEqual(["a"]);
    expect(s.nodes.get("a")!.count).toBe(2);
    expect(s.neighbours("a")).toEqual(new Set(["c"]));
    s.apply(view("snapshot", { nodes: [node("z", 1)] }));
    expect([...s.nodes.keys()]).toEqual(["z"]);
    expect(s.edges.size).toBe(0);
  });

  it("keeps highlights by kind and id", () => {
    const s = new ViewState();
    s.apply(view("snapshot", { highlights: [{ kind: "node", id: "a", spans: [[0, 3]] }] }));
    expect(s.nodeSpans("a")).toEqual([[0, 3]]);
    expect(s.nodeSpans("missing")).toEqual([]);
  });
});

describe("layoutLabel", () => {
  it("keeps a short label on one line", () => {
    expect(layoutLabel("login", 60).lines).toEqual(["login"]);
  });

  it("wraps a long n-gram onto two lines instead of truncating", () => {
    const { lines } = layoutLabel("arithmetic series", 36);
    expect(lines).toEqual(["arithmetic", "series"]);
  });

  it("truncates a single long word only as a last resort", () => {
    const { lines } = layoutLabel("supercalifragilistic", 22);
    expect(lines[0].endsWith("…")).toBe(true);
  });
});
