// Run the browser editor in headless Chromium and check it compiles (SPEC M7).
//
//   python web/build.py --pyodide <Pyodide 0.27.7 dir> --paper <paper-core.js>
//   node web/browser_test.mjs [out-dir]
//
// Serves web/ on a free local port, opens index.html with the local Pyodide and
// Paper.js, waits for the first compile, then checks that each master's sliders show
// and edit that master's own values; in the glyph view drags a stroke point, an outline
// point and a parameter handle, moves a point at one master only, edits a node's width,
// drags in the italic view; reloads the page (the edits are kept), exports the files;
// switches face. Saves a screenshot of each state. Exits 1 if any step reports an error
// or a check fails.
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = process.argv[2] || path.join(HERE, "_build", "shots");
fs.mkdirSync(OUT, { recursive: true });
const TYPES = { ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".wasm": "application/wasm",
                ".json": "application/json", ".zip": "application/zip", ".whl": "application/zip", ".py": "text/plain" };

const server = http.createServer((req, res) => {
  const p = path.join(HERE, decodeURIComponent(new URL(req.url, "http://x").pathname));
  if (!p.startsWith(HERE) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); res.end(); return; }
  res.writeHead(200, { "Content-Type": TYPES[path.extname(p)] || "application/octet-stream" });
  fs.createReadStream(p).pipe(res);
});
await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
const url = `http://127.0.0.1:${server.address().port}/index.html?pyodide=_build/pyodide/&paper=_build/paper-core.js`;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
const errors = [];
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(url);

const results = [];
let last = "";
async function step(label, action) {
  if (action) await action();
  await page.waitForFunction((prev) => {
    const s = document.getElementById("status").textContent;
    return s !== prev && (s.includes("compiled") || s.startsWith("Error") || s.startsWith("Failed"));
  }, last, { timeout: 300000 });
  last = await page.textContent("#status");
  await page.screenshot({ path: path.join(OUT, `${label}.png`) });
  results.push([label, last]);
  console.log(`${label}: ${last}`);
}

const failures = [];
const check = (ok, what) => { console.log(`  ${ok ? "ok" : "FAILED"}: ${what}`); if (!ok) failures.push(what); };
async function drag(selector, dx, dy) {
  const box = await page.locator(selector).boundingBox();
  const x = box.x + box.width / 2, y = box.y + box.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + dx / 2, y + dy / 2);
  await page.mouse.move(x + dx, y + dy);
  await page.mouse.up();
}
const appState = () => page.evaluate(() => window.ductusState());

