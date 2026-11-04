"""H5 评审页生成器模板（2026-11-04 22:50 从 w78 当前实现同步，PR-0495）。

做法与踩坑：`reference/14_h5_review_overview.md`；验证通道：`tools/cdp/h5_edge.sh` + `tools/cdp/h5_probe.js`。
一次生成两份、同源不漂移：`overview_pro.html`（整页，双击本地看）+ `overview_pro.fragment.html`（片段，内联进对话）。

换工程只改这五处，其余结构照抄：
  1. 顶部 import：换成你工程的三个设计源模块（基元/页面语义表/跳转表）。
  2. IO_COLORS / IO_NAME / IO_DESC / OVERRIDES：6 类口径与逐控件覆盖。
  3. gestures()：哪些页之间有滑动手势、目标是谁。
  4. build() 里的分层规则与 AI 预估控件图开关。
  5. OUT 与 HTML 里的品牌字串（标题/页签名）。

当前交互（与 w78 源码一致，勿回退）：
  - 放大图钉在右侧停靠栏；点空白/遮罩/Esc/再点同卡收起，点停靠栏内部不误收。
  - 跳转演练直接换页，**不做过渡动画**；整块 innerHTML 替换，不叠页面层。
  - 全站只有一套来路栈 `trail`，`pushTrail()` 唯一入口；面包屑写「当前页 ← 返回目标」。
  - 返回 = 收起面板 + `selectCard(来路)`，不压栈、不打开面板。
  - 高清设计图（marks:false）也要渲染返回热区 `hotBack`。
  - `overview_confirmed` 未置真时不建热区；生成器收尾 `node --check` 校验内联 JS。
  - 分类覆盖不得吃掉 `behav=换页` 的跳转：build() 末尾有 assert。

铁律：H5 只内嵌设计源渲染出的帧 + 叠标注/热区，绝不重画界面；
      要改呈现就改设计源再重跑本脚本，不手改产出的 HTML。
"""

import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import simple_control as sc        # noqa: E402
import pages as pg                 # noqa: E402
import export_ui as eu             # noqa: E402

OUT = os.path.join(sc.OUT, "overview_pro.html")
OUT_FRAG = os.path.join(sc.OUT, "overview_pro.fragment.html")

IO_COLORS = {
    "in_read": "#7fb3ff", "out_read": "#8fa2b8", "in_write": "#c08cff",
    "out_write": "#5fd3a6", "nav": "#f2b45c", "gesture": "#ff8fb8",
}
IO_NAME = {
    "in_read": "内部读", "out_read": "外部读", "in_write": "内部写",
    "out_write": "外部写", "nav": "跳转按钮", "gesture": "跳动手势",
}
IO_DESC = {
    "in_read": "从 UI 自身取数（页名、计数、缓存时间）",
    "out_read": "从硬件取数（传感值、功率、画面）",
    "in_write": "写 UI 层数据（已读、筛选、配色、本地设置）",
    "out_write": "写硬件（开关、亮度、开合、模式、布防）",
    "nav": "按钮/返回 → 跳到指定页",
    "gesture": "左右滑动 → 切换界面",
}

# 个别控件的数据流向按语义覆盖，不靠通用规则猜
OVERRIDES = {
    ("全部设备", "搜索框"): "in_read",
    ("离线态", "同步信息"): "in_read",
    ("主卧", "晚安模式"): "in_read",
    ("灯详情", "添加定时"): "in_write",
    ("场景详情", "编辑动作"): "in_write",
    ("能源统计", "今日"): "in_write",
    ("能源统计", "本周"): "in_write",
}

ROOMS = ["客厅", "主卧", "厨房", "浴室"]
DETAILS = ["灯详情", "空调详情", "窗帘详情", "传感详情", "插座详情", "摄像头详情"]


def gestures():
    """{页: [(方向标签, 目标说明, 手势框)]}，框在页面左右边缘。"""
    g = {}
    cyc = ROOMS + DETAILS
    for i, p in enumerate(cyc):
        nxt = cyc[(i + 1) % len(cyc)]
        prv = cyc[(i - 1) % len(cyc)]
        who = "房间页" if p in ROOMS else "详情页"
        g[p] = [{"label": "← 滑", "to": "上一个%s：%s" % (who, prv),
                 "go": prv, "box": (0, 130, 26, 260)},
                {"label": "→ 滑", "to": "下一个%s：%s" % (who, nxt),
                 "go": nxt, "box": (774, 130, 26, 260)}]
    g["能源统计"] = [{"label": "← → 滑", "to": "切换 今日 / 本周 视图",
                  "go": "能源统计", "box": (0, 130, 26, 260)}]
    return g


def io_of(page, row):
    k = OVERRIDES.get((page, row["name"]))
    if k:
        return k
    if row["behav"] in ("换页", "返回"):
        return "nav"
    if row["behav"] == "下发硬件":
        return "out_write"
    return "out_read" if row["cat"] == "read" else "in_write"


