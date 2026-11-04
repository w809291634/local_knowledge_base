// h5_probe.js —— 纯 HTML 评审页的无头验证通道（Edge/Chromium headless + CDP）
//
// 用法：
//   bash tools/cdp/h5_edge.sh tmp/prof file:///path/page.html      # 先起无头浏览器
//   node tools/cdp/h5_probe.js --body tmp/check.js --out tmp/shot.png
//   node tools/cdp/h5_probe.js --stay --click 273,580 --body tmp/after.js
//
// --body 文件里写一个 async 箭头函数，返回值 JSON 打印到 stdout：
//   async () => { await new Promise(r=>setTimeout(r,300)); return JSON.stringify({w:innerWidth}); }
//
// 为什么需要它（2026-11-04 w78 实测，PR-0442）：
//   - Desktop 内嵌 Browser 没开可见窗口时视口是 0x0，几何断言全量歪；
//   - element.dispatchEvent 绕过浏览器命中测试，会造出「点了能跳」的假通过；
//     本工具的 --click 走 CDP Input.dispatchMouseEvent，是真坐标真命中。
//   - 同 URL 再 navigate 只算文档内跳转，页面状态不清零；要干净状态就别用 --stay。
//
// 依赖：Node ≥21（全局 fetch / WebSocket），无第三方包。
const fs = require('fs');

function arg(n, d = null) {
  const i = process.argv.indexOf('--' + n);
  if (i < 0) return d;
  const v = process.argv[i + 1];
  return (v && !v.startsWith('--')) ? v : true;
}
function all(n) {
  const out = [];
  process.argv.forEach((a, i) => { if (a === '--' + n && process.argv[i + 1]) out.push(process.argv[i + 1]); });
  return out;
}

const PORT = Number(arg('port', process.env.CDP_PORT || 9333));
const URLV = arg('url', null);
const BODY = arg('body', null);
const OUT = arg('out', null);
const STAY = process.argv.includes('--stay');
const HOVERS = all('hover');
const CLICKS = all('click');

async function pickTarget() {
  const list = await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json();
  const pages = list.filter(p => p.type === 'page' && p.webSocketDebuggerUrl);
  const MATCH = arg('match', null);
  // Edge 会自己多开 edge://sync-confirmation/ 之类的页面 target，拿第一个就验到空页
  const t = (MATCH && pages.find(p => p.url.includes(MATCH)))
    || pages.find(p => !/^(edge|chrome|devtools):/.test(p.url))
    || pages[0];
  if (!t) throw new Error('没找到页面 target（浏览器没起？先跑 h5_edge.sh）');
  return t;
}

async function main() {
  const tgt = await pickTarget();
  if (tgt.url.startsWith('edge://')) console.error('!! 只有内置页 target，页面可能没加载：' + tgt.url);

  const ws = new WebSocket(tgt.webSocketDebuggerUrl);
  let id = 0;
  const pending = {};
  const fails = [];
  const send = (m, p) => new Promise(res => { const k = ++id; pending[k] = res; ws.send(JSON.stringify({ id: k, method: m, params: p || {} })); });
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.id && pending[d.id]) { pending[d.id](d); delete pending[d.id]; }
    else if (d.method === 'Network.loadingFailed') fails.push((d.params.errorText || '') + '|' + (d.params.type || ''));
    else if (d.error) console.error('CDP 错误', JSON.stringify(d.error).slice(0, 200));
  };
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  await send('Page.enable'); await send('Network.enable'); await send('Runtime.enable');

  if (!STAY) {
    if (!URLV) throw new Error('首次运行要带 --url（或用 --stay 复用当前页面）');
    // 加时间戳防缓存；注意同 URL 不带时间戳时只是文档内跳转，页面状态不会清零
    const bust = URLV.includes('?') ? URLV : URLV + '?v=' + Date.now();
    await send('Page.navigate', { url: bust });
    await new Promise(r => setTimeout(r, Number(arg('wait', 1700))));
  }

  async function mouse(type, x, y) {
    const p = { type, x, y };
    if (type !== 'mouseMoved') { p.button = 'left'; p.clickCount = 1; p.buttons = type === 'mousePressed' ? 1 : 0; }
    await send('Input.dispatchMouseEvent', p);
  }
  for (const c of HOVERS) {
    const [x, y] = c.split(',').map(Number);
    await mouse('mouseMoved', x, y);
    await new Promise(r => setTimeout(r, 200));
  }
  for (const c of CLICKS) {
    const [x, y] = c.split(',').map(Number);
    await mouse('mouseMoved', x, y);
    await mouse('mousePressed', x, y);
    await new Promise(r => setTimeout(r, 80));
    await mouse('mouseReleased', x, y);
    await new Promise(r => setTimeout(r, Number(arg('after-click', 700))));
  }

  if (BODY) {
    const src = fs.readFileSync(BODY, 'utf-8');
    const o = await send('Runtime.evaluate', { expression: '(' + src + ')()', awaitPromise: true, returnByValue: true });
    if (o.result && o.result.exceptionDetails) {
      console.error('[页面异常]', JSON.stringify(o.result.exceptionDetails).slice(0, 500));
      process.exitCode = 1;
    } else {
      const v = o.result.result.value;
      console.log(typeof v === 'string' ? v : JSON.stringify(v, null, 1));
    }
  }
  if (OUT) {
    const clip = arg('clip', null);
    const p = { format: 'png' };
    if (clip) { const [x, y, w, h] = clip.split(',').map(Number); Object.assign(p, { clip: { x, y, width: w, height: h, scale: 1 } }); }
    const sh = await send('Page.captureScreenshot', p);
    fs.writeFileSync(OUT, Buffer.from(sh.result.data, 'base64'));
    console.error('[截图] ' + OUT);
  }
  console.error('[网络失败请求] ' + fails.length + (fails.length ? ' → ' + fails.slice(0, 3).join(' , ') : ''));
  ws.close();
}

main().catch(e => { console.error('!! ' + e.message); process.exit(2); });
