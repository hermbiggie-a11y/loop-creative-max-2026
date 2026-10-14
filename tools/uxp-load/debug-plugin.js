// Attach to a loaded UXP plugin via UXP Developer Tool's debug channel (Chrome DevTools Protocol)
// and evaluate an expression inside it. Prints recent console output too.
//   node debug-plugin.js <appId> <pluginSessionId> "<js expression>"
const WebSocket = require("ws");
const [appId, sessionId, expr = "1+1"] = process.argv.slice(2);

const svc = new WebSocket("ws://localhost:14001/socket/cli");
let nextId = 0;
const pending = new Map();
const clients = [];
svc.on("message", (raw) => {
  const d = JSON.parse(raw.toString());
  if (d.command === "didAddRuntimeClient") clients.push(d);
  if (d.command === "reply" && pending.has(d.requestId)) { pending.get(d.requestId)(d); pending.delete(d.requestId); }
});
const ask = (clientId, message) => new Promise((res) => {
  const requestId = ++nextId; pending.set(requestId, res);
  svc.send(JSON.stringify({ command: "proxy", clientId, message, requestId }));
});

svc.on("open", async () => {
  await new Promise((r) => setTimeout(r, 1500));
  const c = clients.find((x) => x.app && x.app.appId === appId);
  if (!c) { console.error("app not connected:", appId); process.exit(2); }
  const r = await ask(c.id, { command: "Plugin", action: "debug", pluginSessionId: sessionId });
  const raw = r.wsdebugUrl || (r.data && r.data.wsdebugUrl);
  if (r.error || !raw) { console.error("debug failed:", JSON.stringify(r)); process.exit(3); }
  const url = raw.startsWith("ws=") ? `ws://${raw.slice(3)}` : raw;
  console.log("cdp:", url);
  const cdp = new WebSocket(url);
  let id = 0;
  const call = (method, params = {}) => new Promise((res) => {
    const mid = ++id;
    const h = (raw) => { const m = JSON.parse(raw.toString()); if (m.id === mid) { cdp.off("message", h); res(m); } };
    cdp.on("message", h);
    cdp.send(JSON.stringify({ id: mid, method, params }));
  });
  const contexts = [];
  cdp.on("message", (raw) => {
    const m = JSON.parse(raw.toString());
    if (m.method === "Runtime.executionContextCreated") contexts.push(m.params.context.id);
    if (m.method === "Runtime.consoleAPICalled") console.log(`[console.${m.params.type}]`, m.params.args.map((a) => a.value ?? a.description).join(" "));
    if (m.method === "Runtime.exceptionThrown") console.log("[exception]", JSON.stringify(m.params.exceptionDetails).slice(0, 500));
  });
  cdp.on("open", async () => {
    await call("Runtime.enable");
    await new Promise((r) => setTimeout(r, 500));
    const params = { expression: expr, awaitPromise: true, returnByValue: true };
    if (contexts.length) params.contextId = contexts[0];
    const out = await call("Runtime.evaluate", params);
    console.log("result:", JSON.stringify(out.result || out).slice(0, 2000));
    setTimeout(() => process.exit(0), 4000);
  });
  cdp.on("error", (e) => { console.error("cdp error", e.message); process.exit(4); });
});
