# B13 主屏与 AppList 跨屏滑动导航（EEZ 原生 Tabview 隐藏栏形态）——手势管线的三环境输入粒度陷阱

> **检索别名**：跨屏滑动 / 左右滑切屏 / 手势返回 / 右滑返回 / Tabview 隐藏栏 /
> tab pager / 单屏 Tabview / 滑动导航 / 仿真器手势难触发。
> 下次说"两屏互滑""滑动导航"即指本案例这套方案。

> 前置：PLAYBOOK §5 场景 E（tab pager 先问后做）。本篇是它的 LVGL/EEZ 实装定稿：
> **跨屏滑动不要走手势管线、不要自建滚动容器，用原生 Tabview 隐藏栏**。

## 现象

410×502 腕表 UI：主屏（表盘）↔ AppList 两屏要左右滑动互切（主屏左滑进列表、
列表右滑返回）。初版用 LVGL 手势事件（`LV_EVENT_GESTURE`）判定右滑返回，出现
**环境不一致**：

- **EEZ Run 预览：右滑返回容易触发** ✓
- **PC 仿真器（lv_sdl_mouse）：右滑极难触发**，要滑得又快又长 ✗
- 修复仿真器后用户体验不佳，且担心真机（30ms 轮询读点）表现再偏。

## 证据

1. **LVGL 9.4 手势管线"低速清零"规则**（`lv_indev.c:1731` 附近）：每次读点
   `|v| < 3px` 即**清空**累计 `gesture_sum_x/y`；累计满 **50px** 才发
   `LV_EVENT_GESTURE`。两个常量硬编码，无 API 可调。
2. **三环境输入粒度实测**：
   - PC 仿真器 `lv_sdl_mouse`：SDL mousemove **逐事件直通**，每事件一读，
     粒度 1–2px → 手 slow 段反复命中"清零"，累计攒不满；
   - EEZ Run 预览：asar 取证 `lvgl_runtime_v9.4.0.js` = 真 LVGL 9.4.0 WASM，
     鼠标事件被**浏览器按帧合并**（~60Hz），粒度恰似真机 30ms 轮询 → 所以预览"正常"；
   - 真机：轮询读点（本项目 30ms）。
     **EEZ 预览正常 ≠ 内核没问题，更 ≠ 仿真器/真机正常。**
3. **手工"滚动容器 + 1×1 SNAPPABLE 锚"方案 kdbg 插桩实证**（最终被推翻的中间方案）：
   - 容器内只有一个吸附点时 `has_more_snap_points()`（`lv_indev_scroll.c:353-360`）
     数出 `sl=sr=-1` → 容器**永不成为滚动候选**，拖动完全无响应；
   - LTR 布局下左滚范围恒 0（`lv_obj_scroll.c:168-173`）——负坐标左溢出
     **不产生左滚范围**，右滑回上屏无路可走。
4. **事件驱动 sw_tab 桥**（tabview + 表达式绑定 + changeScreen）实证：
   `VALUE_CHANGED` 回写与组件派发顺序**无保证** → 桥触发失效。
5. **最终方案实测**：主屏右滑纹丝不动（死方向）、左滑整页进 AppList、
   AppList 右滑整页回主屏、列表纵向滚动 + 行点击**零回归**。

## 曾经的误判（按时间序，五条）

1. **SDL 事件过滤器节流**：以为"事件太密"是根因，加过滤器合并事件——失败。
   30ms 定时器零读点期间照样清零；问题不在事件密度，在**粒度与清零规则的耦合**。
2. **自建 30ms 轮询 indev**（仿真器 main.c 里自建读点设备）：有效，但这只是把
   仿真器粒度对齐真机的**环境补丁**，不解决设计面问题（真机手势仍难触发），
   且属于对输入形态的侵入，最终还原。
3. **手工"容器 + 锚"滚动方案**：以为 tabview"太重"，自建吸附容器——单吸附点
   永不候选 + LTR 左滚范围恒 0，双重死刑（见证据 3）。
4. **事件驱动 tab 切换桥**：以为滑动能用"滚动检测 + changeScreen"桥出来——
   派发顺序竞态，不可靠（证据 4）。
5. **最根本的**：把"跨屏滑动"当成**手势识别问题**去修。它其实是**滚动吸附问题**
   ——换到滚动管线（Tabview）后，手势管线的全部坑消失。

## 真因

跨屏切换需要的是**有真实滚动范围的吸附容器**，不是手势事件。LVGL 的
`lv_tabview` 原生机制（`lv_tabview.c:344-373`）：页容器带 `SNAP_CENTER` 吸附 +
滚到 `SCROLL_END` 自动翻页——整条链走**滚动管线**，与输入粒度无关，
SDL 逐事件 / WASM 帧合并 / 真机轮询三环境行为一致。手势管线方案在任何
输入粒度不齐的环境里都不可移植。

## 修法（建立方式，逐步复刻）