def build():
    data = eu.page_data()
    order = [t for (t, _f, _e, _x, _r) in pg.PAGES]
    parents = {}
    for p, d in data.items():
        for r in d["rows"]:
            if r["target"]:
                parents.setdefault(r["target"], []).append((p, r["name"], r["cat"]))
    depth = {order[0]: 0}
    changed = True
    while changed:
        changed = False
        for p, d in data.items():
            if p not in depth:
                ds = [depth[a] + 1 for (a, _n, _c) in parents.get(p, []) if a in depth]
                if ds:
                    depth[p] = min(ds)
                    changed = True
    status = {q for q in order if q != order[0] and not parents.get(q)}
    for q in status:
        depth[q] = 1            # 状态页不单独成层：按它服务的页面归层

    ges = gestures()
    out = {}
    for p in order:
        d = data[p]
        rows = []
        for r in d["rows"]:
            io_k = io_of(p, r)
            rows.append({"n": r["n"], "name": r["name"], "io": io_k,
                         "act": r["act"], "box": r["box"],
                         "target": r["target"] if io_k == "nav" else "",
                         "dyn": r["behav"] == "返回"})
        out[p] = {"svg": d["svg"], "rows": rows, "layer": depth[p] + 1,
                  "status": p in status,
                  "entry": d["entry"], "exit": d["exit"],
                  "gesture": ges.get(p, [])}
    lost = [(p, r["n"], r["name"]) for p in order for r in out[p]["rows"]
            if any(q["name"] == r["name"] and q["behav"] == "换页" for q in data[p]["rows"])
            and r["io"] != "nav"]
    assert not lost, "覆盖判类吃掉了换页控件的跳转：%s" % lost
    return {"pages": out, "order": order,
            "io": {"color": IO_COLORS, "name": IO_NAME, "desc": IO_DESC},
            "layerNote": {1: "一级：与主页同一种切换方式可达（本工程无 pageview tab / 侧栏，故只有主控）",
                          2: "二级：从一级页用按钮进入的新子页",
                          3: "三级：从二级页进入的新子页",
                          4: "四级：从三级页进入的新子页",
                          5: "五级：从四级页进入的新子页"}}


