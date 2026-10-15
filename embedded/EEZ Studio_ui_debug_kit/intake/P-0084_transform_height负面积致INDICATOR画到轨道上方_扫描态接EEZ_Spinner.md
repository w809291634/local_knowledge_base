# P-0084 · 进度条「轨道上方一条蓝细线」= transform_height 收出负面积；搜索态转圈接 EEZ 原生 Spinner

- **工程**：小艺·智能屏 8（eez-test）/ LVGL 9.4 · 800×480（PC 仿真）
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：transform_height负面积,INDICATOR细线,MAIN pad收细,lv_spinner,EEZ W71,setslider命令,FAKE_SCAN_SEC临时加长
- **关联提示词**：PR-0108

> 补档说明（2026-10-03）：正文按 `index.md` 的 P-0084 行 +
> 工程日志 `.workbuddy/memory/2026-10-02.md`「第 99 轮（18:24-19:15）用户贴图反馈：
> 进度条状态不对 + 搜索要转圈动画（P-0084）」回填。

## 现象（看到什么）

用户贴两张截图反馈（原话：「进度条状态状态不对，搜索网络 需要有一个动画转圈圈，可以高级一点」）：

- 进度条：**轨道上方多了一条蓝色细线 + fill（进度填充）"消失" + 时间与进度视觉不符**；
- 音量条**同样中招**（fill 也在轨道上方 3px，之前目检漏了）；
- 扫描态只有一个静态圆环，没有转圈动画。

## 复现（怎么稳定重现）

走路器 `tapxy` 对 slider **无效**（只发 CLICKED，slider 的点击跳转不吃这个事件）→
本轮新增 `setslider <obj> <val>` 命令（`lv_slider_set_value` + `VALUE_CHANGED`，等价"拖到终态"），
把 slider 设到 48% 后做**像素分析**：knob 在 48% 的位置，但 INDICATOR 一个像素都没有
（fill 跑到了轨道上方）。

## 根因（真正的原因）

★ **P-0049 那套 `transform_height` 老技法的第二条致命副作用**（第一条是 P-0083 的"吃 MAIN 背景"）：

`lv_bar.c` 的 `draw_indic` 用 `lv_area_increase(..., transf_h)` 去收缩 `bar_coords`。
14px 高的控件上写 `transform_height = -9` → 高度收成 **-4（负数）**；内核 snap 回
`LV_BAR_SIZE_MIN = 4` 之后，**仍用那个负的 barh 去算中心** → INDICATOR 被画到**轨道上方 4px**，
成一条细线。于是用户看到"fill 没了 + 多一条蓝线 + 时间与进度不符"三件事同时出现。

**为什么以前没发现**：第 98 轮（P-0083）只验到"收缩生效 / 背景消失"，没做像素级对齐校验；
音量条那 3px 偏移也在平均值门禁的盲区里（对照门禁只看平均差异，单屏/单元素错位不报警 —— P-0032 早记过）。

## 修复（做了什么）

1. **彻底废除 `transform_height`**：INDICATOR 变细改走 **`LV_PART_MAIN` 的
   `pad_top` / `pad_bottom`**（内核 `indic_area` 本来就从 `bar_coords` 减 MAIN 的 pad，
   `lv_bar.c:361-364`），细度作为 extra 分配到 MAIN 的上下 pad。
2. **搜索态转圈 = EEZ 原生 W71 Spinner (LVGL)**（asar 挖证：该组件**无专有属性**；
   `lv_spinner_create` 的 constructor 自带 1000ms 旋转动画，`lv_spinner.c:93`）。接入三步：
   - `json2eez.py`：`TYPE_MAP` + `"spinner"`、`FLAGS` 表 + spinner（**无 CLICKABLE**）、
     `default_clickable` **排除 spinner**（防它挡住面板点击）；
   - `build_ui.py`：扫描态 `circle()` → **spinner 32×32**（MAIN 底弧 = TRACK 3px 半透明、
     INDICATOR 旋转弧 = ACCENT 3px 圆头）。
3. 走路器新增 `setslider` 命令（上面复现段说明的原因）。

## 证据（数字 / 命令输出）

- 修复后实证：**`fill_end=529` 紧贴 knob(530-553)**、时间 **01:54 = 48% × 238s** 完全同步、
  松手不弹回（seek 闭环 OK）。
- 动画实证：临时把 `FAKE_SCAN_SEC` 由 2s 改成 10s，**连拍 4 帧**，亮弧平均角
  **-10° → -18° → -37° → -25°** 逐帧变化 = 确实在转（验完已改回 2s）。
- 门禁：`all.py --sim` **PASS ×2**；设备侧 `_device_syntax_check.py` **4 文件 0 错 0 警**。
- 待用户：真机需 `idf.py build` 重烧才看到效果。
- 工具/环境坑（同轮实测）：`shot` 序号每命令 **+2**；walk 旧截图目录累计到 **50 个文件**会触发
  沙箱 `SAFE_DELETE_BULK_CONFIRM` 拦截（exit=1），清目录重跑即可；raw 快照解析必须走
  `sim.read_raw`（首行文本头 `w h stride cf` + BGRA 序），自己 `frombytes` 会通道错乱、全黑。

## 沉淀（新增断言 / 案例 / 文档）

- ★ **`transform_height` 判死**（连同 P-0083）：细指示条一律用 **MAIN pad** 收细，
  不要再往 bar/slider 的 MAIN 上写 transform_height —— 它会（a）吃掉 obj 背景绘制、
  （b）把 bar_coords 收成负面积后算错中心。
- ★ **P-0049 记的"KNOB 直径 = 控件高度 + pad 方向"结论本身没错**，错的是给它配了
  `transform_height` 这个实现手段；技法清单要连同"副作用"一起记，不能只记"生效"的那半。
- EEZ 原生能力优先：转圈这种动效用 W71 Spinner 直接给（0 行 native），
  与 P-0025/P-0030 的"EEZ 能原生表达的一律留 EEZ"铁律一致。
- 走路器补齐 `setslider`；MEMORY.md「仿真/验收」段的走路命令清单已含 `state` / `mousef` /
  `scan` / `disc`，`setslider` 属同族补充。
- 可加断言（本次未加）：像素级校验 INDICATOR 矩形必须落在 track 矩形内（防负面积复发）。
