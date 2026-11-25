import { describe, expect, it } from "vitest";
import { blocksFor, DESIGNS, designFor, KNIGHTS, PETS, stepsFor, susScore, TASKS } from "./studyPlan";

describe("counterbalancing", () => {
  const designs = Object.values(DESIGNS);

  it("balances condition order and the trace shown in MeDRA over P1-P6", () => {
    expect(designs).toHaveLength(6);
    expect(designs.filter((d) => d.first === "medra")).toHaveLength(3);
    expect(designs.filter((d) => d.medraTrace === PETS)).toHaveLength(3);
  });

  it("covers all four combinations in P1-P4", () => {
    const combos = new Set(["P1", "P2", "P3", "P4"].map((p) => `${DESIGNS[p].first}-${DESIGNS[p].medraTrace}`));
    expect(combos.size).toBe(4);
  });

  it("gives each participant both traces and both conditions", () => {
    for (const d of designs) {
      const [a, b] = blocksFor(d);
      expect(new Set([a.trace, b.trace])).toEqual(new Set([PETS, KNIGHTS]));
      expect(new Set([a.condition, b.condition])).toEqual(new Set(["medra", "texto"]));
      expect(a.condition).toBe(d.first);
    }
  });

  it("treats unknown codes as test runs", () => {
    expect(designFor("P4")).toEqual({ design: DESIGNS.P4, test: false });
    expect(designFor("prueba").test).toBe(true);
  });
});

describe("steps", () => {
  it("puts the practice right before the MeDRA block", () => {
    for (const p of ["P1", "P2"]) {
      const blocks = blocksFor(DESIGNS[p]);
      const steps = stepsFor(blocks);
      const practice = steps.findIndex((s) => s.kind === "practice");
      const medraBlock = blocks.findIndex((b) => b.condition === "medra");
      expect(steps[practice + 1]).toEqual({ kind: "blockIntro", block: medraBlock });
    }
  });

  it("asks every task and one SUS per block", () => {
    const steps = stepsFor(blocksFor(DESIGNS.P1));
    expect(steps.filter((s) => s.kind === "task")).toHaveLength(2 * TASKS.length);
    expect(steps.filter((s) => s.kind === "sus")).toHaveLength(2);
    expect(steps.at(-1)).toEqual({ kind: "submit" });
  });
});

describe("SUS", () => {
  it("scores the standard way", () => {
    expect(susScore([5, 1, 5, 1, 5, 1, 5, 1, 5, 1])).toBe(100);
    expect(susScore([1, 5, 1, 5, 1, 5, 1, 5, 1, 5])).toBe(0);
    expect(susScore([3, 3, 3, 3, 3, 3, 3, 3, 3, 3])).toBe(50);
    // Brooke (1996) worked example style: odd 4 -> 3, even 2 -> 3, so all 3s -> 75.
    expect(susScore([4, 2, 4, 2, 4, 2, 4, 2, 4, 2])).toBe(75);
  });

  it("waits for all ten answers", () => {
    expect(susScore([5, 1, 5, 1, 5, 1, 5, 1, 5, null])).toBeNull();
    expect(susScore([5, 1])).toBeNull();
  });
});
