# P-0060 · PC 仿真器统一适配范式：就地构建 + 引用源码 + 只改 CMakeLists 适配层

- **工程**：小艺·智能屏 8（eez-test）/ PC 仿真工作区
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：仿真,构建,CMake,适配层,引用编译,目录规范
- **关联提示词**：无

## 现象（看到什么）

用户要求：以后 PC 仿真统一用 v5.5.5 树那份 `common/PC_SIM/lv_port_pc_vscode_v9.5`，
**这个目录里的文件一律不改**（main.c / lv_conf.h / CMakeLists / FreeRTOS 子模块全是原样），
仿真内容全部**引用工程里的源码**编译。

旧做法（v5.4.1 树时代）：把仿真器 `copytree` 到 `%TEMP%/eez_sim_ui`，再把 `src/ui`、
`src/native` 拷进去 → 三份副本，改了工程源码忘了同步就是假绿（P-0057 就栽在这）。

## 复现（怎么稳定重现）

`python design/sim.py --walk=pwd` / `--walk=wifi` / `--walk=wifi_ok` / `--walk=wifi_retry`，
以及 `python design/all.py --shots`。

## 根因（真正的原因）

「仿真器是共享资源、工程才是真值」——把路径写死进仿真器内部就等于给仿真器加维护债。
正确形状是：**仿真器只暴露一个适配点（一个宏），其余路径都相对它推出来**。

## 修复（做了什么）

只改 PC_SIM 根目录 `CMakeLists.txt`（唯一适配层），其余文件零改动：

1. `TARGET_PROJ_DIR` = 被仿真工程根（`if(NOT ...)` 时按 `PROJECT_SOURCE_DIR/../../..` 兜底推导，
   换工程 `-DTARGET_PROJ_DIR=...` 覆盖），再往下推导出
   `UI_DIR=${TARGET_PROJ_DIR}/src/ui`、`NATIVE_DIR=.../src/native`、`SIM_MAIN_DIR=.../design/sim_cmake`。
2. `add_executable(main ${SIM_MAIN_DIR}/main.c + PC_SIM/main/src/mouse_cursor_icon.c + ${UI_SOURCES} + ${NATIVE_SOURCES})`
   —— GLOB **引用**工程源码，不复制。`NATIVE_SOURCES` 用 `list(FILTER ... EXCLUDE REGEX
   "(io_esp|test_native)")` 排掉真机后端与自带 main 的自测件。
3. 入口 main.c 与仿真用 lv_conf.h 都放**工程侧** `design/sim_cmake/`（仿真器只引用）：
   - `main.c` 由 `sim.py` 的 `write_main()` 生成（走路器在这里）；
   - `lv_conf.h` 由 `write_lvconf()` 从工程 `design/lv_conf.h` 加工裁剪而来。
4. `build/` 与 `bin/` 就落在 PC_SIM 目录下（它自带 `.gitignore` 已覆盖），不再搬去 %TEMP%。
5. `ui_debug_kit.config.json` 的 `sim.template_dir` → v5.5.5 树那份；`sim.lvgl_src` → 同树
   `APL/apl_lvgl_v9_4`（先确认同树已有 9.4 内核再拔掉跨树引用，否则「两份内核不同版本」）。
6. `sim.py` 删掉 `copy_ui()` / `copy_native()` / `WORK` 临时目录；`exe_stale()` 直接比工程
   `src/native` 与 `sim_cmake/main.c` 的 mtime。

## 证据（数字 / 命令输出）

- 四条走路链路在新链路上全通：`pwd`(2 图) / `wifi`(5 图) / `wifi_ok`(3 图) / `wifi_retry`(6 图)，
  末帧目检：直连成功 = HomeNet-5G 已连 192.168.1.23 + 「断开」；重试成功 = TP-LINK_8890 已连。
- `all.py --shots`：11 屏平均明显差异 **9.30%**（阈值 25%），无缺屏 —— 与旧链路的 9.31% 一致，
  说明「引用编译」没引入视觉差异。
- 工程侧只多了一个 `design/sim_cmake/`（main.c + lv_conf.h + CMakeLists.txt.orig 备份）。

## 沉淀（新增断言 / 案例 / 文档）

- 规则写进项目 `MEMORY.md`「仿真/验收」段：仿真器统一 v5.5.5 树 PC_SIM + 同树 apl_lvgl_v9_4，
  仿真器内除根 CMakeLists **零改动**，`src/ui` + `src/native` 全部引用编译。
- 自检手段：换工程只需 `-DTARGET_PROJ_DIR=`；仿真器自身文件 mtime 应始终是原始安装时间
  （除根 CMakeLists）。
