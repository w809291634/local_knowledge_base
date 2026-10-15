# P-0070 PC_SIM「目录协议」：换工程只改 TARGET_PROJ_DIR 一个宏

- 日期：2026-10-02
- 场景：PC 仿真器 `common/PC_SIM/lv_port_pc_vscode_v9.5`（该目录内除根目录 `CMakeLists.txt`
  外一律不改），要被**多个目标工程**复用。
- 问题：上一轮把适配层从 +139 行瘦身到 +32 行后，工程侧仍要手填 `UI_DIR` / `NATIVE_DIR` /
  `SIM_MAIN_DIR` / `APL_LVGL_DIR` / `SIM_H_RES` / `LV_*` 共 9 项 ——  user 要求"以后基本上
  只用改工程目录宏"。
- 结论：在仿真器根 CMakeLists 顶部立一条**目录协议**，只暴露 `TARGET_PROJ_DIR` 一个入口，
  其余全部自动推导 + 落 CACHE + 缺即 FATAL。

## 一、协议条款（写进 CMakeLists 顶部注释，即契约）

```
<TARGET_PROJ_DIR>/                 ← 唯一入口（cmake -DTARGET_PROJ_DIR= 或 sim_init.cmake）
  ├── src/ui/                       EEZ 生成代码（平铺 .c/.cpp，不是 lv_ui/ 子目录结构）
  ├── src/native/                   用户逻辑（platform/io_*.cpp，非 esp 的编进仿真）
  └── design/sim_cmake/             仿真接入点：main.c + lv_conf.h（工程侧持有）
LVGL 内核：自 <TARGET_PROJ_DIR> 逐级向上找 common/APL/apl_lvgl*（同树共用，跨工程自动命中）
仿真分辨率：<sim_cmake>/lv_conf.h → design/build_ui.py 的 SCREEN_W/SCREEN_H → 兜底 800x480
破例出口：任何一项都能单独 -D 覆盖（显式值优先于自动推导）
```

## 二、实现要点（四个坑）

1. **每个推导值都要 `set(X "${X}" CACHE ...)` 写回 CACHE**。
   apl_lvgl 是 `add_subdirectory` 子作用域，父作用域的普通变量它读不到（P-0066）；
   只在文件顶部"普通 set 定死"能过这一关，但换参数就废，所以统一走 CACHE。
2. **必须是目录 / 必须存在，缺就 `FATAL_ERROR`**。
   目录不存在时 `file(GLOB)` 会静默收空，configure 看着过、链接期才炸
   （"No SOURCES given to target" 那类），早失败早省事。报错里把"期望的路径 + 补救
   `-D 参数`"一次写全。
3. **解析循环要写向上探测的终止条件**：`while(NOT "/" AND ...)` 里必须判
   `get_filename_component(_pa _p DIRECTORY)` 是否原地不动（`/` 的父目录是自己），
   否则 Windows 上会死循环把盘符一级一级往上退。
4. **分辨率只能有一个真值源**。
   原来 `sim.py` 里 `SIM_H_RES=800` 和 `main.c` 里 `#define SIM_H_RES 800` 两份并存，
   改一处不生效是迟早的事（CACHE 变量≠编译宏，这条最容易踩）。
   现在：cmake 读目标工程 `design/build_ui.py` 的 `SCREEN_W/SCREEN_H`（=`string(REGEX)`
   读文件），再 `target_compile_definitions(main PRIVATE SIM_H_RES=...)`` 下传，
   main.c 里的同名 `#ifndef` 退成纯兜底。Python 侧那个常量一并删掉，避免第二真值源。

## 三、换工程的操作（用户视角，只需 1 行）

```python
# design/sim_cmake/sim_init.cmake（sim.py 自动生成，工程侧持有）
set(TARGET_PROJ_DIR "<新工程根>" CACHE PATH "目录协议入口：目标工程根（换工程只改这里）")
```
仿真器（PC_SIM）一行都不用碰；若新工程目录结构不是协议约定（比如 UI 在 `main/ui`），
二选一：改协议那三行 `src/ui`、`src/native`、`design/sim_cmake` 的拼接串，
或对这一项单独 `-DUI_DIR=...`。

## 四、验证清单

```bash
rm -rf PC_SIM/lv_port_pc_vscode_v9.5/build PC_SIM/lv_port_pc_vscode_v9.5/bin/main.exe
python design/sim.py --walk=pwd
```
configure 日志里必须看到 5 行 `[sim]` 自证：
```
[sim] 目录协议：工程 = ...
[sim]   UI_DIR      = .../src/ui
[sim]   NATIVE_DIR  = .../src/native
[sim]   SIM_MAIN_DIR= .../design/sim_cmake
[sim]   LVGL 配置   = .../sim_cmake/lv_conf.h  内核 = .../common/APL/apl_lvgl_v9_4
[sim]   仿真窗口    = 800 x 480
```
再 `grep -E "^(UI_DIR|NATIVE_DIR|SIM_MAIN_DIR|APL_LVGL_DIR|SIM_H_RES):" build/CMakeCache.txt`
确认这些是**自动推导落 CACHE** 出来的（不是工程侧喂进去的）。最后跑走路截图 + 设备侧
`_device_syntax_check.py`（本轮没动真机源码，顺手确认）。

## 五、附带的认识

- 「瘦身」和「目录协议」是两件事：瘦身是**位置**（配置放哪），协议是**形状**（换工程要
  改几行）。协议这部分完全不用 cmake 瘦身的 `-C` 初始缓存也能成立 —— 单纯 `-D` 传
  `TARGET_PROJ_DIR` 即可，但 CACHE 里留一份更利于 IDE 里查看/手改。
- 目录协议方法的通用性：任何"一个通用壳 + N 个具体工程"的构建模板，都值得先定一份
  **目录约定 + 自动推导 + 缺即 FATAL**，比"一堆可填参数"好用得多。
