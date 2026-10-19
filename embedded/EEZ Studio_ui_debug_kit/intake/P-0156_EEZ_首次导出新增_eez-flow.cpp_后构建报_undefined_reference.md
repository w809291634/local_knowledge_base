# P-0156 · EEZ 首次导出新增 eez-flow.cpp 后构建报 undefined reference（file GLOB 未刷新）

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_template
- **日期**：2026-10-19
- **工具**：Trae
- **状态**：fixed
- **标签**：EEZ,CMake,GLOB,reconfigure,undefined reference,构建坑,eez-flow.cpp
- **关联提示词**：PR-0261

## 现象（看到什么）

把 test.eez-project 用 EEZ Studio 从非 Flow 版重导出为 Flow 版（src/ui 新增 eez-flow.cpp / eez-flow.h）后直接 idf.py build，链接失败：undefined reference to eez_flow_init / eez_flow_tick / getFlowState / g_currentScreen（引用方是 ui.c.obj、screens.c.obj）

## 复现（怎么稳定重现）

EEZ Studio 导出到 eez-test/src/ui，不 touch 任何 CMake，直接 idf.py build

## 根因（真正的原因）

ui 组件用 file(GLOB) 收集 *.c / *.cpp，而 file(GLOB) 只在 CMake 配置期求值一次；EEZ 导出新增的文件出现在配置期之后，根本没进编译，结果只有旧对象参与链接

## 修复（做了什么）

任意触发一次 reconfigure：touch eez-test/src/ui/CMakeLists.txt 或删 build/ ，再 build 即通过；已在 ui/CMakeLists.txt 顶部注释写明 每次 EEZ 导出新增文件后先 touch 本文件

## 证据（数字 / 命令输出）

修复前 ld 报 libui.a(ui.c.obj): undefined reference to eez_flow_init / eez_flow_tick / getFlowState / g_currentScreen（计算上只有 5 条 全部来自这两个 obj）；touch CMakeLists 后 idf.py build 成功，binary 0x1172c0 bytes（86 percent free）

## 沉淀（新增断言 / 案例 / 文档）

已固化进工程 eez-test/src/ui/CMakeLists.txt 注释；可推广：任何用 file(GLOB) 收 EEZ 导出产物的工程都会踩同一坑