CSS = r"""
:root{--bg:#05080f;--bg2:#0a0f18;--card:#121822;--edge:#27313f;--t1:#f4f7fb;--t2:#b9c4d4;
--t3:#75859c;--nav:#f2b45c;--r:14px;--f:"Microsoft YaHei","PingFang SC","Noto Sans SC",system-ui,sans-serif}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(1300px 700px at 15% -15%,#0e1522,#05080f 62%);
color:var(--t1);font:13px/1.65 var(--f);-webkit-font-smoothing:antialiased}
header{position:sticky;top:0;z-index:30;background:rgba(10,15,24,.88);backdrop-filter:blur(10px);
border-bottom:1px solid var(--edge);padding:9px 22px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.brand{font-size:14px;font-weight:700;letter-spacing:.3px}
.tabs{display:flex;gap:6px}
.btn{font:12px var(--f);color:var(--t1);background:#1a2230;border:1px solid var(--edge);
border-radius:999px;padding:5px 13px;cursor:pointer;transition:.15s}
.btn:hover{background:#222c3c}
.btn.on{border-color:var(--nav);color:var(--nav);background:rgba(242,180,92,.12)}
.sp{flex:1}
.crumb{color:var(--t3);font-size:12px}.crumb b{color:var(--nav)}
main{padding:18px 22px 40px;max-width:2100px;margin:0 auto}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 16px;padding:10px 14px;
border:1px solid var(--edge);border-radius:var(--r);background:rgba(18,24,34,.6)}
.lg{display:inline-flex;align-items:center;gap:7px;font-size:11.5px;color:var(--t2);
border:1px solid var(--edge);border-radius:999px;padding:3px 11px 3px 8px;cursor:pointer;transition:.15s}
.lg:hover{border-color:#3a4658}
.lg.off{opacity:.35}
.lg i{width:10px;height:10px;border-radius:3px;flex:none}
.lg b{font-weight:600}
.lg em{font-style:normal;color:var(--t3);margin-left:2px}
h2.sec{display:flex;align-items:center;gap:10px;font-size:12px;font-weight:600;letter-spacing:1.4px;
color:var(--t3);text-transform:uppercase;margin:26px 0 12px}
h2.sec:after{content:"";flex:1;height:1px;background:var(--edge)}
h2.sec .cnt{color:#5a6a80;letter-spacing:0;text-transform:none;font-size:11.5px}
.layerrow{display:flex;gap:18px;overflow-x:auto;padding:4px 4px 18px;scroll-snap-type:x proximity}
.layerrow::-webkit-scrollbar{height:9px}
.layerrow::-webkit-scrollbar-thumb{background:#22303f;border-radius:8px}
.pcard{position:relative;flex:0 0 auto;width:520px;border:1px solid var(--edge);border-radius:var(--r);
background:var(--card);overflow:hidden;cursor:pointer;transition:.16s;scroll-snap-align:start}
.pcard:hover{border-color:#3a4658;transform:translateY(-2px)}
.pcard.sel{border-color:var(--nav);box-shadow:0 0 0 2px var(--nav),
  0 14px 34px rgba(0,0,0,.5)}
.pcard.sel:after{content:"已选中";position:absolute;top:-10px;left:14px;font-size:10.5px;
  font-weight:700;color:#05080f;background:var(--nav);border-radius:999px;padding:1px 9px}
.pcard.flash{animation:pop .9s ease}
@keyframes pop{0%{box-shadow:0 0 0 2px var(--nav),0 0 0 0 rgba(242,180,92,.55)}
70%{box-shadow:0 0 0 2px var(--nav),0 0 0 18px rgba(242,180,92,0)}
100%{box-shadow:0 0 0 2px var(--nav),0 0 0 0 rgba(242,180,92,0)}}
#dock{display:none;position:sticky;top:78px;border:1px solid var(--nav);border-radius:18px;
  background:var(--bg2);padding:12px 12px 14px;max-height:calc(100vh - 96px);overflow:auto}
.wrap.docked #dock{display:block}
.wrap.docked{display:grid;grid-template-columns:minmax(0,1fr) minmax(520px,46vw);gap:18px;align-items:start}
#dock h3{margin:0 0 2px;font-size:15px;display:flex;align-items:center;gap:8px}
#dock .dh{color:var(--t3);font-size:11.5px;margin:0 0 10px}
#dock svg{display:block;width:100%;height:auto;background:#05080f;border-radius:12px}
#dockscrim{position:fixed;inset:0;background:rgba(3,6,12,.62);z-index:54;display:none}
@media (max-width:1400px){
  .wrap.docked{display:block}
  #dock{position:fixed;top:64px;right:14px;bottom:14px;left:auto;width:min(760px,92vw);
    z-index:55;max-height:none;box-shadow:0 24px 60px rgba(0,0,0,.6)}
  body.docked #dockscrim{display:block}
}
.pcard .stt{position:absolute;top:8px;right:8px;font-size:10.5px;color:#ff7a6b;border:1px solid #5a3038;border-radius:999px;padding:1px 7px;background:rgba(5,8,15,.7)}
.pcard .cap{padding:8px 11px;display:flex;align-items:center;gap:7px;font-size:13px;font-weight:600}
.pcard .cap .c{margin-left:auto;color:var(--t3);font-size:11px;font-weight:400}
.pcard svg.mini{display:block;width:100%;height:auto;background:#05080f}
.pcard .tags{padding:2px 11px 12px;display:block}
.tg{display:flex;flex-wrap:wrap;align-items:center;gap:4px 5px;margin:0 0 6px}
.tg:last-child{margin-bottom:0}
.tl{flex:0 0 78px;display:inline-flex;align-items:center;gap:6px;font-size:10.5px;font-weight:700;
border:1px solid;border-radius:999px;padding:1px 8px;background:rgba(5,8,15,.5)}
.tl em{font-style:normal;margin-left:auto;font-weight:400;color:var(--t2);font-size:11px}
.pill{display:inline-flex;align-items:center;gap:6px;font:11px var(--f);border:1px solid var(--edge);
border-radius:999px;padding:2px 10px 2px 7px;color:var(--t2);cursor:pointer;transition:.15s;background:none}
.pill:hover{border-color:var(--nav);color:var(--nav)}
.pill i{width:7px;height:7px;border-radius:50%;flex:none;background:#f2b45c}
.pill.nav{background:#f2b45c;border-color:#f2b45c;color:#05080f;font-weight:700}
.pill.nav b{font-weight:900}
.pill.nav:hover{background:#ffc873;border-color:#ffc873;color:#05080f}
.pill.back{background:rgba(242,180,92,.10);border-color:#f2b45c;color:#f2b45c;font-weight:700}
.pill.back:hover{background:rgba(242,180,92,.28);border-color:#ffc873;color:#ffc873}
.pill.ges b{font-weight:900}
.pill.ges:hover{background:#ffa5c6;border-color:#ffa5c6;color:#05080f}
.pill.static{border-color:transparent;background:rgba(117,133,156,.09);color:#8b9aac;font-weight:400}
.pill.static:hover{border-color:transparent;color:#8b9aac;background:rgba(117,133,156,.14)}
g.hi rect{stroke-width:4!important;opacity:1!important}
g.hi circle{r:12}
.badge{font-size:10.5px;font-weight:700;border:1px solid var(--nav);color:var(--nav);
border-radius:999px;padding:1px 8px}
.stage{display:grid;grid-template-columns:minmax(0,1fr) 430px;gap:18px;align-items:start}
.big{border:1px solid var(--edge);border-radius:18px;overflow:hidden;background:#05080f;position:relative}
.big .pg{display:block}
.big svg{display:block;width:100%;height:auto}
svg g.hot{cursor:pointer}
svg g.hot>rect:not(.hit):not(.hitg){transition:.12s}
svg g.hot:hover>rect:not(.hit):not(.hitg){stroke-width:4}
svg rect.hit{fill:rgba(242,180,92,.10)}
svg g.hot:hover rect.hit{fill:rgba(242,180,92,.32)}
svg g.hot:active rect.hit{fill:rgba(242,180,92,.62)}
svg rect.hitg{fill:rgba(255,143,184,.12)}
svg g.hot:hover rect.hitg{fill:rgba(255,143,184,.34)}
svg g.hot:active rect.hitg{fill:rgba(255,143,184,.6)}
.trailbar{display:flex;align-items:center;gap:7px;flex-wrap:nowrap;overflow-x:auto;margin:0 0 10px;
  padding-bottom:2px;font-size:12px;color:var(--t3)}
.trailbar>*{flex:0 0 auto}
.trailbar .t{border:1px solid var(--edge);border-radius:999px;padding:1px 9px;color:var(--t2)}
.trailbar .t.now{border-color:var(--nav);color:var(--nav);font-weight:700}
.trailbar .ta{color:#44536a}
.btn[disabled]{opacity:.4;cursor:default}
.side{border:1px solid var(--edge);border-radius:18px;background:var(--bg2);padding:14px;
position:sticky;top:78px}
.side h3{margin:0 0 4px;font-size:15px}
.side .m{color:var(--t3);font-size:11.5px;margin:0 0 12px}
.grp{margin:0 0 12px}
.grp .gt{display:flex;align-items:center;gap:7px;font-size:11.5px;color:var(--t3);margin-bottom:5px}
.grp .gt i{width:9px;height:9px;border-radius:3px}
.grp .gt em{font-style:normal;color:#5a6a80;margin-left:auto;font-size:11px}
.item{display:flex;gap:8px;align-items:baseline;padding:4px 0;font-size:12px;
border-bottom:1px solid #101823}
.item:last-child{border-bottom:0}
.item .k{font-size:10.5px;color:var(--t3);min-width:18px}
.item .go{margin-left:auto;color:var(--nav);font-size:11.5px;cursor:pointer}
.item .go:hover{text-decoration:underline}
.hint{color:var(--t3);font-size:11.5px;line-height:1.75;margin:10px 0 0}
.gesline{display:flex;align-items:center;gap:8px;font-size:12px;color:#ff8fb8;
border:1px dashed #ff8fb8;border-radius:999px;padding:4px 12px;margin-top:8px}
@media (max-width:1250px){.stage{grid-template-columns:1fr}.side{position:static}}
"""

