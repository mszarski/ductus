// Run the browser editor in headless Chromium and check it compiles (SPEC M7).
//
//   python web/build.py --pyodide <Pyodide 0.27.7 dir> --paper <paper-core.js>
//   node web/browser_test.mjs [out-dir]
//
// Serves web/ on a free local port, opens index.html with the local Pyodide and
// Paper.js, waits for the first compile, then checks that each master's sliders show
// and edit that master's own values, drags a stroke point and an outline point in the
// glyph view, and switches italic and face, saving a screenshot of each state. Exits 1
// if any step reports an error or a check fails.
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
  const o = st.overrides["n.arch.shoulder"];
  check(o && o.dx > 0 && o.dy > 0, `dragging right and up gave a +x +y override (${JSON.stringify(o)})`);
  check((await page.getAttribute("#glyphsvg path.outline", "d")) !== outline0, "the n's outline followed the point");
  await page.fill("#glyphchar", "e");
  await page.waitForSelector('#glyphsvg rect[data-name="e.bar.bl"]');
  await step("drag_e_bar", () => drag('#glyphsvg rect[data-name="e.bar.bl"]', 0, 12));
  st = await appState();
  const ob = st.overrides["e.bar.bl"];
  check(ob && ob.stage === "outline" && ob.dy < 0, `an outline point dragged down (${JSON.stringify(ob)})`);
  await step("sans_bold_italic", async () => { await page.selectOption("#master", "700"); await page.check("#italic"); });
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
