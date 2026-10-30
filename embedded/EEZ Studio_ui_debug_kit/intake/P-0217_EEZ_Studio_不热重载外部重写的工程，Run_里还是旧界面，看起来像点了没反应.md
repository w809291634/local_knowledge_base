# P-0217 · EEZ Studio 不热重载外部重写的工程，Run 里还是旧界面，看起来像点了没反应

- **工程**：w78-tabview-smart-home
- **日期**：2026-10-30
- **工具**：Qoder
- **状态**：fixed
- **标签**：EEZ,Run,热重载,工程缓存,点击,验证
- **关联提示词**：PR-0397,PR-0398,PR-0399,PR-0400

## 现象（看到什么）

EEZ Studio 0.29 已打开 haven-home.eez-project；生成器在外部重写工程后，Run 里点按钮/侧栏/卡片没有按压反应，而同一份生成代码在 PC 仿真点击正常。

## 复现（怎么稳定重现）

Studio 进程 14:11 启动；工程 14:51/15:24 被外部重写；不关工程直接 Run，点 (367,230) 的“查看”无反馈；关闭工程标签后重开、再 Run 点击正常。

## 根因（真正的原因）

Studio 把工程模型缓存在内存，文件系统变更不触发重载，Run 仍用旧模型；另 no-flow Run 只执行 LVGL 原生反馈，不执行 native 跳转/硬件动作。

## 修复（做了什么）

生成器重写 .eez-project 后必须关闭工程标签再重开；批1 给每页 11 个侧栏 Tab、所有卡片、CONTROLS 标注行/按钮补 129 个透明原生按压层（默认 bg_opa=0，PRESSED 白色 14%），放在可见控件之下。

## 证据（数字 / 命令输出）

PC 仿真真实 SDL 按下命中侧栏 (8,138,60x38)、房间卡 (96,258,160x100)、按钮 (328,220,78x20)、窗帘卡 (96,124,680x104)，pressed 0→1→0；叠加前后静态 diff 0.0；用户重开工程后在 EEZ Run 验证 OK。

## 沉淀（新增断言 / 案例 / 文档）

NO_FLOW/FLOW §3.1 改正“重生成即生效”的表述；README 加 Studio 重开提示；按压证据与生成器快照已复制到 `intake/attachments/`（工程删除后仍可查）。


---

## 详细复盘（2026-10-30 补；工程可能删除，本节自包含）

> 附件（工程删除后仍保留）：`attachments/P-0217_press_check.png`（按压证据）、
> `attachments/P-0217_build_smart_home.py`（生成器快照，含 129 个按压层实现；依赖原仓库模板，仅作代码参考）。

### A. 工程与生成链（复现所需的最小上下文）

- 工程：`w78-tabview-smart-home`，800×480，EEZ Studio 0.29，**no flow**，批1 共 6 页：
  `home / rooms / living / lighting / climate / curtains`。
- 设计源：`design/design_source.py`（唯一真值）；EEZ 工程：`haven-home.eez-project`（生成物）。
- 生成/构建链：
  ```bat
  python design/design_view.py          :: 出设计图（非必需）
  python design/build_smart_home.py     :: 从设计源重写 .eez-project
  python design/cli_build.py            :: EEZ CLI 生成 src/ui
  python design/gen_font_batch1.py      :: 烘 14 档中文字体（CLI 会删已烘字体，必须在 CLI 之后）
  design\sim_cmake\run_sim.bat build    :: PC 仿真
  ```
- PC 仿真点击自证：`main.c` 临时支持 `SIM_PAGE / SIM_SHOT / SIM_CLICK / SIM_CX / SIM_CY`，
  用 `SDL_PushEvent` 发真实鼠标事件，遍历屏幕对象统计 `LV_STATE_PRESSED`，截图后撤掉探针。
- 关键事实：**`src/ui` 与 `.eez-project` 都是生成物**；人手改会被覆盖，改行为永远回设计源/生成器。

### B. 时间线（同一台机器，2026-10-30）

| 时间 | 事件 |
|---|---|
| 14:11 | 用户启动 EEZ Studio（主进程 15144），随后打开 `haven-home.eez-project` |
| 14:36 前后 | 生成器把批1 从“整页背景图 + 透明命中层”改为“装饰背景 + 可见原生控件/文本” |
| 14:51 | 生成器再次重写 `.eez-project`（修滑条百分数单位、kWh 位置） |
| 15:24 | 生成器再次重写（补 129 个侧栏/卡片/标注区透明按压层） |
| 15:2x | 用户在不关工程的情况下点 Run，仍无点击反应 |
| 15:3x | 用户关闭工程再重开，EEZ Run 点击反馈通过 |