JS = r"""
const D = JSON.parse(document.getElementById('data').textContent);
const IO = D.io;
let view = 'layers', cur = D.order[0];
const hist = [];                      // {view, cur, y, rows}
function pushState(){
  hist.push({view:view, cur:cur, y:window.scrollY,
    rows:[...document.querySelectorAll('.layerrow')].map(r=>r.scrollLeft)});
  if(hist.length>60) hist.shift();
}
function popState(){
  const h = hist.pop();
  if (!h) return false;
  view = h.view; cur = h.cur; trail = []; render();
  requestAnimationFrame(()=>{
    window.scrollTo(0, h.y);
    document.querySelectorAll('.layerrow').forEach((r,i)=>
      { r.scrollLeft = (h.rows && h.rows[i]) || 0; });
  });
  return true;
}
let ioOn = new Set(Object.keys(IO.color));

function showIo(r){ return ioOn.has(r.io); }

/* 帧上叠加：6 色控件框 + 序号 + 跳转箭头 + 手势弧 */
function mark(page, opts){
  const p = D.pages[page], o = opts || {};
  const lane = (o.lane !== false) && !o.slim;
  const VW = lane ? 992 : 800;
  let s = '<svg viewBox="0 0 '+VW+' 480" xmlns="http://www.w3.org/2000/svg">' + p.svg;
  if (lane) s += '<rect x="816" y="0" width="176" height="480" fill="#0a0f18"/>'
    + '<line x1="816" y1="0" x2="816" y2="480" stroke="#27313f"/>'
    + '<text x="828" y="16" font-size="10.5" fill="#5a6a80" font-family="sans-serif">'
    + '目标页</text>';
  s += '<defs>'
    + '<marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6"'
    + ' orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#f2b45c"/></marker>'
    + '<marker id="ag" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6"'
    + ' orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="#ff8fb8"/></marker>'
    + '</defs>';
  if (o.marks !== false){
    p.rows.filter(showIo).forEach(r=>{
      const b=r.box, col=IO.color[r.io];
      const hot = o.hot ? (r.io==='nav' && (r.target || r.dyn)) : (o.hotBack && r.dyn);
      const attrs = !hot ? '' : (r.dyn ? ' class="hot" data-back="1"'
                                       : ' class="hot" data-go="'+r.target+'" data-dir="1"');
      s += '<g id="'+(o.pid||'x')+'-'+r.n+'"'+attrs+'>'
         + '<rect x="'+(b[0]-1.5)+'" y="'+(b[1]-1.5)+'" width="'+(b[2]+3)+'" height="'+(b[3]+3)+
           '" fill="none" stroke="'+col+'" stroke-width="'+(o.slim?1.8:2.4)+'" rx="8" opacity="'+
           (o.slim?0.9:1)+'"/>';
      if (hot) s += '<rect class="hit" x="'+b[0]+'" y="'+b[1]+'" width="'+b[2]+'" height="'+b[3]+
        '" rx="8" pointer-events="all"/>';
      if (r.io==='nav' && o.slim){          // 缩略图上也画一小段跳转箭头
        s += '<path d="M'+(b[0]+b[2]+2)+','+(b[1]+b[3]/2)+' h14" stroke="#f2b45c"'+
             ' stroke-width="2.4" marker-end="url(#ar)"/>';
      }
      s += '<circle cx="'+(b[0]+1)+'" cy="'+(b[1]+1)+'" r="'+(o.slim?8:11)+'" fill="'+col+'"/>'+
           '<text x="'+(b[0]+1)+'" y="'+(b[1]+(o.slim?3.6:5))+'" font-size="'+(o.slim?8.5:11)+
           '" font-weight="700" fill="#05080f" text-anchor="middle" font-family="sans-serif">'+
           r.n+'</text></g>';
      if (r.io==='nav' && r.target && !o.slim && !lane){
        const dir=(b[0]+b[2]+210<800)?1:-1;
        const sx=dir>0?b[0]+b[2]+2:b[0]-2, ty=b[1]+b[3]/2, tx=sx+dir*40;
        s += '<path d="M'+sx+','+ty+' h'+(dir*38)+'" stroke="#f2b45c" stroke-width="2.2"'+
             ' marker-end="url(#ar)"/>';
        const label='→ '+r.target, w=label.length*12+16;
        const lx=dir>0?tx+3:tx-w-3;
        s += '<rect x="'+lx+'" y="'+(ty-12)+'" width="'+w+'" height="24" rx="12" fill="#f2b45c"/>'+
             '<text x="'+(lx+w/2)+'" y="'+(ty+4.5)+'" font-size="11.5" font-weight="700" fill="#05080f"'+
             ' text-anchor="middle" font-family="sans-serif">'+label+'</text>';
      }
    });
    if (lane){
      const navs = p.rows.filter(r=>r.io==='nav' && r.target && showIo(r))
                         .sort((a,c)=>a.box[1]-c.box[1]);
      const step = Math.max(21, Math.min(30, 452 / Math.max(navs.length,1)));
      navs.forEach((r,i)=>{
        const b=r.box, cy=22+i*step+step/2, sx=b[0]+b[2], sy=b[1]+b[3]/2;
        if (o.hot) s += '<g class="hot" data-go="'+r.target+'" data-dir="1">';
        s += '<path d="M'+sx+','+sy+' C'+(sx+70)+','+sy+' 780,'+cy+' 820,'+cy+'" '
           + 'fill="none" stroke="#f2b45c" stroke-width="1.6" opacity=".85"'
           + ' marker-end="url(#ar)"/>';
        s += '<rect x="824" y="'+(cy-11)+'" width="162" height="22" rx="11" fill="#f2b45c"/>'+
             '<text x="834" y="'+(cy+4)+'" font-size="11.5" font-weight="700" fill="#05080f"'+
             ' font-family="sans-serif">'+r.n+'. → '+r.target+'</text>';
        if (o.hot) s += '</g>';
      });
    }
    p.gesture.filter(()=>showIo({io:'gesture'})).forEach(g=>{
      const b=g.box, cx=b[0]+b[2]/2, y0=b[1]+8, y1=b[1]+b[3]-8;
      const bulge = b[0] < 400 ? 34 : -34;
      if (o.hot) s += '<g class="hot" data-go="'+g.go+'" data-dir="'+(g.label.indexOf('←')===0?-1:1)+'">'+
        '<rect x="'+b[0]+'" y="'+b[1]+'" width="'+b[2]+'" height="'+b[3]+'" class="hitg" pointer-events="all"/></g>';
      s += '<path d="M'+cx+','+y0+' q'+bulge+','+((y1-y0)/2)+' 0,'+(y1-y0)+'" fill="none"'+
           ' stroke="#ff8fb8" stroke-width="2.4" stroke-dasharray="7 6" marker-end="url(#ag)"/>';
      s += '<text x="'+(cx+bulge*0.62)+'" y="'+((y0+y1)/2)+'" font-size="11" fill="#ff8fb8"'+
           ' text-anchor="middle" font-family="sans-serif">'+g.label+'</text>';
    });
  }
  if (o.hotBack && o.marks === false) {          // 无标注视图（高清设计图）也要能点返回
    p.rows.filter(r=>r.dyn).forEach(r=>{
      const b=r.box;
      s += '<g class="hot" data-back="1"><rect class="hit" x="'+b[0]+'" y="'+b[1]+'" width="'+
           b[2]+'" height="'+b[3]+'" rx="8" pointer-events="all"/></g>';
    });
  }
  return s + '</svg>';
}

function pill(r){
  if (!r.target) return '<button class="pill back" data-back="1" data-hi="'+r.n+'"'+
    ' title="目标=来路（运行时决定）；在总览里点它 = 回到上一次浏览的页">'+
    '<i style="background:#f2b45c"></i>'+r.n+'. '+r.name+' <b>‹</b> 来路</button>';
  return '<button class="pill nav" data-go="'+r.target+'" data-hi="'+r.n+'">'+r.n+'. '+r.name+
         ' <b>→</b> '+r.target+'</button>';
}
function tagIo(r){
  return '<span class="pill static" data-hi="'+r.n+'" title="'+r.act+'"><i style="background:'+
         IO.color[r.io]+'"></i>'+r.n+'. '+r.name+'</span>';
}
function tally(d){
  return d.rows.length + ' 控件';
}

/* 底部标签：按 6 类分行，固定顺序（可操作在前、数据在后），不再按控件序号交错 */
const IO_ORDER = ['nav', 'gesture', 'out_write', 'in_write', 'out_read', 'in_read'];
function tagLine(k, items){
  return '<div class="tg"><span class="tl" style="color:' + IO.color[k] + ';border-color:' +
    IO.color[k] + '">' + IO.name[k] + '<em>' + items.length + '</em></span>' + items.join('') + '</div>';
}
function tags(d){
  const lines = [];
  IO_ORDER.forEach(k=>{
    if (!ioOn.has(k)) return;
    if (k === 'gesture'){
      const g = d.gesture;
      if (g.length) lines.push(tagLine(k, g.map(x=>'<span class="pill ges" data-go="'+x.go+
        '" title="'+x.to+'">'+x.label+' <b>→</b> '+x.to+'</span>')));
      return;
    }
    const rs = d.rows.filter(r=>r.io===k);
    if (!rs.length) return;
    lines.push(tagLine(k, rs.map(r=>(k==='nav')?pill(r):tagIo(r))));
  });
  return lines.join('') || '<div class="tg"><span class="m">当前筛选下无控件</span></div>';
}

/* 视图 1：分层总览（每层横向） */
function vLayers(){
  const by={};
  D.order.forEach(p=>{const l=D.pages[p].layer;(by[l]=by[l]||[]).push(p);});
  return Object.keys(by).sort().map(l=>
    '<h2 class="sec"><span class="badge">L'+l+'</span>'+D.layerNote[l]+
    '<span class="cnt">'+by[l].length+' 页</span></h2>'+
    '<div class="layerrow">'+by[l].map(p=>{
      const d=D.pages[p];
      return '<div class="pcard'+(p===cur?' sel':'')+'" data-sel="'+p+'" data-dock="'+p+'" title="点开右侧放大图">'+
          (d.status?'<div class="stt">状态页</div>':'')+
        mark(p,{slim:true,marks:true,pid:p,hotBack:true}).replace('<svg ','<svg class="mini" ')+
        '<div class="cap">'+p+'<span class="c">'+tally(d)+'</span></div>'+
        '<div class="tags">'+tags(d)+'</div></div>';
    }).join('')+'</div>').join('');
}

/* 视图 2：跳转演练——帧上真控件可点就真跳页（按真机方向横滑），6 类标注与右栏清单都保留 */
let trail = [];
function sideHtml(p){
  const d=D.pages[p];
  const groups=['nav','gesture','out_write','in_write','out_read','in_read']
    .filter(k=>ioOn.has(k));
  const list=groups.map(k=>{
    let items = k==='gesture'
      ? d.gesture.map(g=>'<div class="item"><span class="k">✋</span><span>'+g.label+
                         '</span><span class="go" style="color:#ff8fb8" data-go="'+g.go+
                         '" data-dir="'+(g.label.indexOf('←')===0?-1:1)+'">'+g.to+'</span></div>')
      : d.rows.filter(r=>r.io===k).map(r=>'<div class="item"><span class="k">'+r.n+'</span>'+
        '<span>'+r.name+'</span>'+(r.target?'<span class="go" data-go="'+r.target+'" data-dir="1">→ '+r.target+
        '</span>':'<span class="go" style="color:var(--t3);cursor:default">'+r.act+'</span>')+'</div>');
    if(!items.length) return '';
    return '<div class="grp"><div class="gt"><i style="background:'+IO.color[k]+'"></i>'+
      IO.name[k]+'<em>'+IO.desc[k]+'</em></div>'+items.join('')+'</div>';
  }).join('');
  return '<h3>'+p+'页 <span class="badge">L'+d.layer+'</span></h3>'+
    '<p class="m">'+d.rows.length+' 个控件 · 入口：'+d.entry.replace(/^入口：/,'')+
    ' · 出口：'+d.exit.replace(/^出口：/,'')+'</p>'+
    (list||'<p class="m">当前筛选下没有控件</p>')+
    '<p class="hint">点帧上橙色控件 = 真跳到目标页（新页从右滑入）；点左右边缘粉色条 = '+
    '按手势方向滑页；‹ 上一页 = 反向滑回。序号 = 右栏行号，顶栏色签可按类隐藏。</p>';
}
function trailHtml(){
  const path = trail.concat([cur]);
  return '<button class="btn" id="trailback"'+(trail.length?'':' disabled')+'>‹ 上一页</button>'+
    '<button class="btn" id="trailhome">回主控</button>'+
    path.map((x,i)=>'<span class="t'+(i===path.length-1?' now':'')+'">'+x+'</span>')
        .join('<span class="ta">→</span>');
}
function vJump(){
  const d=D.pages[cur];
  return '<div class="stage"><div>'+
    '<div class="trailbar">'+trailHtml()+'</div>'+
    '<div class="big" id="bigbox"><div class="pg">'+mark(cur,{hot:true})+'</div></div>'+
    (d.gesture.length?'<div class="gesline">✋ 本页手势：'+
      d.gesture.map(g=>g.label+' → '+g.to).join('；')+'</div>':'')+
    '</div><div class="side" id="side">'+sideHtml(cur)+'</div></div>';
}
function swapBig(p){
  const host=document.getElementById('bigbox'); if(!host) return;
  host.innerHTML = '<div class="pg">' + mark(p,{hot:true}) + '</div>';   // 直接换页，不做滑动
}
function crumbText(){
  return trail.length ? cur + '  ← ' + trail[trail.length-1] : cur + '（无来路）';
}
function refreshJump(){
  const s=document.getElementById('side'); if(s) s.innerHTML=sideHtml(cur);
  const t=document.querySelector('.trailbar'); if(t) t.innerHTML=trailHtml();
  document.getElementById('crumb').textContent=crumbText();
}
function pushTrail(p){
  if(!p) return;
  if(trail[trail.length-1] === p) return;       // 连续同一页不重复记
  trail.push(p); if(trail.length>10) trail.shift();
}
function navJump(p, dir){
  if(!p || !D.pages[p] || p===cur) return;
  pushState(); pushTrail(cur);
  cur=p;
  swapBig(p, dir||1); refreshJump();
}
function navBack(){
  if(!trail.length) return false;
  cur=trail.pop(); swapBig(cur,-1); refreshJump(); return true;
}

/* 视图 3：高清设计图（每层横向、原尺寸、无标注） */
function vDesign(){
  const by={};
  D.order.forEach(p=>{const l=D.pages[p].layer;(by[l]=by[l]||[]).push(p);});
  return Object.keys(by).sort().map(l=>
    '<h2 class="sec"><span class="badge">L'+l+'</span>'+D.layerNote[l]+'</h2>'+
    '<div class="layerrow">'+by[l].map(p=>
      '<div class="pcard'+(p===cur?' sel':'')+'" data-sel="'+p+'" data-dock="'+p+'" title="点开右侧放大图" style="width:660px">'+
      mark(p,{marks:false,lane:false,hotBack:true}).replace('<svg ','<svg class="mini" ')+
      '<div class="cap">'+p+'<span class="c">800×480 · 原尺寸</span></div></div>').join('')+
    '</div>').join('');
}

function legend(){
  return Object.keys(IO.color).map(k=>
    '<button class="lg'+(ioOn.has(k)?'':' off')+'" data-io="'+k+'">'+
    '<i style="background:'+IO.color[k]+'"></i><b>'+IO.name[k]+'</b>'+
    '<em>'+IO.desc[k]+'</em></button>').join('')
    + '<span class="end" style="margin-left:auto;color:#5a6a80;font-size:11.5px">'
    + '总览内：点跳转标签 → 平滑滑到目标页并加选中外框；点卡片本体 → 右侧停靠栏出带标注放大图（再点卡片 / 点空白处 / Esc 收起）；'
    + '返回 = 回到上一次浏览位置</span>';
}

function render(){
  document.getElementById('legend').innerHTML = legend();
  document.getElementById('body').innerHTML =
    view==='layers'?vLayers():view==='jump'?vJump():vDesign();
  document.getElementById('crumb').textContent = cur;
  document.querySelectorAll('.tabs .btn').forEach(b=>
    b.classList.toggle('on', b.getAttribute('data-v')===view));
}
function selectCard(p){                       // 只选卡不记来路（返回时用）
  const el=document.querySelector('.pcard[data-sel="'+p+'"]');
  if(!el) return false;
  document.querySelectorAll('.pcard').forEach(c=>
    c.classList.toggle('sel', c.getAttribute('data-sel')===p));
  const rows=[...document.querySelectorAll('.layerrow')];
  rows.forEach(r=>r.style.scrollSnapType='none');   // snap 会把平滑滑动过程拽回卡头
  el.scrollIntoView({behavior:'smooth', block:'center', inline:'center'});
  clearTimeout(selectCard.t);
  selectCard.t=setTimeout(()=>rows.forEach(r=>r.style.scrollSnapType=''), 600);
  el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash');
  cur=p; document.getElementById('crumb').textContent=crumbText();
  return true;
}
function reveal(p){
  if(!document.querySelector('.pcard[data-sel="'+p+'"]')) return false;
  const prev = cur;
  if(!selectCard(p)) return false;
  if(prev !== p){ pushTrail(prev); }
  if(dockOn) openDock(p, true, true);     // 放大图跟着换页，但不重复记来路
  return true;
}
function go(p, dir){
  if (!p) return;
  if (view==='jump'){ navJump(p, dir); return; }
  if (view==='layers'){ pushState(); if(reveal(p)) return; cur=p; view='jump'; trail=[]; render(); return; }
  if (p===cur) return;
  pushState();
  cur=p; render();
}
/* 右侧停靠放大栏：点卡片开/关，钉住不跟随鼠标；窄窗口自动改成右侧浮层 */
let dockOn = false;
function openDock(p, keepPos, fromBack){
  const d = D.pages[p]; if(!d) return;
  if(!fromBack && p !== cur){ pushTrail(cur); }
  dockOn = true; cur = p;
  document.getElementById('dock').innerHTML =
    '<h3>'+p+'页 <span class="badge">L'+d.layer+'</span>'+
    '<button class="btn" id="dockx" style="margin-left:auto">✕ 收起</button></h3>'+
    '<p class="dh">'+d.rows.length+' 控件 · 原 800×480 · 再点卡片、点空白处或按 Esc 收起</p>'+
    mark(p,{marks:true,lane:false,hotBack:true}).replace('<svg ', '<svg class="dsvg" ');
  document.getElementById('wrap').classList.add('docked');
  document.body.classList.add('docked');
  document.getElementById('dockx').onclick = closeDock;
  document.getElementById('crumb').textContent = p;
  document.querySelectorAll('.pcard').forEach(c=>
    c.classList.toggle('sel', c.getAttribute('data-sel')===p));
  const el = document.querySelector('.pcard.sel');
  if (el && !keepPos) el.scrollIntoView({block:'nearest', inline:'center'});
}
function closeDock(){
  dockOn = false;
  document.getElementById('wrap').classList.remove('docked');
  document.body.classList.remove('docked');
}
document.addEventListener('click', e=>{
  if(e.target.closest('#dockscrim') || e.target.closest('#dockx')){ closeDock(); return; }
  const io=e.target.closest('[data-io]');
  if(io){const k=io.getAttribute('data-io');
    ioOn.has(k)?ioOn.delete(k):ioOn.add(k); render(); return;}
  const t=e.target.closest('[data-v]');
  if(t){closeDock(); view=t.getAttribute('data-v'); trail=[]; render(); return;}
  if(e.target.closest('[data-back]')){
    if(view==='jump'){ navBack(); }
    else {
      const h = trail.pop();                  // 与演练共用同一套来路
      const to = (h && D.pages[h]) ? h : D.order[0];
      if(dockOn) closeDock();                 // 返回不是"放大"，先把放大图收掉
      selectCard(to);
      if(!h){ document.getElementById('crumb').textContent = to + '（没有来路，已回主控）'; }
      return;
    }
  }
  if(e.target.closest('#trailback')){ navBack(); return; }
  if(e.target.closest('#trailhome')){ navJump(D.order[0], -1); return; }
  const g=e.target.closest('[data-go]');
  if(g){ go(g.getAttribute('data-go'), g.hasAttribute('data-dir')?+g.getAttribute('data-dir'):1); return; }
  const dk=e.target.closest('[data-dock]');
  if(dk){ const p=dk.getAttribute('data-dock');
    (dockOn && cur===p) ? closeDock() : openDock(p); return; }
  if(dockOn && !e.target.closest('#dock')) closeDock();   // 点空白处即收起，不用刻意找关闭键
});
window.addEventListener('keydown', e=>{ if(e.key==='Escape') back(); });
function back(){
  if (view==='jump' && trail.length){ navBack(); return; }
  if(dockOn){ closeDock(); return; } popState();
}
document.addEventListener('mouseover', e=>{
  const t=e.target.closest('[data-hi]'); if(!t) return;
  const card=t.closest('.pcard'); if(!card) return;
  const g=card.querySelector('g[id$="-'+t.getAttribute('data-hi')+'"]');
  if(g) g.classList.add('hi');
});
document.addEventListener('mouseout', e=>{
  const t=e.target.closest('[data-hi]'); if(!t) return;
  const card=t.closest('.pcard'); if(!card) return;
  const g=card.querySelector('g.hi'); if(g) g.classList.remove('hi');
});
function boot(){
  document.getElementById('back').onclick=back;
  document.getElementById('home').onclick=()=>go(D.order[0]);
  const v=location.hash.slice(1);
  if(['layers','jump','design'].includes(v)) view=v;
  render();
}
if(document.readyState==='loading') window.addEventListener('DOMContentLoaded', boot); else boot();
"""

