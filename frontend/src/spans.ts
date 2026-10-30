// Splitting text into pieces by the marks (mention spans) that cover them.
// Marks can overlap: "arithmetic series" and "series formula" share "series",
// so a piece carries every mark id that covers it. Discourse markers ("Wait,")
// are marks too, flagged separately: they are shown, but are not bubbles.

export interface Mark {
  start: number;
  end: number;
  id: string;
  marker?: boolean;
}

export interface Piece {
  start: number;
  end: number;
  ids: string[]; // bubble marks covering the whole piece, longest mark first
  marker: boolean; // inside a discourse marker
}

/** Pieces covering [start, end) in order; boundaries wherever a mark starts or ends. */
export function splitByMarks(start: number, end: number, marks: Mark[]): Piece[] {
  const inside = marks
    .filter((m) => m.end > start && m.start < end)
    .map((m) => ({ ...m, start: Math.max(m.start, start), end: Math.min(m.end, end) }));
  const cuts = new Set([start, end]);
  for (const m of inside) {
    cuts.add(m.start);
    cuts.add(m.end);
  }
  const points = [...cuts].sort((a, b) => a - b);
  const pieces: Piece[] = [];
  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i];
    const b = points[i + 1];
    const covering = inside.filter((m) => m.start <= a && m.end >= b);
    const bubbles = covering.filter((m) => !m.marker);
    bubbles.sort((x, y) => y.end - y.start - (x.end - x.start) || x.id.localeCompare(y.id));
    pieces.push({ start: a, end: b, ids: bubbles.map((m) => m.id), marker: covering.some((m) => m.marker) });
  }
  return pieces;
}

/** Marks overlapping [start, end), from a list sorted by start. */
export function marksIn(sorted: Mark[], start: number, end: number): Mark[] {
  // Binary search for the first mark that starts at or after `start`, then look
  // back a few marks for ones that start earlier but still reach into the range
  // (marks are at most a few words long, so a short window is enough).
  const LOOK_BACK = 8;
  let lo = 0;
  let hi = sorted.length;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (sorted[mid].start < start) lo = mid + 1;
    else hi = mid;
  }
  const out: Mark[] = [];
  for (let i = Math.max(0, lo - LOOK_BACK); i < sorted.length && sorted[i].start < end; i++) {
    if (sorted[i].end > start) out.push(sorted[i]);
  }
  return out;
}
