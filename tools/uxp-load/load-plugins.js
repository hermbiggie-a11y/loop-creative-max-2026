// Load the adb-mcp UXP panels into Photoshop and Premiere via UXP Developer Tool's local service
// (same protocol as Adobe's uxp-devtools-cli, without its native helper). UXP Developer Tool must be running.
//   node load-plugins.js            -> loads ps + pr panels into whichever apps are running
const WebSocket = require("ws");
const path = require("path");

const ADB = path.resolve(__dirname, "..", "adb-mcp", "uxp");
const PLUGINS = { PS: path.join(ADB, "ps"), premierepro: path.join(ADB, "pr"), PPRO: path.join(ADB, "pr") };
const ONLY = process.argv[2]; // optional: "PS" or "premierepro" to load just one
const PORT = process.env.UXP_DEVTOOLS_PORT || 14001;

const ws = new WebSocket(`ws://localhost:${PORT}/socket/cli`);
const clients = [];
const pending = new Map();
let nextId = 0;

function send(clientId, message) {
  return new Promise((resolve, reject) => {
    const requestId = ++nextId;
    pending.set(requestId, { resolve, reject });
    ws.send(JSON.stringify({ command: "proxy", clientId, message, requestId }));
    setTimeout(() => pending.has(requestId) && (pending.delete(requestId), reject(new Error("timeout"))), 20000);
  });
}

ws.on("message", (raw) => {
  const data = JSON.parse(raw.toString());
  if (data.command === "didAddRuntimeClient") clients.push(data);
  if (data.command === "reply" && pending.has(data.requestId)) {
    const cb = pending.get(data.requestId); pending.delete(data.requestId);
    data.error ? cb.reject(new Error(data.error)) : cb.resolve(data);
  }
});
ws.on("error", (e) => { console.error(`Cannot reach UXP Developer Tool service on port ${PORT}: ${e.message}`); process.exit(2); });

ws.on("open", async () => {
  await new Promise((r) => setTimeout(r, 1500)); // let the service announce connected apps
  if (!clients.length) { console.error("No apps connected to UXP Developer Tool. Open Photoshop/Premiere first."); process.exit(3); }
  let failed = 0;
  for (const c of clients) {
    const app = c.app || {};
    console.log(`app: ${app.appName} ${app.appVersion} (id ${app.appId})`);
    const folder = PLUGINS[app.appId];
    if (!folder || (ONLY && ONLY !== app.appId)) continue;
    try {
      const res = await send(c.id, { command: "Plugin", action: "load", params: { provider: { type: "disk", path: folder } }, breakOnStart: false });
      console.log(`  loaded ${path.basename(folder)} -> ${JSON.stringify(res.pluginSessionId || res.data || "ok")}`);
    } catch (e) { failed++; console.error(`  FAILED ${path.basename(folder)}: ${e.message}`); }
  }
  ws.close();
  process.exit(failed ? 1 : 0);
});
