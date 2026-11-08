# -*- coding: utf-8 -*-
"""出两张交付物：
  1) designer_simple/00_page_map.svg  —— 分层方框图（一级/房间/详情/工具页）
  2) prototype/index.html            —— 可点原型：点界面控件直接跳页

两者都只消费 pages.PAGES + nav_map.NAV_TARGETS，不重画界面。
"""
import io
import json
import os

import simple_control as sc
import pages as pg
import nav_map as nm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "design", "flow_state.json")


def read_state(argv):
    """全览确认状态：未确认 => H5 只出全览核对态，不出热区与控件图。"""
    ok = False
    if os.path.exists(STATE):
        ok = bool(json.load(io.open(STATE, encoding="utf-8"))
                  .get("overview_confirmed", False))
    if "--tree-only" in argv:
        ok = False
    if "--confirmed" in argv:
        ok = True
    return ok


OUT = sc.OUT
PROTO = os.path.join(ROOT, "prototype")

LEVELS = [
    ("一级 · 主控", ["主控"], "根页面，所有二级页都从这里进"),
    ("二级 · 房间页（同一模板）", list(sc.ROOM_ORDER),
     "入口：主控 2×2 房间卡 ×4；返回：‹ 主控"),
    ("三级 · 设备详情（按设备分 6 种）",
     ["灯详情", "空调详情", "窗帘详情", "传感详情", "插座详情", "摄像头详情"],
     "入口：房间设备格「详情」×18 / 全部设备行 / 通知「查看」×3；返回：‹ 上一房间页"),
    ("二级 · 工具页（11 屏）",
     ["通知中心", "能源统计", "设置", "全部设备", "安防", "场景详情",
      "添加设备·选类型", "添加设备·配网中", "添加设备·完成", "关于", "离线态"],
     "入口：主控顶部 4 入口 + 安防 pill；页内互跳：设置→关于、全部设备→添加 ×3"),
]


def page_data():
    data = {}
    for (title, svg, entry, exit_, rows) in pg.PAGES:
        items = []
        for i, (name, cat, act, behav, box) in enumerate(rows, start=1):
            target = nm.NAV_TARGETS.get((title, name), "")
            items.append({"n": i, "name": name, "cat": cat, "act": act,
                          "behav": behav, "box": list(box), "target": target})
        data[title] = {"svg": svg, "entry": entry, "exit": exit_, "rows": items}
    return data



def edges_of(data):
    """[(源页, 控件名, 目标页)]，只取会换页的控件。"""
    return [(pg, r["name"], r["target"])
            for pg, d in data.items() for r in d["rows"]
            if r["target"] and r["cat"] != "back"]


