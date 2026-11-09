// Run the browser editor in headless Chromium and check it compiles (SPEC M7).
//
//   python web/build.py --pyodide <Pyodide 0.27.7 dir> --paper <paper-core.js>
//   node web/browser_test.mjs [out-dir]
//
// Serves web/ on a free local port, opens index.html with the local Pyodide and
// Paper.js, waits for the first compile, then switches master, italic, face and a
// parameter, saving a screenshot of each state. Exits 1 if any step reports an error.
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

try {
  await step("sans_regular");
  await step("sans_bold", () => page.selectOption("#master", "700"));
  await step("sans_bold_italic", () => page.check("#italic"));
  await step("display", () => page.selectOption("#face", "display"));
  await step("display_text_opsz9", () => page.selectOption("#master", "9"));
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
process.exit(results.some(([, s]) => !s.includes("compiled")) ? 1 : 0);
