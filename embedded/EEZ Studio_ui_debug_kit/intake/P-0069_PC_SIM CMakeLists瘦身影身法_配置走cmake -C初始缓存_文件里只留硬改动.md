# P-0069 PC_SIM CMakeLists 瘦身影身法：配置走 `cmake -C` 初始缓存，文件里只留硬改动

**日期**：2026-10-02
**现象**：把仿真适配层塞进 `common/PC_SIM/lv_port_pc_vscode_v9.5/CMakeLists.txt` 后，
文件从 240 行涨到 349 行（`git diff` = **+139 / −30**），用户当场质疑"改动怎么这么大"。
**结论**：新增里 47% 是纯踩坑注释；真正的新增代码约 70 行，其中只有 ~20 行**必须**留在
PC_SIM 里，其余全能用 cmake 命令行/初始缓存从**工程侧**注进来。已按此瘦身到
**+32 / −11（271 行）**。

## 一、先分类：哪些改动真的必须留在 PC_SIM

| 改动 | 必须留？ | 原因 |
|---|---|---|
| `file(GLOB_RECURSE UI_SOURCES "${UI_DIR}/lv_ui/*.c" "${UI_DIR}/lv_interface/*.c")` | ✅ 是 | 目标工程是 EEZ **平铺**布局（`src/ui/*.c`），原 GLOB 指向不存在的子目录 → **静默收空**，不报错但链接期炸 |
| `NATIVE_SOURCES` 收集 + `FILTER` 掉 `io_esp`/`test_native` | ✅ 是 | io_esp 要 `esp_*/freertos`，test_native 自带 main |
| `set(APL_LVGL_DIR "${PROJECT_SOURCE_DIR}/../../APL/apl_lvgl")` 写死普通变量 | ✅ 是（改 1 行） | 它会在 `add_subdirectory` 前**把 -D 传进来的值盖掉**，且旧目录名已不存在 → 改成 `set(APL_LVGL_DIR "${APL_LVGL_DIR}" CACHE PATH "")` |
| `add_executable` 入口 `${PROJECT_SOURCE_DIR}/main/src/main.c` → `${SIM_MAIN_DIR}/main.c` + `${NATIVE_SOURCES}` | ✅ 是（2 行） | 两个 main() 会重定义；工程入口由 `SIM_MAIN_DIR` 变量提供 |
| `target_link_libraries(... m pthread)` | ✅ 是（改 WIN32 分支） | `m`/`pthread` 是 POSIX 库名，Windows 翻成 `m.lib`/`pthread.lib` 根本不存在；`lvgl::examples/demos/thorvg` 在关掉 `CONFIG_*` 后也不存在 |
| `target_include_directories` 里 `${UI_DIR}/lv_ui{,/pages}`、`${UI_DIR}/lv_interface` | ✅ 是（压成 1 行） | 平铺后都是不存在的路径，且缺 `${NATIVE_DIR}` |
| **ThorVG 源文件屏蔽**（`HEADER_FILE_ONLY`） | ✅ 是（~8 行） | lvgl 的 `file(GLOB_RECURSE src/*.cpp)` 无条件收 `libs/thorvg/*.cpp`，而 `config.h` 只有它自己的构建才生成；必须在 `add_subdirectory` 之后、`lvgl` target 存在时才改得动 source 属性 |
| 目标工程路径探测、UI_DIR/NATIVE_DIR/SIM_MAIN_DIR 定义、存在性断言 | ❌ 可搬 | `-C` 初始缓存 / `-D` 全搞定 |
| `LV_BUILD_CONF_DIR/PATH`、`LV_CONF_PATH` | ❌ 可搬 | 同上 |
| `APL_LVGL_DIR`、分辨率 `SIM_H_RES/SIM_V_RES` | ❌ 可搬 | 同上 |
| 全部踩坑注释（61 行） | ❌ 可删 | 内容已沉到 intake |

## 二、手段：`cmake -C <初始缓存>` 才是正确形态

