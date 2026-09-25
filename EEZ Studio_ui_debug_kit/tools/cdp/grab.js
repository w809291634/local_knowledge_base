// grab.js —— 通用 CDP 抓图器（任何 Electron / Chromium / 浏览器 都适用）
//
// 用法:
//   node grab.js --out out.png                              # 截整窗
//   node grab.js --out out.png --canvas                     # 取最大 <canvas> 的原始像素（推荐）
//   node grab.js --out out.png --canvas --click "<视图名>"   # 先用合成事件点开目标，再取
//   node grab.js --out dir/ --click "<A>" --click "<B>"      # 每个目标一张
//   node grab.js --text                                     # 只输出界面文本（排障：抓报错原文）
//
// 端口：--port 或环境变量 CDP_PORT，默认 9222
//
// 关键经验（PLAYBOOK §3.2 / §4.6）：
//   - 画布常常"只在打开了对应视图时才挂载" → 必须先 --click 点开
//   - 合成事件必须 bubbles:true + view:window（React/Vue 靠事件委托才认）
//   - 只有"像素与上一帧不同"才落盘，否则会拿到旧帧
//   - 应用常会在十几秒后自行崩溃 → 尽早执行；一个目标一次会话最稳
const fs = require("fs");
const path = require("path");

function arg(name, def = null) {
  const i = process.argv.indexOf("--" + name);
  if (i < 0) return def;
  const v = process.argv[i + 1];
  return (v && !v.startsWith("--")) ? v : true;
}
function args(name) {
  const out = [];
  process.argv.forEach((a, i) => {
    if (a === "--" + name && process.argv[i + 1] && !process.argv[i + 1].startsWith("--"))
      out.push(process.argv[i + 1]);
  });
  return out;
}

const PORT = arg("port", process.env.CDP_PORT || 9222);
const OUT = arg("out", "grab.png");
const USE_CANVAS = !!arg("canvas", null);
const TEXT_ONLY = !!arg("text", null);
const CLICKS = args("click");
const WAIT_MS = parseInt(arg("wait", "600"), 10);
const TRIES = parseInt(arg("tries", "14"), 10);
const MIN_BYTES = parseInt(arg("min", "2500"), 10);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const JS_CLICK = (name) => `(() => {
  const all = [...document.querySelectorAll('div,span,li,a,button')];
  const hits = all.filter(e => (e.textContent || '').trim() === ${JSON.stringify(name)});
  if (!hits.length) return 'not found: ' + ${JSON.stringify(name)};
  hits.sort((a, b) => b.querySelectorAll('*').length - a.querySelectorAll('*').length);
  const el = hits[0];
  ['mousedown','mouseup','click','dblclick'].forEach(type =>
    el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window,
      detail: type === 'dblclick' ? 2 : 1 })));
  const r = el.getBoundingClientRect();
  return 'clicked @' + Math.round(r.x) + ',' + Math.round(r.y);
})()`;

const JS_CANVASES = `(() => {
  const cs = [...document.querySelectorAll('canvas')];
  return JSON.stringify(cs.map((c, i) => ({ i, w: c.width, h: c.height, d: c.toDataURL('image/png') })));
})()`;

const JS_TEXT = `(() => {
  const errs = [...document.querySelectorAll('*')]
    .filter(e => e.children.length === 0 && /(fail|error|失败|错误|cannot|unable)/i.test(e.textContent || ''))
    .map(e => (e.textContent || '').trim())
    .filter(t => t.length > 8 && t.length < 600);
  return JSON.stringify({ errors: [...new Set(errs)].slice(0, 30),
                          body: (document.body.innerText || '').slice(0, 3000) });
})()`;

async function connect() {
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const pages = list.filter((x) => x.type === "page");
  if (!pages.length) throw new Error("没有可用的 page target（应用是否已崩溃？）");
  const t = pages[0];
  const ws = new WebSocket(t.webSocketDebuggerUrl);
  let id = 0; const pend = new Map();
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data);
    if (m.id && pend.has(m.id)) { pend.get(m.id)(m); pend.delete(m.id); }
  };
  const send = (method, params = {}) => new Promise((r) => {
    const i = ++id; pend.set(i, r);
    ws.send(JSON.stringify({ id: i, method, params }));
  });
  await new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  await send("Page.enable");
  return { ws, send, url: t.url };
}

async function evalJS(send, expr) {
  const r = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
  return r && r.result && r.result.result ? r.result.result.value : undefined;
}

async function grabCanvas(send, outFile, prev) {
  for (let k = 0; k < TRIES; k++) {
    await sleep(WAIT_MS);
    const v = await evalJS(send, JS_CANVASES);
    if (!v) continue;
    const arr = JSON.parse(v);
    if (!arr.length) continue;
    arr.sort((a, b) => b.w * b.h - a.w * a.h);   // 主渲染面通常是最大的画布
    const c = arr[0];
    const data = c.d || "";
    if (!data || data === prev) continue;          // 与上一帧相同 → 还是旧帧，继续等
    const m = /^data:image\/png;base64,(.*)$/.exec(data);
    if (!m) continue;
    const buf = Buffer.from(m[1], "base64");
    if (buf.length < MIN_BYTES) continue;          // 空白帧（单色压缩后极小）
    fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
    fs.writeFileSync(outFile, buf);
    return { file: outFile, w: c.w, h: c.h, bytes: buf.length, data };
  }
  return null;
}

async function main() {
  const { ws, send } = await connect();

  if (TEXT_ONLY) {
    for (const name of (CLICKS.length ? CLICKS : [null])) {
      if (name) console.log("click:", await evalJS(send, JS_CLICK(name)));
      await sleep(1000);
      const v = await evalJS(send, JS_TEXT);
      if (v) {
        const o = JSON.parse(v);
        console.log("=== 界面上的错误文本 ===");
        (o.errors || []).forEach((e) => console.log(" *", e.replace(/\s+/g, " ")));
      }
    }
    ws.close();
    return;
  }

  const targets = CLICKS.length ? CLICKS : [null];
  let prev = null;
  for (const name of targets) {
    if (name) {
      const msg = await evalJS(send, JS_CLICK(name));
      console.log("click :", msg);
      if (String(msg).startsWith("not found")) { prev = null; continue; }
    }
    const multi = targets.length > 1 || OUT.endsWith("/") || OUT.endsWith("\\");
    const outFile = multi ? path.join(OUT, (name || "window") + ".png") : OUT;

    if (USE_CANVAS) {
      const r = await grabCanvas(send, outFile, prev);
      if (r) {
        console.log(`OK    ${name || "canvas"} -> ${r.file} (${r.w}x${r.h}, ${r.bytes}B)`);
        prev = r.data;
      } else {
        console.log(`MISS  ${name || "canvas"}（画布未挂载，或画面未变化）`);
      }
    } else {
      await sleep(WAIT_MS);
      const s = await send("Page.captureScreenshot", { format: "png" });
      const d = s && s.result && s.result.data;
      if (d) {
        fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
        fs.writeFileSync(outFile, Buffer.from(d, "base64"));
        console.log(`OK    ${name || "window"} -> ${outFile}`);
      } else {
        console.log(`MISS  ${name || "window"}（captureScreenshot 失败）`);
      }
    }
    prev = null;
  }
  ws.close();
}

main().catch((e) => { console.error("ERR", e.message); process.exit(1); });