唯一设计源 `build_watch_ui.py`（EEZ 工程由脚本直出 JSON）。**零 flow 桥、
零内核修改、零 C 侧补丁**：

**① 建 Tabview（隐藏栏形态）**

```python
# tabviewPosition=TOP、tabviewSize=0（隐藏 tab 栏）、selectedTab=0 字面量。
# selectedTab 用字面量是因为 tabview 自带状态记忆：从功能页 changeScreen(Dial)
# 返回时自然落在用户离开的那个 tab，无需任何变量/动作。
swp = w('tabview', 0, 0, W, H, ident='tv_Dial',
        tabviewPosition='TOP', tabviewSize=0,
        selectedTab=0, selectedTabType='literal',
        children=[t0, t1])
```

**② Tab 页 widgetFlags 三件套（每一条都是踩坑实录）**

```python
# 保留 SNAPPABLE：tab 页没有吸附点 = 拖动完全失效（参照工程 README 踩坑 #2）；
# 去 SCROLL_ELASTIC / SCROLL_MOMENTUM：p0 右滑是死方向（左侧无页），
#   带弹性会出现橡皮筋拖动；去掉后死方向纹丝不动，左滑有真实整页范围不受影响。
_tv_flags = ('CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|'
             'SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_WITH_ARROW|SNAPPABLE')
t0['widgetFlags'] = _tv_flags
t0['flagScrollbarMode'] = 'OFF'
```

**③ Tab 页显式 ZERO_PAD（不居中的根因）**

`lv_tabview_add_tab` 建出的 tab 页无 pad 样式时会**继承主题默认 pad（~13px）**
→ 整页右移。必须显式清零：

```python
t0['localStyles']['definition'] = merge(style(**NO_PAD, bg_opa=0))
```

**④ AppList 独立屏退役，内容并入 Tab p1**

- 内容函数只产出 `list_scroll` 节点（滚动容器 + 行 + 磁吸锚），作为
  `t1['children']`；
- `PAGES` 删 AppList 条目（36 屏）；仿真快照表删 `02_AppList`
  （对象树上它 = `01_Dial` 同源，重复快照无意义）。

**⑤ 导航表同步（两处兜底）**

- `page_gestures()`：功能页右滑返回的 `'AppList'` 全部改指 `'Dial'`
  （返回落在用户离开的 tab，符合直觉）；
- `build()` goto 循环：`if target == 'AppList': target = 'Dial'`。

**⑥ 滚轮动效链随迁**：AppList 的 wheel_flow / clock_flow 挂到 Dial 分支
（内容在哪个屏，flow 就在哪个屏）。

**⑦ 清理干净**：swipe_flow / SWIPE_* 常量 / sw_tab 桥整段删除；
孤儿审计（未引用 actions、悬空连线、陈旧白名单）归零。

**禁改清单**：LVGL 内核源码；EEZ 工程核心逻辑；Tab 页 SNAPPABLE（见了就想删——删了就滑不动）。

## 验证

主链全绿（可复现）：

1. 生成 → EEZ headless 构建 **0 错 0 警**；
2. `nav_audit.py` PASS（36 屏 / 70 边 / 0 错误）、`check_nav.py` PASS
   （72 条导航链 / 0 死链）；
3. 像素测量：表盘 num12 中心 x=202（设计 205；ZERO_PAD 修复前偏 +13）；
4. PC_SIM 实测四项：主屏右滑纹丝不动 / 左滑整页进列表 / 列表右滑整页回 /
   列表滚动与行点击零回归；
5. EEZ Run 预览行为一致（这次是真的一致——机制与输入粒度无关）。

## 通用化

- **EEZ/LVGL"两页互滑"选型定则**：原生 Tabview（隐藏栏）＞ 手势管线 ＞ 自建
  滚动容器（基本不可行：单吸附点永不候选 + LTR 左滚范围 0）。多页（≥3）同理，
  Tabview 原生支持。
- **Tab 页三件套口诀**：`SNAPPABLE` 保留 / `ZERO_PAD` 显式 / 死方向去弹性。
  隐藏栏 = `tabviewSize=0`；返回落在离开页 = `selectedTab` 字面量 0 起步 + tabview
  自带状态记忆。
- **输入粒度三环境定理**：凡是依赖"输入事件粒度"的交互（手势、惯量、长按判定、
  惯性甩动），SDL 逐事件直通 / WASM 帧合并 / 真机轮询三种环境行为**必然不同**
  → 仿真器验证结论不可信。要么选粒度无关机制（滚动管线、状态机、原生控件），
  要么真机实测定案。**"EEZ 预览正常"永远不构成"功能正常"的证据。**
- 跨栈对照：Web 前端 scroll-snap + 轮播组件 vs 手写 touch 事件——同样是
  "优先用平台的吸附/分页机制，不手写手势阈值"，原因同源（触控板/鼠标/触摸屏
  的事件粒度不可对齐）。