try {
  await step("sans_regular");
  check((await page.textContent("#v_stem")) === "84", "Regular stem slider shows 84");
  // the sliders show the selected master's own values
  await step("sans_bold", () => page.selectOption("#master", "700"));
  const boldStem = +(await page.textContent("#v_stem"));
  check(boldStem > 140, `Bold stem slider shows the Bold's value (${boldStem})`);
  await step("sans_bold_stem", () => page.$eval("#params input[data-p=stem]", (el) => { el.value = 160; el.dispatchEvent(new Event("input")); }));
  let st = await appState();
  check(st.state["700"] && st.state["700"].stem === 160 && !st.state["400"], `the change is stored for the Bold only (${JSON.stringify(st.state)})`);
  await step("sans_regular_again", () => page.selectOption("#master", "400"));
  check((await page.textContent("#v_stem")) === "84", "Regular stem is still 84");
  // drag a stroke point of the n, then an outline point of the e
  const outline0 = await page.getAttribute("#glyphsvg path.outline", "d");
  await step("drag_n_shoulder", () => drag('#glyphsvg circle[data-name="n.arch.shoulder"]', 25, -15));
  st = await appState();
  const o = st.overrides.all["n.arch.shoulder"];
  check(o && o.dx > 0 && o.dy > 0, `dragging right and up gave a +x +y override (${JSON.stringify(o)})`);
  check((await page.getAttribute("#glyphsvg path.outline", "d")) !== outline0, "the n's outline followed the point");
  await page.fill("#glyphchar", "e");
  await page.waitForSelector('#glyphsvg rect[data-name="e.bar.bl"]');
  await step("drag_e_bar", () => drag('#glyphsvg rect[data-name="e.bar.bl"]', 0, 12));
  st = await appState();
  const ob = st.overrides.all["e.bar.bl"];
  check(ob && ob.stage === "outline" && ob.dy < 0, `an outline point dragged down (${JSON.stringify(ob)})`);
  // a parameter handle of the n: the join height, for this glyph only
  await page.fill("#glyphchar", "n");
  await page.waitForSelector('#glyphsvg path.phandle[data-param="n_join_at"]');
  await step("drag_n_join_handle", () => drag('#glyphsvg path.phandle[data-param="n_join_at"]', 0, -40));
  st = await appState();
  const oh = st.overrides.all["n.@n_join_at"];
  check(oh && oh.dv && Math.abs(oh.dv) > 0.01, `a handle drag wrote a per-glyph parameter delta (${JSON.stringify(oh)})`);
  // a node's stroke width (click selects it)
  await page.click('#glyphsvg circle[data-name="n.arch.shoulder"]');
  await page.waitForSelector('#nodectl input[data-k="dw"]');
  await step("n_shoulder_width", async () => { await page.fill('#nodectl input[data-k="dw"]', "14"); await page.dispatchEvent('#nodectl input[data-k="dw"]', "change"); });
  st = await appState();
  check(st.overrides.all["n.arch.shoulder"].dw === 14, `the width control wrote dw (${JSON.stringify(st.overrides.all["n.arch.shoulder"])})`);
  // a move at the Bold only
  await step("bold_again", () => page.selectOption("#master", "700"));
  await page.selectOption("#scope", "master");
  await step("bold_only_move", () => drag('#glyphsvg circle[data-name="n.arch.shoulder"]', -20, 0));
  st = await appState();
  const om = (st.overrides.masters["700"] || {})["n.arch.shoulder"];
  check(om && om.dx < 0 && st.overrides.all["n.arch.shoulder"].dx > 0, `the move went to the Bold's own (${JSON.stringify(st.overrides.masters)})`);
  await page.selectOption("#scope", "all");
  // the italic view: the construction slanted; a horizontal drag stores a horizontal upright move
  await step("bold_italic_view", () => page.check("#italic"));
  check((await page.textContent("#glyphname")).includes("italic"), "the glyph view shows the italic");
  await page.fill("#glyphchar", "l");
  await page.waitForSelector("#glyphsvg circle.node");
  const lnode = await page.getAttribute("#glyphsvg circle.node", "data-name");
  await step("italic_drag", () => drag(`#glyphsvg circle[data-name="${lnode}"]`, 30, 0));
  st = await appState();
  const oi = st.overrides.all[lnode];
  check(oi && oi.dx > 0 && Math.abs(oi.dy || 0) <= 1, `an italic drag stored the upright move (${JSON.stringify(oi)})`);
  // the edits survive a reload
  const before = JSON.stringify(await appState());
  last = "";
  await step("reloaded", () => page.reload());
  check(JSON.stringify(await appState()) === before, "the edits were restored after a reload");
  await page.click("#export");
  const files = await page.$$eval("#exports a", (as) => as.map((a) => a.textContent));
  check(files.includes("overrides.yaml") && files.includes("overrides_700.yaml") && files.includes("params_700.json"),
        `export offers the face's files (${files.join(", ")})`);
  await step("display", () => page.selectOption("#face", "display"));
  await step("display_text_opsz9", () => page.selectOption("#master", "9"));
  check(+(await page.textContent("#v_hairline")) > 45, "the text master's hairline slider shows its heavier hairline");
  await step("display_stem120", async () => {
    await page.fill("#filter", "stem");
    await page.$eval("#params input[data-p=stem]", (el) => { el.value = 120; el.dispatchEvent(new Event("input")); });
  });
} catch (e) {
  console.log("step failed:", e.message.split("\n")[0], "| status:", await page.textContent("#status"));
  results.push(["timeout", "Error"]);
}
await browser.close();
server.close();
for (const e of errors) console.log("console error:", e);
process.exit(results.some(([, s]) => !s.includes("compiled")) || failures.length ? 1 : 0);
