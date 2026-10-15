# P-0061 · LVGL 配置注入只能走 LV_BUILD_CONF_PATH，且必须是普通变量（DIR 分支会静默回落）

- **工程**：小艺·智能屏 8（eez-test）/ PC 仿真
- **日期**：2026-10-02
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：CMake,LVGL配置,lv_conf,ThorVG,FS_STDIO,静默回落
- **关联提示词**：无

## 现象（看到什么）

第一次在 v5.5.5 树编译 PC 仿真：

```
src/libs/thorvg/tvg*.cpp: fatal error: 'config.h' file not found      （一堆 Error 2）
src/libs/fsdrv/lv_fs_stdio.c: fatal error: 'dirent.h' file not found
```

两者都是「内核按默认配置把相关源文件编进来了」。工程侧仿真 `lv_conf.h` 里
`LV_USE_THORVG_INTERNAL 0 / LV_USE_VECTOR_GRAPHIC 0 / LV_USE_FS_STDIO 0` 都写着，就是不生效。

## 复现（怎么稳定重现）

`LV_BUILD_CONF_DIR` 指目录（而不是 PATH）时必现；或者 `LV_BUILD_CONF_PATH` 写成 CACHE
变量且已被历史 configure 落成空值后，再设非空也会命中 `os_desktop.cmake:40` 的
`FATAL_ERROR "can not use LV_BUILD_CONF_DIR and LV_BUILD_CONF_PATH at the same time"`。

## 根因（真正的原因）

apl_lvgl 的 `env_support/cmake/os_desktop.cmake` 只有两条支路：

- `LV_BUILD_CONF_PATH` → 定义 `LV_CONF_PATH="<文件本体>"` 宏，编译期
  `lv_conf_internal.h` 走 `#ifdef LV_CONF_PATH → #include LV_CONF_PATH`，**真正用上工程那份 lv_conf**；
- `LV_BUILD_CONF_DIR`（只指目录）→ 只定义 `LV_CONF_INCLUDE_SIMPLE`，
  `lv_conf_internal.h` 的优先级是 `LV_CONF_PATH` > `LV_CONF_INCLUDE_SIMPLE`，
  于是回落到 `#include "lv_conf.h"` → CMAKE_SOURCE_DIR 那份 **PC 仿真器根目录原始模板**
  （THORVG=1 / FS_STDIO=1）→ PC 上必挂。

而 PC_SIM 根目录那份原始 `lv_conf.h` 恰恰就是 THORVG=1、FS_STDIO=1 的"PC 模板"，
FS_STDIO 要 `dirent.h`、ThorVG 要只有它自己的 cmake 才生成的 `config.h`。

**为什么容易踩**：两个变量如果都写成 `CACHE`，历史 configure 一旦落成空值，
`if(LV_BUILD_CONF_PATH)` 就是假，悄悄退回 DIR 分支甚至退回根目录模板，编译报错信息
（缺 config.h / dirent.h）离病根很远。

## 修复（做了什么）

在 PC_SIM 根 CMakeLists 的适配层里：

```cmake
set(LV_BUILD_CONF_DIR "")                                  # 普通变量压掉历史 cache
set(LV_BUILD_CONF_PATH "${SIM_MAIN_DIR}/lv_conf.h")        # ★ 普通变量，不是 CACHE
set(LV_CONF_PATH "${SIM_MAIN_DIR}/lv_conf.h" CACHE PATH "Shared LVGL config header")  # 仅供人读
# 保留 target_compile_definitions(main PRIVATE LV_CONF_INCLUDE_SIMPLE) 无妨：
# lv_conf_internal.h 里 PATH 分支优先于 INCLUDE_SIMPLE 分支。
```

apl_lvgl 是被 `include`/`add_subdirectory` 进来的**子作用域**，父作用域的**普通变量**子作用域
可见 → 普通变量一定能传到；CACHE 变量反而会被历史值钉死。

另外 `build()` 每次都重新 `cmake` configure（1~2 秒）：源文件清单和「LVGL 编哪些源码」都是
configure 期定死的，照时间戳猜会编出上轮那份（假绿）。

工程侧 `write_lvconf()` 保证仿真用 lv_conf 是裁剪版：
`LV_USE_SNAPSHOT=1`、LOTTIE/THORVG_INTERNAL/VECTOR_GRAPHIC/ASSERT_MEM_INTEGRITY/ASSERT_STYLE/ASSERT_OBJ=0、
`LV_USE_FS_STDIO=0`（clang 无 dirent.h，且 UI 全量 grep `lv_fs_` 零命中，纯内嵌图）、
`LV_USE_STDLIB_MALLOC` 从 BUILTIN 改 CLIB。

## 证据（数字 / 命令输出）

改完这两处后 ThorVG / fsdrv 的 config.h、dirent.h 报错**一次性消失**，且 `screens.c` 等
EEZ 产物能正常编过 —— 证明工程侧仿真 lv_conf 确实进了编译期（不是恰好少编了源文件）。

## 沉淀（新增断言 / 案例 / 文档）

- 「屏蔽 ThorVG 源文件」那条思路（`set_source_files_properties(... HEADER_FILE_ONLY TRUE)`
  设在父作用域）**无效**：lvgl target 定义在 apl_lvgl 子目录里，父作用域管不到已展开的
  SOURCES。别再从这条路上找补，从配置源头关掉才对。
- 用 `LV_CONF_PATH` 优先级（`lv_conf_internal.h:54-57`）作为判据：只要报错变成别的，
  就说明配置真的生效了。