def build_tree_svg(data):
    """全览树：顶层=主控，逐层=可被调用的页；实线=跳转(标控件名)，虚线=返回，方框=只下发硬件不连线。"""
    import collections
    import simple_control as sc

    order = [t for (t, _f, _e, _x, _r) in pg.PAGES]
    es = edges_of(data)
    out_edges = collections.defaultdict(list)
    parents = collections.defaultdict(list)
    for a, n, b in es:
        out_edges[a].append((n, b))
        parents[b].append((a, n))

    depth = {"主控": 0}
    dq = collections.deque(["主控"])
    while dq:
        cur = dq.popleft()
        for _n, nxt in out_edges[cur]:
            if nxt not in depth:
                depth[nxt] = depth[cur] + 1
                dq.append(nxt)
    for t in order:
        depth.setdefault(t, max(depth.values()) + 1)

    NW0, GAPX, TOP, M = 240, 22, 120, 40      # 节点宽 240 = 800 的 0.3 倍
    rows = collections.defaultdict(list)
    for t in order:
        rows[depth[t]].append(t)

    maxn = max(len(v) for v in rows.values())
    NW = NW0
    TS = NW / 800.0                    # 缩略比例：节点宽 / 设计稿宽
    TH = int(480 * TS)                 # 缩略图高
    NH = TH + 54                       # 节点卡高 = 缩略图 + 文字区
    ROWH = NH + 118                    # 行距留出箭头与标签空间
    W = max(1560, M * 2 + maxn * (NW + GAPX) - GAPX)

    def place(names):
        span = len(names) * NW + (len(names) - 1) * GAPX
        x0 = (W - span) / 2
        return {n: x0 + i * (NW + GAPX) for i, n in enumerate(names)}

    pos, px = {}, {}
    for dv in sorted(rows):
        names = rows[dv]
        if dv == 0:
            names.sort(key=order.index)
        else:
            def key(nm):
                xs = [px[a] for (a, _n) in parents[nm] if a in px]
                return (min(xs) if xs else W, order.index(nm))
            names.sort(key=key)
        px = place(names)
        for nm in names:
            pos[nm] = (px[nm], TOP + dv * ROWH)

    def jump_marks(d, x, y, ts):
        """缩略图上给会触发跳转的控件打序号点（放大后同样位置有箭头）。"""
        out = []
        for r in d["rows"]:
            if not r["target"]:
                continue
            bx, by, bw, bh = r["box"]
            cx, cy = x + bx * ts + 5, y + by * ts + 5
            out.append(f'<circle cx="{cx}" cy="{cy}" r="6" fill="{sc.ACCENT}" '
                       f'stroke="{sc.BG}" stroke-width="1"/>'
                       f'<text x="{cx}" y="{cy + 2.6}" font-size="7.5" fill="{sc.BG}" '
                       f'font-weight="700" text-anchor="middle">{r["n"]}</text>')
        return "".join(out)

    def chip(x, y, w, h, txt, color):
        return (sc.r(x, y, w, h, "none", color, 6) +
                sc.t(x + w / 2, y + h / 2 + 3.5, txt, 8.5, color, "600", "middle"))

    parts, labels = [], []
    for child in order:
        ps = parents.get(child, [])
        if len(ps) > 3:
            cx0, cy0 = pos[child]
            names = "、".join(n for (_a, n) in ps)
            labels.append(
                f'<g><title>{child} 的入口：{names}</title>' +
                sc.t(cx0 + NW * 0.3, cy0 - 12, f"入口 ×{len(ps)}", 10,
                    sc.ACCENT, "700", "middle") + '</g>')
        for i, (a, n) in enumerate(ps):
            if depth[a] >= depth[child] and a != "主控":
                pass                                  # 同层/回指也照画，走同一通道
            ax, ay = pos[a]
            cx, cy = pos[child]
            sx, sy = ax + NW * 0.3, ay + NH
            ex, ey = cx + NW * 0.3, cy
            parts.append(
                f'<path d="M{sx},{sy} C{sx},{sy + 60} {ex},{ey - 60} {ex},{ey - 6}" '
                f'fill="none" stroke="{sc.ACCENT}" stroke-width="1.25" '
                f'marker-end="url(#tarr)"/>')
            if len(ps) <= 3:
                off = (i - (len(ps) - 1) / 2) * 22
                yy = cy - 14 - (i % 2) * 13
                labels.append(sc.t(ex + off, yy, n, 10, sc.ACCENT, "600",
                                   "middle"))
        bk = [r["target"] for r in data[child]["rows"] if r["cat"] == "back"]
        if bk and bk[0] in pos:
            cx, cy = pos[child]
            ax, ay = pos[bk[0]]
            parts.append(
                f'<path d="M{cx + NW * 0.72},{cy} C{cx + NW * 0.72},{cy - 44} '
                f'{ax + NW * 0.72},{ay + NH + 44} {ax + NW * 0.72},{ay + NH + 6}" '
                f'fill="none" stroke="{sc.TEAL}" stroke-width="1.1" '
                f'stroke-dasharray="5 4" marker-end="url(#tarr2)"/>')

    for name, (x, y) in pos.items():
        d = data[name]
        n_hw = sum(1 for r in d["rows"] if r["behav"] == "下发硬件")
        n_ro = sum(1 for r in d["rows"] if r["behav"] == "只刷新")
        n_nav = sum(1 for r in d["rows"] if r["target"])
        root = name == "主控"
        orphan = not parents.get(name) and not root
        border = sc.ACCENT if root else (sc.RED if orphan else sc.GREEN)
        ty0 = y + NH - 50
        parts.append(
            f'<g class="tnode" data-page="{name}" style="cursor:pointer">' +
            sc.r(x, y, NW, NH, "#0A0F18", border, 10) +
            f'<g transform="translate({x},{y}) scale({TS:.4f})">{d["svg"]}</g>' +
            sc.r(x, y, NW, TH, "none", "#273140", 6) + jump_marks(d, x, y, TS) +
            sc.t(x + 10, ty0 + 14, name, 13, sc.T1, "700") +
            sc.t(x + NW - 10, ty0 + 14, f"L{depth[name]}", 10, sc.T3, "400", "end") +
            sc.t(x + 10, ty0 + 32, f"{len(d['rows'])} 控件 · {n_nav} 跳转", 9.5, sc.T2) +
            (chip(x + 112, ty0 + 22, 52, 18, f"硬 {n_hw}", sc.GREEN) if n_hw else "") +
            (chip(x + 172, ty0 + 22, 52, 18, f"读 {n_ro}", sc.T3) if n_ro else "") +
            (sc.t(x + NW / 2, y + NH + 13, "无入口（状态页）", 8, sc.RED, "400",
                  "middle") if orphan else "") +
            '</g>')

    legend = (sc.t(M, 40, "全览树：顶层=主页，逐层=可被调用的页", 14, sc.T1, "700") +
              sc.t(M, 60, "节点内嵌真实设计图（800x480 缩略）；"
                          "实线箭头 = 点该控件跳到下一页（名字标在子节点上方）；"
                          "青色虚线 = 返回；绿框标签 = 只下发硬件、不跳页（不画线）；"
                          "缩略图上的橙色序号点 = 会触发跳转的控件，悬停可看带箭头的全尺寸图",
              9.5, sc.T2))
    H = TOP + (max(rows) + 1) * ROWH + 40
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
            f'viewBox="0 0 {W} {H}" font-family="Microsoft YaHei,Noto Sans SC,'
            f'PingFang SC,sans-serif">' + sc.r(0, 0, W, H, sc.BG, "none", 0) +
            legend + "".join(parts) + "".join(labels) +
            '<defs><marker id="tarr" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#F2B45C"/></marker>'
            '<marker id="tarr2" viewBox="0 0 10 10" refX="9" refY="5" '
            'markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
            '<path d="M0,0 L10,5 L0,10 z" fill="#5FD3C6"/></marker></defs></svg>')