**判据**：Studio 进程启动时间早于工程文件 mtime 半个多小时；期间工程被外部重写多次。
Studio 没有文件监听，Run 用的是打开时载入内存的旧模型——用户点的是旧版界面。

### C. 现象与稳定复现

现象（用户原话）：
- “为什么EEZ中点击run 没有按钮点击效果”
- “你仔细检查一下原因，为什么会这个样子，是父子关系错乱了吗”
- “EEZ 里面还是无法点击啊 ，什么情况”

稳定复现：
1. 在 EEZ Studio 打开 `haven-home.eez-project`（保持工程标签开着）。
2. 用生成器从外部重写同一个 `.eez-project`（文件 mtime 变化）。
3. 不关闭工程标签，直接点 Run；点按钮/侧栏/卡片均无按压或跳转。
4. 关闭工程标签，重新打开工程，再 Run；同样的点击出现按压反馈。
5. 对照：同一份生成代码用 PC 仿真点击正常（说明不是代码/控件树本身坏了）。

### D. 根因（四层，从直接触发到底层限制）

1. **工程模型缓存在内存（直接触发）**
   EEZ Studio 只在“打开工程”时解析 `.eez-project`；外部重写文件不会触发重载，Run 用内存里的旧模型。
   所以“改了没生效”不是生成器没写盘，而是 Studio 没读新盘。
2. **旧批的点击链被 Label 截走（旧模型无反馈的原因之一）**
   旧批按钮是透明命中层（`bg_opa=0`），且当时文字 Label 带 `CLICKABLE`。
   LVGL 命中测试取最上层可点对象：Label 在按钮之上，点击先给 Label；父按钮收不到
   `LV_EVENT_PRESSED`，又没有 PRESSED 样式，视觉上完全没反应。
   排查过父子/层叠顺序：`bg_*` 与 `c_*` 都是 screen 的直接子对象，背景先建、控件后建，**顺序正确**。
3. **侧栏/卡片是背景像素（新模型也会遇到的死区）**
   14:51 的版本只有 38 个原生交互件（10 按钮 + 12 开关 + 16 滑条）；侧栏 11 个 Tab、
   房间/场景/安防/能源等卡片仍是位图。点在像素上没有控件对象，天然不可能有反馈。
   15:24 补了 129 个透明原生按压层才覆盖这些区域。
4. **no-flow Run 不执行 native 跳转/硬件动作（能力边界）**
   no-flow 工程的事件绑定主要生成 C；EEZ Run 只跑 LVGL 原生反馈（按压/勾选/滑动），
   不执行 C 侧跳转与硬件调用。按压可以亮，但不会切页。
   跳转只能在 PC 仿真（真实 C）或固件里验；本仓库把这条写在 no-flow ⑦/⑤ 步。

### E. EEZ Run 的指针通路（排除“Run 根本不能点”）

查 `resources/app.asar`（EEZ Studio 0.29）确认：
- `project-editor/flow/runtime/wasm-runtime.js` 的 `WasmCanvas` 监听 `pointerdown/move/up/cancel`，
  把坐标换算成页面坐标后放进 `pointerEvents`，随 `worker.postMessage` 下发。
- `project-editor/flow/runtime/wasm-worker.js` 的 `createWasmWorker().postMessage` 对每条事件调用
  `wasm._onPointerEvent(x, y, pressed)`。
- `project-editor/lvgl/page-runtime.js` 的 `LVGLPageViewerRuntime` 用同一个 `worker.wasm`
  通过 `page.lvglCreate` 建对象；所以指针事件能进到页面对象。

结论：**输入通路不是问题**；问题在“页面模型是旧的 / 旧模型里没有可点对象或按压不可见”。
（asar 结构备忘：u32(0)=4，u32(12)=JSON 长度，JSON 从 offset 16 开始，payload 起点=16+JSON 长度。）

### F. 修复（可迁移的做法）

1. 流程修复（最重要）：生成器重写 `.eez-project` 后，在 EEZ Studio 里**关闭工程标签再重开**
   （或重启 Studio），再判 Run。只看“文件已更新”不够。
