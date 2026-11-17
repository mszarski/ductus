// The compiler for the browser editor, off the page's thread (SPEC M7).
//
// index.html starts this as a Web Worker with ?pyodide=<base url>&paper=<paper-core.js>
// &build=<_build/ url>. It loads Paper.js and Pyodide, installs the ductus wheel and the
// example faces, and imports web/driver.py. Then each message {id, fn, args} calls
// driver.<fn>(*args) and answers {id, result} or {id, error}; messages run one at a time,
// in order. While starting it posts {status} lines for the page.
const q = new URLSearchParams(location.search);
const PYODIDE = q.get("pyodide"), PAPER = q.get("paper"), BUILD = q.get("build");
const say = (status) => postMessage({ status });

async function start() {
  importScripts(PAPER);               // Paper.js runs headless here (no window, no document)
  importScripts(PYODIDE + "pyodide.js");
  const py = await loadPyodide({ indexURL: PYODIDE });
  say("Loading packages…");
  await py.loadPackage(["numpy", "pyyaml", "fonttools", "micropip"]);
  const micropip = py.pyimport("micropip");
  const manifest = await (await fetch(BUILD + "manifest.json")).json();
  // the ductus wheel without its native dependencies (skia-pathops, typer): Paper.js does the booleans
  await micropip.install.callKwargs(BUILD + manifest.wheel, { deps: false });
  const zip = await (await fetch(BUILD + "examples.zip")).arrayBuffer();
  py.unpackArchive(zip, "zip", { extractDir: "/home/pyodide/examples" });
  py.FS.writeFile("/home/pyodide/driver.py", await (await fetch(BUILD + "driver.py")).text());
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide'); import driver");
  return py.pyimport("driver");
}
const ready = start();
ready.then(() => say("ready"), (e) => say("Failed to start: " + e.message));

// the calls, chained so they run in the order sent
let chain = Promise.resolve();
self.onmessage = (e) => {
  const { id, fn, args } = e.data;
  chain = chain.then(async () => {
    try {
      const driver = await ready;
      if (fn === "build") {
        const res = driver.build(...args);
        const [bytes, ms, n] = res.toJs();
        res.destroy();
        const buf = new Uint8Array(bytes);
        postMessage({ id, result: { bytes: buf, ms, n } }, [buf.buffer]);
      } else {
        postMessage({ id, result: driver[fn](...args) });
      }
    } catch (err) {
      postMessage({ id, error: String(err && err.message || err) });
    }
  });
};