```cmake
# 由 design/sim.py 生成 -> design/sim_cmake/sim_init.cmake
set(UI_DIR "<proj>/src/ui" CACHE PATH "...")
set(NATIVE_DIR "<proj>/src/native" CACHE PATH "...")
set(SIM_MAIN_DIR "<proj>/design/sim_cmake" CACHE PATH "...")
set(APL_LVGL_DIR "<sim_root>/../../APL/apl_lvgl_v9_4" CACHE PATH "...")
set(SIM_H_RES 800 CACHE STRING "...")   # 仿真窗口 = 真机 LCD 分辨率
set(SIM_V_RES 480 CACHE STRING "...")
set(LV_BUILD_CONF_DIR "" CACHE PATH "")                       # 必须置空，否则与 PATH 同在会 FATAL
set(LV_BUILD_CONF_PATH "<proj>/design/sim_cmake/lv_conf.h" CACHE PATH "...")
set(LV_CONF_PATH       "<proj>/design/sim_cmake/lv_conf.h" CACHE PATH "...")
```
```python
cmake -S <PC_SIM> -B <PC_SIM>/build -C <proj>/design/sim_cmake/sim_init.cmake ...
```
**为什么是 `-C` 而不是"在父作用域 set 普通变量"**：apl_lvgl 是 `add_subdirectory` 出来的
**子作用域**，父作用域的普通变量它读不到（P-0066：实测读到空字符串，于是静默回落
"Using lv_conf.h from the top-level project directory"）。而 `-C` 在**顶层 CMakeLists
之前**就把 CACHE 落地，子作用域一定能读到。cmake 命令行 `-D` 同样可行，但一堆 `-D`
拼 Windows 绝对路径要转义，且旧 build 目录复用时不生效；`-C` 只在一句话里放一个文件。

**为什么必须写 CACHE 而不是普通 set**（两条都堵）：
1. 子作用域读不到父的普通变量（P-0066）；
2. 历史 `CMakeCache.txt` 里若已有空值的 CACHE，`if(LV_BUILD_CONF_PATH)` 就是假，
   会悄悄退回仿真器根目录那份原始 lv_conf（ThorVG=1 / FS_STDIO=1，PC 上必挂）。

## 三、踩到的新坑（本次才发现的）

- **L124 那行 `set(APL_LVGL_DIR "${PROJECT_SOURCE_DIR}/../../APL/apl_lvgl")` 是无 CACHE 的
  普通 set**，位置在 `add_subdirectory` 之前，正好盖掉 `-D` 传进来的值 → 只靠命令行
  **不够**，这一行必须改成 CACHE 形式，否则 add_subdirectory 直接失败。
  这条比"父作用域普通变量传不进子作用域"（P-0066）更隐蔽，因为它不需要子作用域也能触发。
- `message(STATUS "[sim] LVGL 配置 = ${LV_BUILD_CONF_PATH}  内核 = ${APL_LVGL_DIR}")`
  建议**保留**：瘦身删掉了那套长注释，唯一能自证"注入命中"的就是 configure 期这一行。

## 四、瘦身后的责任边界

- **PC_SIM 目录**：除根 `CMakeLists.txt` 外零改动；该文件只留 ~20 行硬改动（代码 ~19 行
  + 注释 13 行），换工程一行都不用动。
- **工程侧 `design/sim_cmake/` 三件套**（全部由 `design/sim.py` 生成，随工程走）：
  `main.c`（仿真入口）、`lv_conf.h`（真机配置剪一刀）、`sim_init.cmake`（本次新增，
  CMake 初始缓存）。换工程 = 改这边的工程根路径。

## 五、验证清单（改完必跑）+ 实测结果

1. 把旧 `build` 目录改名造全新 `CMakeCache.txt`（`-C` 只在首次 configure 生效，
   不造新环境测不出问题）；
2. configure 日志里确认出现 `[sim] LVGL 配置 = .../design/sim_cmake/lv_conf.h 内核 = .../apl_lvgl_v9_4`；
3. `design/sim.py --walk=pwd` / `--walk=wifi_ok` 走路截图全通；
4. `design/_device_syntax_check.py` 绿（本轮没动真机源码，但顺手确认）。

**实测（2026-10-02）**：
- ① `build/CMakeCache.txt` 里 8 项注入值全部命中：`UI_DIR/NATIVE_DIR/SIM_MAIN_DIR`
  → 工程路径、`APL_LVGL_DIR` → `apl_lvgl_v9_4`、`SIM_H_RES=800`、`SIM_V_RES=480`、
  `LV_BUILD_CONF_PATH` = `LV_CONF_PATH` = 工程侧 `sim_cmake/lv_conf.h`、
  `LV_BUILD_CONF_DIR` 为空（未触发双非空 FATAL）。
- ②③ 全新 build 目录全量编译 `EXIT=0`（3m54s，mingw gcc，clang 那条线未复测），
  `pwd` 2 图 / `wifi_ok` 3 图走路全通；④ `_device_syntax_check.py` 四个文件 0 错 0 警。
- ⚠️ 过程中两次"假绿"：一是 `exe_stale()` 判定源码不比 exe 新就**跳过编译**，
  移走 `build/` 并不会让 exe 失效，瘦身后的 CMakeLists 一次都没被编译验证
  （见 P-0070）；二是首次 `make -j12` 在 4% 处报 `Error 2` 且**没有任何错误行**
  （子进程被外部掐掉），手动 `make -j12` 重跑 `EXIT=0` → 属偶发，不是配置问题，
  但**验证时必须看到 `[100%] Built target main` 才算真过**。
