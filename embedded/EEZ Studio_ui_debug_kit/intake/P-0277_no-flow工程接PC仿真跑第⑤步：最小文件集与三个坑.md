# P-0277 · no-flow 工程接 PC 仿真跑第⑤步：最小文件集与三个坑

- **工程**：多参数监护仪 UI（multipara_monitor_ui）
- **日期**：2026-11-08
- **工具**：Trae
- **状态**：fixed
- **标签**：第⑤步,PC仿真,导航闭环,C,B2,no-flow
- **关联提示词**：PR-0626

## 现象（看到什么）

纯 EEZ 生成代码的工程（只有 `src/ui`）无法直接跑第⑤步：没有仿真入口，也
没有 `action_nav_goto` 实现，链接期报 `undefined reference to action_nav_goto`。

## 复现（怎么稳定重现）

把只含 `src/ui` 的 no-flow 工程接到 `PC_SIM/lv_port_pc_vscode_v9.5`，
指定 `SIM_TARGET_PROJ_DIR` 后构建：前面的编译全部通过，最后链接失败。

## 根因（真正的原因）

PC_SIM 只提供宿主与 LVGL，工程必须自带四样：
`design/sim_cmake/main.c`（入口）、`design/sim_cmake/lv_conf.h`、
`design/sim_cmake/run_sim.bat`（注入 `SIM_TARGET_PROJ_DIR` / `SIM_BIN_DIR`）、
以及 native 侧的跳转回调实现。EEZ 的 action 声明是 `implementationType=native`，
只生成调用，不生成实现。

## 修复（做了什么）

- `design/sim_cmake/main.c`：`lv_init → hal_init(SDL) → ui_init`；
  `MON_AUTOTEST=1` 时逐屏 `loadScreen` 出 B2 截图，再按边表注入真实 SDL 鼠标事件
  （`MOUSEMOTION → UP → DOWN → UP`，`windowID=0`），断言 `lv_screen_active()`。
- `src/native/nav_actions.c`：唯一回调 `action_nav_goto(lv_event_t*)`，
  `userData`（页索引 0 起）→ `loadScreen(idx+1)`。
- `design/gen_sim_nav.py`：从 `design_source.json` 派生 `sim_nav.h` 边表与
  `sim_page_obj()`，不手写第二份跳转真值。
- `design/b2_check.py`：B2（`build/b2/*.bmp`）↔ B1（`build/b1/*.png`）互证。

## 证据（数字 / 命令输出）

- 构建：`run_sim.bat build` 成功，exe 落在工程私有 `design/sim_cmake/build_rel/bin`。
- C：43/43 PASS（逐边真点击，含隐藏热区控件）。
- B2：14 张；与 B1 互证平均 **98.72%**，最低 main 98.14%。

## 沉淀（新增断言 / 案例 / 文档）

- 第⑤步最小文件集：`sim_cmake/{main.c,lv_conf.h,run_sim.bat}` + `src/native/nav_actions.c` + 派生边表脚本。
- 三个坑：
  1. `action_nav_goto` 必须由 native 实现，否则链接失败；
  2. 运行时需要 SDL2 dll 在 PATH（`setup_env.bat` 负责）；
  3. B2 截图路径相对进程 cwd，跑 AUTOTEST 要先把 cwd 设到工程根。
