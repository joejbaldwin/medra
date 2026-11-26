/* Generated from docs/contracts/v1.schema.json by `npm run gen:types`. Do not edit. */

export type ServerMessage = HelloMessage | TextMessage | ViewMessage | EndMessage | ErrorMessage;

/**
 * Not a message: a container so every contract lands in one schema.
 */
export interface MedraContracts {
  text_chunk: TextChunk;
  mining_update: MiningUpdate;
  view_update: ViewUpdate;
  server_message: ServerMessage;
  session_config: SessionConfig;
  session_created: SessionCreated;
  sample_info: SampleInfo;
  source_info: SourceInfo;
}
/**
 * A piece of streamed text. Boundaries are arbitrary (may split a word).
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "TextChunk".
 */
export interface TextChunk {
  schema_version: string;
  session_id: string;
  /**
   * Strictly increasing within a session.
   */
  seq: number;
  /**
   * reasoning = chain-of-thought, answer = final answer.
   */
  channel: "reasoning" | "answer" | "meta";
  text: string;
  /**
   * Seconds since session start.
   */
  t: number;
  /**
   * Last chunk of this channel.
   */
  final: boolean;
}
/**
 * Full snapshot of the miner's state after a commit.
 *
 * Emitted each time at least one sentence is committed. It is a snapshot,
 * not a diff: Layer 2 and 3 run in the same process, so this costs no
 * network traffic, and it keeps the "incremental == batch" test simple.
 * Diffing happens in Layer 3, before the network.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "MiningUpdate".
 */