HTML = r"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Haven Home · 全览专业版</title><style>__CSS__</style></head><body>
<header>
  <span class="brand">Haven Home · 全览专业版</span>
  <div class="tabs">
    <button class="btn" data-v="layers">分层总览</button>
    <button class="btn" data-v="jump">跳转演练</button>
    <button class="btn" data-v="design">高清设计图</button>
  </div>
  <button class="btn" id="back">‹ 返回</button>
  <button class="btn" id="home">回主控</button>
  <span class="sp"></span>
  <span class="crumb">当前页 <b id="crumb">主控</b></span>
</header>
<main><div id="legend" class="legend"></div>
<div class="wrap" id="wrap"><div id="body"></div><aside id="dock"></aside></div></main>
<div id="dockscrim"></div>
<script id="data" type="application/json">__DATA__</script>
<script>__JS__</script></body></html>"""


def fragment(html):
    """整页 → 可直接嵌进对话/宿主页的片段：同一份 CSS+JS，不另写第二版。"""
    css = html.split("<style>")[1].split("</style>")[0]
    body = html.split("<body>", 1)[1].rsplit("</body>", 1)[0]
    skin = ("#h5ov{background:radial-gradient(1300px 700px at 15% -15%,#0e1522,#05080f 62%);"
            "color:#f4f7fb;min-height:100vh}")
    return (u'<div id="h5ov">\n<style>\n' + skin + u"\n" + css + u"\n</style>\n"
            + body + u"\n</div>")


def main():
    payload = build()
    html = (HTML.replace("__CSS__", CSS).replace("__JS__", JS)
            .replace("__DATA__", json.dumps(payload, ensure_ascii=False)))
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(html)
    io.open(OUT_FRAG, "w", encoding="utf-8", newline="\n").write(fragment(html))
    n_io = {}
    for p, d in payload["pages"].items():
        for r in d["rows"]:
            n_io[r["io"]] = n_io.get(r["io"], 0) + 1
    n_ges = sum(len(d["gesture"]) for d in payload["pages"].values())
    layers = sorted({d["layer"] for d in payload["pages"].values()})
    print("written", OUT)
    print("written", OUT_FRAG, "（可内联片段）")
    print("[GATE] 页 %d 层 %s 控件 %d 手势边 %d 分类计数 %s"
          % (len(payload["order"]), layers,
             sum(len(d["rows"]) for d in payload["pages"].values()), n_ges,
             json.dumps(n_io, ensure_ascii=False)))
    assert all(k in n_io for k in ("in_read", "out_read", "in_write",
                                   "out_write", "nav")), "6 类里有一类没控件"
    assert_js(html)


def assert_js(html):
    """产出的页面脚本必须语法可解析：生成器写出坏页面 = 打开全白，比报错更坑。"""
    js = html.rsplit("<script>", 1)[1].rsplit("</script>", 1)[0]
    import subprocess
    import tempfile
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                         encoding="utf-8") as f:
            f.write(js)
            path = f.name
        r = subprocess.run(["node", "--check", path], capture_output=True, text=True)
        import os as _os
        _os.unlink(path)
        assert r.returncode == 0, "页面 JS 语法错误: " + (r.stderr or "")[:500]
        print("[GATE] 页面 JS 语法 OK（node --check）")
    except FileNotFoundError:
        print("[GATE] 跳过 JS 语法检查（本机没有 node）")


if __name__ == "__main__":
    main()