2. Label 不再抢点击：
   ```python
   # 生成器里所有文本 Label 只保留 GESTURE_BUBBLE，不带 CLICKABLE
   widget(key, "LVGLLabelWidget", x, y, w, h, "GESTURE_BUBBLE", ...)
   ```
3. 可见按钮显式写按压态：
   ```python
   parts={"PRESSED": {"bg_color": lighten(bg), "bg_opa": 255}}
   ```
   `lighten()` 把底色向白色混 18%，按压时明显变亮。
4. 背景死区垫透明原生按钮（129 个）：
   ```python
   def overlay_widget(key, box, radius):
       x, y, w, h = box
       return widget(key, "LVGLButtonWidget", x, y, w, h, BASE_FLAGS,
                     styles({"bg_color": "0xFFFFFF", "bg_opa": 0,
                             "radius": int(radius)},
                            parts={"PRESSED": {"bg_color": "0xFFFFFF",
                                               "bg_opa": 36,
                                               "radius": int(radius)}}))
   ```
   - 默认全透明，不改变静态画面；按下白色 14% 提亮。
   - 覆盖：每页 11 个侧栏 Tab、所有卡片、CONTROLS 标注的行/按钮/滑条。
   - **层序**：背景图 → 文本 Label → 透明按压层 → 可见原生控件。
     可见控件最后建，位于最上层，滑条/开关不会被按压层挡住。
5. 工程侧 README 写明：Studio 不热重载，重写工程后必须重开。

### G. 验证（数字）

- PC 仿真真实 SDL 鼠标按下，命中并进入 `LV_STATE_PRESSED`：
  - 侧栏 Tab：`(8,138,60×38)`
  - 房间卡：`(96,258,160×100)`
  - 原生按钮 `c_home_0`：`(328,220,78×20)`
  - 窗帘卡：`(96,124,680×104)`
  - pressed 计数 `0 → 1 → 0`，松开恢复。
- 叠加按压层前后静态首页逐像素平均差 **0.0**。
- 工程对账：6 屏 / 6 位图 / 14 字体 / 347 个对象 ID 唯一 / no flow；
  原生交互件 38 个 + 透明按压层 129 个 + 文本 Label 167 个。
- EEZ CLI 构建 `0 error / 0 warning`。
- **用户复核**：关闭并重开工程后，EEZ Run 点击反馈通过（2026-10-30，原话“现在基本对了……我在eez中验证OK”）。
- 证据图：`intake/attachments/P-0217_press_check.png`（侧栏 Tab / 房间卡 / 原生按钮 / 窗帘卡按下）。
- 生成器快照（工程删除后仍可复现按压层做法）：`intake/attachments/P-0217_build_smart_home.py`。

### H. 已落库的预防条款

- `EEZ_FIRST_WORKFLOW_NO_FLOW.md` §3.1：Run 吃工程模型；外部重写后必须关闭工程再重开（P-0217）。
- 同文件 §2 七步 ④ 内环：EEZ 画布/Run 核对前先关闭工程再重开。
- 同文件 §4 误区速查：“EEZ 里点不了”先重开工程；画布无输入，Run 只验原生控件反馈。
- 同文件 §2 验证分工表：no-flow 的跳转/硬件动作只能在仿真/固件核，Run 只验原生按压/勾选/滑动。
- `EEZ_FIRST_WORKFLOW_FLOW.md` §3.1 与默认链：`… → 烘字体 → 关闭工程重开 → EEZ 编辑器/Run 看一眼`。
- 本工程 README：批1 结果、重开提示、用户复核记录。
- 提示词留痕：PR-0397 / PR-0398 / PR-0399 / PR-0400 / PR-0401。

### I. 迁移/复用时先问自己

1. 生成器是不是刚重写过 `.eez-project`？→ 先关工程重开，再判 Run。
2. 点击点是不是落在背景像素/位图上？→ 看工程树里该坐标有没有可点对象；
   没有就垫透明原生 Button，或在设计阶段改成可见原生控件。
3. 点的是 Label 还是按钮？→ Label 不能带 `CLICKABLE`，否则会截走父按钮的 pressed。
4. 期待的是“按压反馈”还是“跳转/改硬件”？→ 后者 no-flow Run 不做，去仿真/固件验。
5. 透明按压层是否压在滑条/开关之上？→ 必须建在可见控件之前，保证 z 序更低。