export interface MiningUpdate {
  schema_version: string;
  session_id: string;
  seq: number;
  t: number;
  /**
   * ISO 639-1, e.g. 'en' or 'es'.
   */
  language: string | null;
  /**
   * Reasoning characters received so far.
   */
  text_length: number;
  /**
   * Characters analysed; text after this is pending.
   */
  committed_upto: number;
  final: boolean;
  sentences: Sentence[];
  segments: Segment[];
  terms: Term[];
  tfidf: SegmentKeywords[];
  cooc: Cooccurrence[];
  clusters: Cluster[];
  markers: Marker[];
  stats: Stats;
  /**
   * Decisions for the last tokens committed in this update (not cumulative).
   */
  recent_tokens: TokenDecision[];
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Sentence".
 */
export interface Sentence {
  id: number;
  start: number;
  end: number;
  segment_id: number | null;
  /**
   * Word tokens in the sentence (the timeline's x axis).
   */
  words: number;
}
/**
 * A 'tramo': a run of sentences about one step of the reasoning.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Segment".
 */
export interface Segment {
  id: number;
  start: number;
  end: number;
  /**
   * The boundary may still move; drawn dashed.
   */
  provisional: boolean;
  /**
   * Discourse marker that opened it.
   */
  marker: string | null;
  step_type: string | null;
  boundary_score: number;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Term".
 */
export interface Term {
  /**
   * Lemma or n-gram; the key used by every other field.
   */
  id: string;
  surface_forms: string[];
  count: number;
  /**
   * Number of segments the term appears in.
   */
  df_segments: number;
  spans: [number, number][];
  /**
   * Offset of the first mention.
   */
  first_seen: number;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "SegmentKeywords".
 */
export interface SegmentKeywords {
  segment_id: number;
  /**
   * Top-k by TF-IDF, highest first.
   */
  terms: TermWeight[];
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "TermWeight".
 */
export interface TermWeight {
  term_id: string;
  weight: number;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Cooccurrence".
 */
export interface Cooccurrence {
  a: string;
  b: string;
  count: number;
  pmi: number;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Cluster".
 */
export interface Cluster {
  id: string;
  label_terms: string[];
  term_ids: string[];
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Marker".
 */
export interface Marker {
  /**
   * e.g. backtrack, alternative, verification, conclusion.
   */
  type: string;
  text: string;
  /**
   * @minItems 2
   * @maxItems 2
   */
  span: [number, number];
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Stats".
 */
export interface Stats {
  words: number;
  sentences: number;
  segments: number;
  lexical_diversity: number | null;
  hedges_per_100w: number | null;
  extra: {
    [k: string]: number;
  };
}
/**
 * What the miner did with one token: the 'pipeline working' trace.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "TokenDecision".
 */
export interface TokenDecision {
  form: string;
  lemma: string;
  pos: string;
  /**
   * term = kept; stopword/filler = in a stoplist; pos = word type not kept; number = numeral; other = punctuation-like or too short.
   */
  outcome: "term" | "stopword" | "filler" | "pos" | "number" | "other";
  /**
   * @minItems 2
   * @maxItems 2
   */
  span: [number, number];
}
/**
 * What the screen should show, as a diff against the previous update.
 *
 * The first update of a session has kind="snapshot". After that, each list
 * holds only items that were added or changed (upsert by id), and `removed`
 * lists ids to delete. `timeline` and `stats`, when present, replace the
 * previous value whole. `ticker` items are appended.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "ViewUpdate".
 */
export interface ViewUpdate {
  schema_version: string;
  session_id: string;
  seq: number;
  t: number;
  kind: "snapshot" | "diff";
  committed_upto: number;
  final: boolean;
  nodes: Node[];
  edges: Edge[];
  topics: Topic[];
  paragraphs: Paragraph[];
  highlights: Highlight[];
  timeline: Timeline | null;
  steps: Step[];
  ticker: TickerItem[];
  stats: Stats | null;
  removed: Removed;
}
/**
 * A bubble in the concept map. The browser runs the physics.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Node".
 */
export interface Node {
  id: string;
  label: string;
  count: number;
  radius: number;
  topic_id: string | null;
  /**
   * Index into the dashboard's categorical palette.
   */
  colour_slot: number;
  /**
   * Starting position in a 0..1 box; the force layout moves it.
   */
  seed_xy: [number, number] | null;
  /**
   * 0..1, e.g. recently mentioned.
   */
  emphasis: number;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Edge".
 */
export interface Edge {
  id: string;
  a: string;
  b: string;
  width: number;
  colour_slot: number;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Topic".
 */
export interface Topic {
  id: string;
  name: string;
  colour_slot: number;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Paragraph".
 */
export interface Paragraph {
  segment_id: number;
  start: number;
  end: number;
  topic_id: string | null;
  /**
   * Segment keywords (top TF-IDF terms); the dashboard adds 'Tramo n'.
   */
  label: string;
  provisional: boolean;
}
/**
 * Spans to underline when a node or topic is selected.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Highlight".
 */
export interface Highlight {
  kind: "node" | "topic";
  id: string;
  spans: [number, number][];
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Timeline".
 */
export interface Timeline {
  x_axis: "words";
  x_max: number;
  series: TimelineSeries[];
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "TimelineSeries".
 */
export interface TimelineSeries {
  topic_id: string;
  points: [number, number][];
}
/**
 * One node of the step graph: a segment, with how it was opened.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Step".
 */
export interface Step {
  segment_id: number;
  step_type: string | null;
  topic_id: string | null;
  /**
   * Earlier segments whose topic this step returns to ('retoma').
   */
  arcs_back_to: number[];
  /**
   * Discourse marker that opened the step.
   */
  marker: string | null;
  marker_span: [number, number] | null;
  words: number;
}
/**
 * One entry of the 'pipeline working' strip: form -> lemma -> outcome.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "TickerItem".
 */
export interface TickerItem {
  form: string;
  lemma: string;
  /**
   * A TokenDecision outcome code; the dashboard words it.
   */
  outcome: string;
  pos: string | null;
  /**
   * The bubble this token feeds, if any.
   */
  node_id: string | null;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "Removed".
 */
export interface Removed {
  nodes: string[];
  edges: string[];
  topics: string[];
  paragraphs: number[];
  /**
   * 'kind:id' keys.
   */
  highlights: string[];
  steps: number[];
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "HelloMessage".
 */
export interface HelloMessage {
  type: "hello";
  schema_version: string;
  session_id: string;
  source: string;
  title: string | null;
  prompt: string | null;
  language: string | null;
}
/**
 * Raw text, passed straight through so the stream feels live.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "TextMessage".
 */
export interface TextMessage {
  type: "text";
  chunk: TextChunk;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "ViewMessage".
 */
export interface ViewMessage {
  type: "view";
  view: ViewUpdate;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "EndMessage".
 */
export interface EndMessage {
  type: "end";
  reason: "completed" | "cancelled" | "error";
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "ErrorMessage".
 */
export interface ErrorMessage {
  type: "error";
  message: string;
}
/**
 * Body of POST /sessions.
 *
 * replay needs `sample`, paste needs `text`, deepseek needs `prompt`. words_per_second, chunking and seed only apply to replay and paste
 * (a live model sets its own pace).
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "SessionConfig".
 */
export interface SessionConfig {
  source: "replay" | "paste" | "deepseek";
  /**
   * Sample trace id, as listed by GET /datasets.
   */
  sample: string | null;
  /**
   * Pasted reasoning text.
   */
  text: string | null;
  /**
   * Question for a live model.
   */
  prompt: string | null;
  /**
   * 0 = as fast as possible.
   */
  words_per_second: number;
  chunking: "word" | "random";
  seed: number;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "SessionCreated".
 */
export interface SessionCreated {
  session_id: string;
}
/**
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "SampleInfo".
 */
export interface SampleInfo {
  id: string;
  title: string;
  language: string;
  words: number;
  origin: string;
  /**
   * The task the trace answers (empty if unknown).
   */
  prompt: string;
}
/**
 * One entry of GET /sources: what the dashboard can offer.
 *
 * This interface was referenced by `MedraContracts`'s JSON-Schema
 * via the `definition` "SourceInfo".
 */
export interface SourceInfo {
  id: "replay" | "paste" | "deepseek";
  label: string;
  available: boolean;
  /**
   * Why it is unavailable, or a warning to show.
   */
  note: string | null;
  /**
   * Starting a session needs an access code (deployed backend).
   */
  needs_code: boolean;
}
