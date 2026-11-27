import { describe, expect, it } from "vitest";
import type { Node, ViewUpdate } from "./contracts";
import { layoutLabel } from "./conceptMap";
import { ViewState } from "./state";

const node = (id: string, count: number): Node => ({
  id, label: id, count, radius: 20 + count, topic_id: null, colour_slot: 0, seed_xy: null,
});

function view(kind: "snapshot" | "diff", partial: Partial<ViewUpdate>): ViewUpdate {
  return {
    schema_version: "1.2", session_id: "s", seq: 0, t: 0, kind, committed_upto: 0, final: false,
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

  it("keeps topics, steps and the timeline, and orders them for display", () => {
    const s = new ViewState();
    const step = (segment_id: number, topic_id: string | null) => ({
      segment_id, step_type: null, topic_id, arcs_back_to: [], marker: null, marker_span: null, words: 10,
    });
    const timeline = { x_axis: "words" as const, x_max: 20, series: [] };
    s.apply(view("snapshot", {
      topics: [{ id: "t1", name: "b", colour_slot: 1 }, { id: "t0", name: "a", colour_slot: 0 }],
      steps: [step(1, "t1"), step(0, "t0")],
      timeline,
    }));
    expect(s.orderedTopics().map((t) => t.id)).toEqual(["t0", "t1"]); // palette order
    expect(s.orderedSteps().map((x) => x.segment_id)).toEqual([0, 1]);
    expect(s.slotOf("t1")).toBe(1);
    expect(s.slotOf(null)).toBe(5);
    expect(s.slotOf("gone")).toBe(5);
    // A diff without a timeline keeps the previous one; removals apply.
    s.apply(view("diff", { removed: { nodes: [], edges: [], topics: ["t1"], paragraphs: [], highlights: [], steps: [1] } }));
    expect(s.timeline).toEqual(timeline);
    expect([...s.topics.keys()]).toEqual(["t0"]);
    expect([...s.steps.keys()]).toEqual([0]);
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
