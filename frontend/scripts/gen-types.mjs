// Generate src/contracts.ts from the backend's JSON Schema (docs/contracts/).
// json-schema-to-typescript does not read draft 2020-12 tuples (prefixItems),
// so they are rewritten to the older `items: [...]` form first.
import { readFileSync, writeFileSync } from "node:fs";
import { compile } from "json-schema-to-typescript";

const SCHEMA = new URL("../../docs/contracts/v1.schema.json", import.meta.url);
const OUT = new URL("../src/contracts.ts", import.meta.url);

function rewriteTuples(node) {
  if (Array.isArray(node)) return node.forEach(rewriteTuples);
  if (node === null || typeof node !== "object") return;
  if (node.prefixItems) {
    node.items = node.prefixItems;
    delete node.prefixItems;
  }
  Object.values(node).forEach(rewriteTuples);
}

const schema = JSON.parse(readFileSync(SCHEMA, "utf8"));
rewriteTuples(schema);
const ts = await compile(schema, "MedraContracts", {
  bannerComment: "/* Generated from docs/contracts/v1.schema.json by `npm run gen:types`. Do not edit. */",
  unreachableDefinitions: true,
  additionalProperties: false,
});
writeFileSync(OUT, ts);
console.log(`wrote ${OUT.pathname}`);