def build_prototype(data, confirmed):
    os.makedirs(PROTO, exist_ok=True)
    levels = [{"name": n, "pages": ps} for n, ps, _d in LEVELS]
    payload = {"pages": data, "levels": levels, "confirmed": confirmed}
    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>Haven Home 可点原型</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#05080f;color:#f4f7fb;font:13px "Microsoft YaHei",system-ui,sans-serif}
header{display:flex;align-items:center;gap:14px;padding:10px 16px;border-bottom:1px solid #273140}
h1{font-size:15px;margin:0}
.crumb{color:#75859c;font-size:12px}
button{font:12px inherit;color:#f4f7fb;background:#1c2430;border:1px solid #273140;
  border-radius:8px;padding:5px 10px;cursor:pointer}
button:hover{background:#273140}
button.primary{background:#f2b45c;color:#05080f;border-color:#f2b45c;font-weight:700}
button.tog.on{border-color:#5fd3a6;color:#5fd3a6}
main{display:grid;grid-template-columns:196px 812px 1fr;gap:14px;padding:14px 16px}
nav{display:flex;flex-direction:column;gap:12px}
nav h2{font-size:11px;color:#75859c;margin:6px 0 4px;font-weight:600}
nav .pg{display:block;width:100%;text-align:left;margin:2px 0;padding:5px 8px}
nav .pg.on{border-color:#f2b45c;color:#f2b45c}
#stage{position:relative;width:800px;height:480px;background:#05080f;
  border:1px solid #273140;border-radius:10px;overflow:hidden}
#stage svg{display:block;width:800px;height:480px}
.hot{position:absolute;border-radius:6px;cursor:pointer;background:transparent;
  border:1px solid transparent;transition:background .12s,border-color .12s}
.hot:hover{background:rgba(242,180,92,.14);border-color:#f2b45c}
.hot.flash{background:rgba(242,180,92,.35);border-color:#f2b45c}
.hot.act:active{background:rgba(95,211,166,.3);border-color:#5fd3a6}
aside{min-width:330px}
aside h2{font-size:12px;margin:0 0 6px;color:#75859c}
table{border-collapse:collapse;width:100%}
td{padding:3px 6px;border-bottom:1px solid #111925;font-size:11px;vertical-align:top}
tr.nav td{color:#f2b45c;cursor:pointer}
tr.nav:hover td{background:#151b24}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
.legend{margin-top:10px;color:#75859c;font-size:11px;line-height:1.7}
.legend b{color:#b9c4d4}
#hint{margin-left:auto;color:#5fd3a6;font-size:12px}
#peek{display:none;position:fixed;z-index:20;pointer-events:none;border:1px solid #f2b45c;
  border-radius:10px;background:#05080f;box-shadow:0 8px 30px rgba(0,0,0,.6);
  transform-origin:top left}
#peek .cap{color:#f2b45c;font-size:12px;padding:4px 8px}
</style></head><body>
<header>
  <h1>Haven Home · 可点原型</h1>
  <span class="crumb" id="crumb">主控</span>
  <button id="back">‹ 返回</button>
  <button class="primary" id="home">回主控</button>
  <button id="treebtn" class="tog">全览</button>
  <span id="hint">黄色框 = 有跳转，点一下进页</span>
</header>
<main id="work">
  <nav id="nav"></nav>
  <div>
    <div id="stage"></div>
    <div class="legend" id="legend"></div>
  </div>
  <aside><h2 id="ptitle">控件</h2><table id="tbl"></table></aside>
</main>
<div id="treeview" style="display:none;padding:0 16px 16px;overflow:auto"></div>
<div id="peek"></div>
<script id="data" type="application/json">__DATA__</script>
<script id="tree" type="image/svg+xml">__TREE__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const CAT = {nav:'#f2b45c',back:'#5fd3c6',scene:'#c08cff',toggle:'#5fd3a6',
             slider:'#7fb3ff',read:'#75859c'};
const CATN = {nav:'跳转',back:'返回',scene:'场景',toggle:'开关',slider:'滑条',read:'只读'};
const BEH = {换页:'#f2b45c','下发硬件':'#5fd3a6','只刷新':'#75859c'};
let cur = '主控', stack = [];

function navList(){
  const n = document.getElementById('nav');
  n.innerHTML = '';
  D.levels.forEach(l=>{
    const h = document.createElement('h2'); h.textContent = l.name; n.appendChild(h);
    l.pages.forEach(p=>{
      const b = document.createElement('button');
      b.className = 'pg' + (p===cur?' on':'');
      b.textContent = p;
      b.onclick = ()=>go(p);
      n.appendChild(b);
    });
  });
}

function go(page, push=true){
  if(!D.pages[page]) return;
  if(push && page!==cur) stack.push(cur);
  cur = page;
  render();
}

function back(){
  const p = stack.pop();
  if(p) go(p, false);
}

function render(){
  const d = D.pages[cur];
  document.getElementById('crumb').textContent = cur;
  document.getElementById('stage').innerHTML =
    '<svg viewBox="0 0 800 480" width="800" height="480">' + d.svg + '</svg>';
  const stage = document.getElementById('stage');
  d.rows.forEach(r=>{
    if(!r.target || !D.confirmed) return;
    const h = document.createElement('div');
    h.className = 'hot';
    h.style.left = r.box[0]+'px'; h.style.top = r.box[1]+'px';
    h.style.width = r.box[2]+'px'; h.style.height = r.box[3]+'px';
    h.title = r.name + ' → ' + r.target;
    h.onclick = ()=>go(r.target);
    stage.appendChild(h);
  });
  const tbl = document.getElementById('tbl');
  document.getElementById('ptitle').textContent = cur + ' · ' + d.rows.length + ' 个控件' +
    (D.confirmed ? '（AI 预估控件图，待你改口径）' : '');
  document.getElementById('hint').textContent = D.confirmed
    ? '黄色框 = 有跳转，点一下进页'
    : '全览核对态：点节点可看单页；确认分层与跳转后才会生成页面连接与控件图';
  tbl.innerHTML = '';
  if (!D.confirmed){
    tbl.innerHTML = '<tr><td>全览尚未确认：控件图与页面连接未生成。先在「全览」核对分层与跳转，确认后我再出。</td></tr>';
    navList(); return;
  }
  d.rows.forEach(r=>{
    const tr = document.createElement('tr');
    tr.className = r.target ? 'nav' : '';
    tr.innerHTML = '<td>'+r.n+'</td>' +
      '<td><span class="dot" style="background:'+CAT[r.cat]+'"></span>'+r.name+'</td>' +
      '<td>'+CATN[r.cat]+'</td><td>'+r.act+'</td>' +
      '<td style="color:'+BEH[r.behav]+'">'+r.behav+'</td>';
    tr.onclick = ()=>{ if(r.target) go(r.target); };
    tbl.appendChild(tr);
  });
  document.getElementById('legend').innerHTML =
    '<b>入口</b> ' + d.entry.replace(/^入口：/, '') + '　|　<b>出口</b> ' +
    d.exit.replace(/^出口：/, '') +
    '<br>' + Object.keys(CAT).map(k=>'<span class="dot" style="background:'+
      CAT[k]+'"></span>'+CATN[k]).join('　');
  navList();
}

const peek = document.getElementById('peek');
let peekK = 1;
function peekSvg(page){
  const d = D.pages[page];
  let s = '<svg viewBox="0 0 800 480" width="800" height="480">' + d.svg +
    '<defs><marker id="pk" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"' +
    ' markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"' +
    ' fill="#F2B45C"/></marker></defs>';
  d.rows.filter(r=>r.target).forEach(r=>{
    const b = r.box, bx=b[0], by=b[1], bw=b[2], bh=b[3];
    s += '<rect x="'+bx+'" y="'+by+'" width="'+bw+'" height="'+bh+
         '" fill="none" stroke="#F2B45C" stroke-width="2.5" rx="7"/>';
    s += '<circle cx="'+(bx+2)+'" cy="'+(by+2)+'" r="12" fill="#F2B45C"/>' +
         '<text x="'+(bx+2)+'" y="'+(by+6)+'" font-size="12" font-weight="700"' +
         ' fill="#05080F" text-anchor="middle">'+r.n+'</text>';
    const dir = (bx + bw + 190 < 800) ? 1 : -1;
    const sx = dir > 0 ? bx + bw : bx, ty = by + bh / 2;
    const tx = sx + dir * 46;
    s += '<path d="M'+sx+','+ty+' h'+(dir*42)+'" stroke="#F2B45C" stroke-width="2.5"' +
         ' marker-end="url(#pk)"/>';
    const label = '\u2192 ' + r.target, w = label.length * 13 + 16;
    const lx = dir > 0 ? tx + 4 : tx - w - 4;
    s += '<rect x="'+lx+'" y="'+(ty-13)+'" width="'+w+'" height="26" rx="13"' +
         ' fill="#F2B45C"/>' +
         '<text x="'+(lx+w/2)+'" y="'+(ty+5)+'" font-size="12" font-weight="700"' +
         ' fill="#05080F" text-anchor="middle">'+label+'</text>';
  });
  return s + '</svg>';
}
function bindPeek(t){
  t.querySelectorAll('.tnode').forEach(g=>{
    const page = g.getAttribute('data-page');
    g.addEventListener('mouseenter', ()=>{
      peekK = Math.min(1, Math.max(0.35,
        (innerWidth - 40) / 800, (innerHeight - 90) / 480));
      peek.style.transform = 'scale(' + peekK.toFixed(3) + ')';
      peek.innerHTML = '<div class="cap">' + page +
        '页 · 800×480 全尺寸 · 橙框橙箭头 = 该控件触发的跳转</div>' + peekSvg(page);
      peek.style.display = 'block';
    });
    g.addEventListener('mousemove', e=>{
      const k = peekK;
      let x = e.clientX + 18, y = e.clientY + 14;
      if (x + 800 * k > innerWidth - 8) x = Math.max(4, e.clientX - 800 * k - 18);
      if (y + 500 * k > innerHeight - 8) y = Math.max(4, innerHeight - 500 * k - 8);
      peek.style.left = Math.max(4, x) + 'px'; peek.style.top = Math.max(4, y) + 'px';
    });
    g.addEventListener('mouseleave', ()=>{ peek.style.display = 'none'; });
  });
}
function openTree(){
  const t = document.getElementById('treeview');
  if (!t.childElementCount){
    t.innerHTML = document.getElementById('tree').textContent;
    t.querySelectorAll('.tnode').forEach(g=>g.onclick = ()=>{
      go(g.getAttribute('data-page'));
      showWork();
    });
    bindPeek(t);
  }
  document.getElementById('work').style.display = 'none';
  t.style.display = 'block';
  document.getElementById('treebtn').classList.add('on');
}
function showWork(){
  document.getElementById('treeview').style.display = 'none';
  document.getElementById('work').style.display = 'grid';
  document.getElementById('treebtn').classList.remove('on');
}
document.getElementById('treebtn').onclick = ()=>{
  document.getElementById('treeview').style.display === 'none' ? openTree() : showWork();
};
document.getElementById('back').onclick = back;
document.getElementById('home').onclick = ()=>go('主控');
document.addEventListener('keydown', e=>{ if(e.key==='Escape') back(); });
render();
// 默认打开即全览（设计图的 H5 形态）；#work 直达单页核验
if (location.hash !== '#work') openTree(); else showWork();
</script>
</body></html>"""
    html = html.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    html = html.replace("__TREE__", build_tree_svg(data))
    path = os.path.join(PROTO, "index.html")
    io.open(path, "w", encoding="utf-8", newline="\n").write(html)
    return path


def build_map(data):
    T = 0.2
    TW, TH = int(800 * T), int(480 * T)
    GAP, PADX, PADY = 14, 24, 14
    LX = 40
    TXT_W = 190
    X0 = LX + TXT_W
    W = 1600
    per_row = (W - X0 - 40 + GAP) // (TW + GAP)

    rows_y, y = [], 110
    for gi, (gname, pages, note) in enumerate(LEVELS):
        nrow = (len(pages) + per_row - 1) // per_row
        h = 52 + nrow * (TH + 26) + PADY
        rows_y.append((y, h, gname, pages, note))
        y += h + 22
    H = y + 70

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="Microsoft YaHei,Noto Sans SC,'
        f'PingFang SC,sans-serif">',
        sc.r(0, 0, W, H, sc.BG, "none", 0),
        sc.t(40, 44, "Haven Home · 页面分层方框图（22 屏）", 24, sc.T1, "700"),
        sc.t(40, 68, "同一方框内 = 同一层；方框标题写了这层的入口与返回；"
                     "逐条可点跳转见 prototype/index.html",
             11, sc.T2),
    ]

    for i, (gy, gh, gname, pages, note) in enumerate(rows_y):
        color = [sc.ACCENT, sc.GREEN, sc.BLUE, sc.PURPLE][i]
        out.append(sc.r(LX, gy, W - 2 * LX, gh, "#080C14", color, 12))
        out.append(sc.t(LX + 18, gy + 28, gname, 14, color, "700"))
        out.append(sc.t(LX + 18, gy + 46, note.split("；")[0], 8, sc.T3))
        out.append(sc.t(X0, gy + 28, f"{len(pages)} 屏", 10, sc.T3, "600"))
        for j, name in enumerate(pages):
            cx = X0 + (j % per_row) * (TW + GAP)
            cy = gy + 48 + (j // per_row) * (TH + 26)
            d = data[name]
            out.append(f'<g transform="translate({cx},{cy}) scale({T})">{d["svg"]}</g>')
            out.append(sc.r(cx, cy, TW, TH, "none", color, 4))
            out.append(sc.t(cx, cy + TH + 14, name, 10, sc.T1, "600"))
            n_nav = sum(1 for r in d["rows"] if r["target"])
            out.append(sc.t(cx + TW, cy + TH + 14, f"{len(d['rows'])} 控件 / "
                                                   f"{n_nav} 跳转", 8, sc.T3,
                            "400", "end"))

    # 层间关系写在每个方框的副标题里（入口/返回），不画跨层连线，避免叠线
    for i, (gy, gh, gname, pages, note) in enumerate(rows_y):
        if "；" in note:
            out.append(sc.t(LX + 18, gy + gh - 10, note.split("；")[1], 8, sc.T3))

    out.append(sc.t(40, H - 26, "层级：一级 1 屏 → 二级 房间 4 屏 / 工具页 11 屏 → "
                                "三级 设备详情 6 屏；每个方框内页面同层，可横向互跳的已标在方框标题",
                    10, sc.T2))
    out.append("</svg>")

    svg = os.path.join(OUT, "00_page_map.svg")
    io.open(svg, "w", encoding="utf-8", newline="\n").write("".join(out))
    print("written", svg, "size", W, H)
    try:
        import cairosvg
        png = os.path.join(OUT, "00_page_map.png")
        cairosvg.svg2png(url=svg, write_to=png, output_width=W, output_height=H)
        print("written", png)
    except Exception as e:
        print("png skip", e)


def main(argv=None):
    argv = list(argv or [])
    data = page_data()
    # 门禁：目标页必须存在；每页至少一条跳转（主控除外无强制）
    names = set(data)
    missing = [(p, n, t) for p, d in data.items() for r in d["rows"]
               for t in [r["target"]] if t and t not in names]
    assert not missing, f"跳转目标不存在: {missing[:3]}"
    assert len(data) >= 20, len(data)
    confirmed = read_state(argv)
    proto = build_prototype(data, confirmed)
    print("written", proto, "| 全览:", "已确认→出可点跳转+AI预估控件图"
          if confirmed else "未确认→只出全览核对态")
    build_map(data)
    print(f"[GATE] 屏 {len(data)} 跳转控件 "
          f"{sum(1 for d in data.values() for r in d['rows'] if r['target'])}")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])