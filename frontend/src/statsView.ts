// The «Estadísticas» popup: the text-mining figures of the current trace, as
// the miner and presenter reported them (no new computation here, only counts
// over the view state). Numbers are written out; bars only help compare them.
import type { TickerItem } from "./contracts";
import type { ViewState } from "./state";
import { stepTypeEs } from "./stepGraph";
import { esc } from "./util";

const fmt = (n: number, digits = 0) => n.toLocaleString("es", { minimumFractionDigits: digits, maximumFractionDigits: digits });

const POS_ES: Record<string, string> = {
  VERB: "verbo", AUX: "auxiliar", ADV: "adverbio", ADP: "preposición", DET: "determinante",
  PRON: "pronombre", CCONJ: "conjunción", SCONJ: "conjunción", INTJ: "interjección", PART: "partícula",
};

/** What the miner did with one token, in Spanish («contraseña» → concepto). */
export function tickerLine(item: TickerItem, state: ViewState): string {
  const via = item.lemma !== item.form.toLowerCase() ? ` → ${esc(item.lemma)}` : "";
  let outcome: string;
  switch (item.outcome) {
    case "term": {
      const node = item.node_id ? state.nodes.get(item.node_id) : undefined;
      outcome = node ? `<em>concepto «${esc(node.label)}»</em>` : "término";
      break;
    }
    case "stopword": outcome = "descartada (stopword)"; break;
    case "filler": outcome = "descartada (relleno)"; break;
    case "pos": outcome = `descartada (${esc(POS_ES[item.pos ?? ""] ?? item.pos ?? "categoría")})`; break;
    case "number": outcome = "descartada (número)"; break;
    default: outcome = "descartada";
  }
  return `«${esc(item.form)}»${via} → ${outcome}`;
}

interface Row {
  label: string;
  value: number;
  shown: string;
  slot?: number; // a topic's colour; the accent when absent
}

function bars(rows: Row[]): string {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return rows
    .map(
      (r) =>
        `<div class="bar-row" title="${esc(r.label)}: ${esc(r.shown)}"><span class="bar-label">${esc(r.label)}</span>` +
        `<span class="bar-track"><span class="bar" style="width:${(100 * r.value) / max}%;${r.slot === undefined ? "" : ` --c: var(--c${r.slot % 6})`}"></span></span>` +
        `<span class="bar-value">${esc(r.shown)}</span></div>`,
    )
    .join("");
}

function tile(label: string, value: string, note = ""): string {
  return `<div class="tile"><span class="tile-label">${label}</span><span class="tile-value">${value}</span>${note ? `<span class="tile-note">${note}</span>` : ""}</div>`;
}

export function statsHtml(state: ViewState, text: string): string {
  const stats = state.stats;
  const ticker = state.ticker
    .slice(-6)
    .reverse()
    .map((t) => `<div>${tickerLine(t, state)}</div>`)
    .join("");
  const tickerBlock = `<section class="st-section st-ticker"><h3>Procesando ahora</h3><div class="ticker">${ticker || "<div>Esperando texto…</div>"}</div></section>`;
  if (!stats) return `<p class="stats-empty">Todavía no hay análisis: elige una fuente y envía para empezar.</p>${tickerBlock}`;

  const analysed = text.length ? Math.min(1, state.committedUpto / text.length) : 0;
  const tiles = [
    tile("Palabras", fmt(stats.words)),
    tile("Oraciones", fmt(stats.sentences)),
    tile("Tramos", fmt(stats.segments)),
    tile("Temas", fmt(state.topics.size)),
    tile("Conceptos", fmt(state.nodes.size), "en el mapa"),
    tile("Coocurrencias", fmt(state.edges.size), "enlaces en el mapa"),
    tile("Diversidad léxica", stats.lexical_diversity != null ? fmt(stats.lexical_diversity, 2) : "—", "vocabulario / palabras"),
    tile("Dudas", stats.hedges_per_100w != null ? fmt(stats.hedges_per_100w, 1) : "—", "por 100 palabras"),
  ].join("");

  const byType = new Map<string, number>();
  for (const s of state.orderedSteps()) {
    const t = stepTypeEs(s.step_type);
    byType.set(t, (byType.get(t) ?? 0) + 1);
  }
  const steps = [...byType].sort((a, b) => b[1] - a[1]).map(([t, n]) => ({ label: t, value: n, shown: fmt(n) }));

  const top = [...state.nodes.values()]
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label))
    .slice(0, 8)
    .map((n) => ({ label: n.label, value: n.count, shown: fmt(n.count), slot: n.colour_slot }));

  const paragraphs = state.orderedParagraphs();
  const topics = state
    .orderedTopics()
    .map((t) => {
      const concepts = [...state.nodes.values()].filter((n) => n.topic_id === t.id).length;
      const tramos = paragraphs.flatMap((p, i) => (p.topic_id === t.id ? [i + 1] : []));
      return (
        `<li style="--c: var(--c${t.colour_slot % 6})"><span class="dot"></span><b>${esc(t.name)}</b>` +
        `<span>${concepts} ${concepts === 1 ? "concepto" : "conceptos"}${tramos.length ? ` · ${tramos.length === 1 ? "tramo" : "tramos"} ${tramos.join(", ")}` : ""}</span></li>`
      );
    })
    .join("");

  const langs = Object.entries(stats.extra)
    .filter(([k]) => k.startsWith("share_"))
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => ({ label: k.slice(6), value: v, shown: `${fmt(100 * v)} %` }));

  return (
    `<div class="analysed"><span>Texto analizado: <b>${fmt(state.committedUpto)}</b> de ${fmt(text.length)} caracteres</span>` +
    `<span class="bar-track"><span class="bar" style="width:${100 * analysed}%"></span></span></div>` +
    `<div class="tiles">${tiles}</div>` +
    `<div class="st-grid">` +
    `<section class="st-section"><h3>Conceptos más mencionados</h3>${top.length ? bars(top) : `<p class="muted">Aún ninguno.</p>`}</section>` +
    `<section class="st-section"><h3>Pasos por tipo</h3>${steps.length ? bars(steps) : `<p class="muted">Aún ninguno.</p>`}` +
    `<h3>Idioma</h3>${langs.length ? bars(langs) : `<p class="muted">—</p>`}</section>` +
    `<section class="st-section"><h3>Temas</h3>${topics ? `<ul class="st-topics">${topics}</ul>` : `<p class="muted">Aparecen cuando hay términos repetidos.</p>`}</section>` +
    tickerBlock +
    `</div>`
  );
}
