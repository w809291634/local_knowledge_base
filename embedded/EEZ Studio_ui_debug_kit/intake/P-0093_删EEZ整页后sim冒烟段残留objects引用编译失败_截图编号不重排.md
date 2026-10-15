# P-0093 · 删掉 EEZ 整页后 sim.py 冒烟段残留 objects.m_* 引用，编译直接失败

- **工程**：p4_touch_lcd4_3_exp / lvgl_demo_ai / eez-test（AI 对话页 4 页删后两页）
- **日期**：2026-10-03
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：删页,EEZ生成区,仿真,编译错误,objects引用,截图编号
- **关联提示词**：PR-0114

## 现象（看到什么）

用户点单删掉「对话」tabview 4 页中的后两页（正在聆听 / 对话记录）。改完 DSL 跑
`python design/all.py --sim`，流水线**第一遍就编译失败**：

```
design/sim_cmake/main.c:391: error: 'objects_t' has no member named 'm_ai_orb'
```

同一轮还差点踩第二个坑：顺手想把 `sim.py` 的 `PAGES` 从
`01,02,05,06,...` 重编号成 `01,02,03,04,...`。

## 复现（怎么稳定重现）

1. `design/build_ui.py` 里删掉某个 tab 页（含页内所有 widget）；
2. 跑 `python design/all.py --sim`；
3. 只要 `design/sim.py` 生成 main.c 时还有**引用该页内对象的冒烟/走路段**，必编不过。

判据：`grep -n "objects\.m_" design/sim.py` 与 `src/ui/screens.h` 的对象表对照。

## 根因（真正的原因）

- **生成区是单向产物**：`build_ui.py` → `ui.json` → `json2eez.py` → EEZ CLI → `src/ui`。
  删页后 `objects_t` 结构体里该页对象**整体消失**，但 `sim.py` 里手写进 main.c 模板的
  C 代码是**另一条独立来源**，不会跟着自动删 → 悬空引用。
- 之所以容易漏：`sim.py` 的冒烟段（模拟用户点事件验证 action 通路）和被删页面是
  **弱耦合**——它引用对象名，但语义上属于"测试代码"，改 DSL 时视线不在那儿。
- **截图编号重排**是另一类同源错误：`build/sim_shots` 里的历史 PNG 文件名 + `compare.py`
  的 `MAP` + `build/verify_center.py` 的 `RAW_OF` + `icon_survey.py` 的 `VIEW_FILE`
  都**以文件名为键**。重编号 = 四处映射集体错位，而且是**静默**错位（不报错，只是
  比对到错的图 / 报缺屏），比编译错误更难查。

## 修复（做了什么）

1. `design/build_ui.py`（2868→2690 行）三处联动：
   - `ai_nav` 的 tab 定义与 children 只留 `ai_standby` / `ai_chat`（原 4 页）；
   - `pane_main()` 删「全部记录」按钮（原 p1，带 `switchTab`→tab 1），p2 平移补位；
   - 整段删 `pane_voice()` + `pane_history()` + `_WAVE`（175 行）。
2. `design/sim.py`：删掉引用 `objects.m_ai_orb` 的冒烟段（含
   `set_tv_layer(1, objects.m_ai_nav, 2)`），并写注释说明
   `action_voice_stop` 的 native 实现**保留为孤儿函数（无害）**。
3. **截图文件名故意不重排**，四处同步删项即可：
   `sim.py` 的 `PAGES`+`VIEWS`、`icon_survey.py` 的 `AI_TABS`/`VIEW_FILE`/`VIEW_NAME`、
   `compare.py` 的 `MAP`、`build/verify_center.py` 的 `RAW_OF`。

## 证据（数字 / 命令输出）

- 修复前后：编译 `error: 'objects_t' has no member named 'm_ai_orb'` → 全绿。
- 流水线：**9 屏**（原 11 屏）、平均差异 **9.08%**（阈值 25%）、无缺屏。
- `src/ui/screens.c` 对象表只剩 `m_tab_standby` / `m_tab_aichat`；
  `m_tab_aivoice` / `m_tab_aihist` 彻底消失（`grep` 零命中）。
- 生成区未手改自证：`ls -la --time-style=+%H:%M:%S src/ui/*` → EEZ 产物时间戳同秒
  `16:12:11`。
- 目检：`01_standby.png`「全部记录」已消失、「继续对话」贴右边缘无空隙；
  `02_ai_chat.png` 完好。

## 沉淀（新增断言 / 案例 / 文档）

- ★ **删页/删控件后的固定自检清单**（三步，缺一不可）：
  1. `grep -n "objects\.m_" design/sim.py` 对照 `src/ui/screens.h` 对象表查悬空引用；
  2. `grep -rn "被删对象名" design/*.py build/*.py` 查映射表残留；
  3. 跑 `python design/all.py --sim` 看编译 + 屏数 + 差异率。
- ★ **编号只删不排**：截图/页名/映射键一律"跳号保留"，注释写明「跳号无害，勿顺手整理」。
- 可加断言：`tools/` 里加一条 CHECK —— 扫 `sim.py` 生成的 main.c 中所有
  `objects.m_xxx`，逐一在 `src/ui/screens.h` 里校验存在（本次未加，留作后续）。
