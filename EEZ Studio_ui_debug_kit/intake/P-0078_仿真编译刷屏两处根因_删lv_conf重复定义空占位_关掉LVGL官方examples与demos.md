# P-0078 仿真编译「警告刷屏」两处根因

- 日期：2026-10-02
- 现象：编译输出被
  `lv_conf.h:713: warning: "LV_FONT_CUSTOM_DECLARE" redefined`（附 705 行 previous definition）
  刷满屏，一个文件一条，看着像几百条。
- 用户原话：「这个警告这么多」

## 根因 1：lv_conf.h 里同一个宏定义了两遍

- 705 行 = **LVGL 官方模板留的空占位** `#define LV_FONT_CUSTOM_DECLARE`
- 713 行 = 我们（EEZ 烘焙字体）追加的实体声明
  `#define LV_FONT_CUSTOM_DECLARE extern const lv_font_t ui_font_ya_hei_consolas_hybrid_13;`

两份 lv_conf.h 都有（设计侧 `design/lv_conf.h` 是源头，仿真副本 `design/sim_cmake/lv_conf.h`
是 `sim.py:write_lvconf()` 从它加工来的，所以改源头两边一起好）。

**修法：删掉官方那行空占位**（`design/lv_conf.h`），换成 4 行说明为什么删。
安全性有内核保证：`apl_lvgl_v9_4/src/lv_conf_internal.h:1922` 有
`#ifndef LV_FONT_CUSTOM_DECLARE → #define LV_FONT_CUSTOM_DECLARE`（空值兜底），
所以删掉占位后**实体声明自动成为首次定义**，功能一模一样，只是少一条 redefinition。
（内核 `src/font/lv_font.h:341` 是 `#ifdef LV_FONT_CUSTOM_DECLARE` 后原样展开，靠的就是这个。）

## 根因 2：仿真在白编 LVGL 官方 examples / demos

`apl_lvgl_v9_4/env_support/cmake/os_desktop.cmake:33-34`：

```cmake
option(CONFIG_LV_BUILD_DEMOS    "Build demos" ON)
option(CONFIG_LV_BUILD_EXAMPLES "Build examples" ON)
```

仿真是 EEZ 自绘 UI，一个官方 example/demo 都不用，却把它们全编了 ——
**每个 example .c 都 include 一次 lv_conf.h，于是每条字体宏警告被复制若干次**，
这才是"警告这么多"的真正放大倍数（不是几百条独立问题，是一条 × N 个文件）。

**修法**（写进 PC_SIM 根 CMakeLists、**add_subdirectory 之前**，与 ThorVG 开关同批）：

```cmake
set(CONFIG_LV_BUILD_EXAMPLES OFF CACHE BOOL "仿真不需要 LVGL 官方 examples")
set(CONFIG_LV_BUILD_DEMOS    OFF CACHE BOOL "仿真不需要 LVGL 官方 demos")
```

⚠️ 沿用 P-0077 铁律：这类"给内核读的赋值"必须在 `add_subdirectory(${APL_LVGL_DIR})` 之前，
否则内核的 `option()` 已跑完，静默失效。

## 验证

- configure 阶段 `grep -i warning` 干净；CACHE 三开关齐 OFF
  （`CONFIG_LV_USE_THORVG_INTERNAL:BOOL=OFF` / `CONFIG_LV_BUILD_EXAMPLES:BOOL=OFF` /
  `CONFIG_LV_BUILD_DEMOS:BOOL=OFF`）
- 全新环境编译（先 `mv bin/main.exe` 再 `mv build`）：**exit=0，warning 数 = 0**
- `--walk=wifi_ok` 3 图、目检 `12_ok.png`：中文「无线网络 / 已保存 / 已连接」、
  WiFi 与信号图标、数字 IP 全部正常渲染（字体宏改动的最直接验收）
- 出图与改前一致（仍有 `can't open file for write !` 两条 = P-0077 记的
  `07b`/`09` 两张 16B PNG 头残片，既有问题）

## 方法论

1. **"警告很多"先算倍数再看条数**：一条 macro-redefined × N 个编译单元 = N 条。
   先问"这条警告是不是每个文件都来一份"，是的话优先砍编译单元数（关掉不需要的库），
   比逐条改写配置划算得多。
2. **改 lv_conf 优先动源头**：`design/lv_conf.h` 是唯一源头，仿真副本与真机同源派生，
   改一处两边生效，别直接改 `design/sim_cmake/lv_conf.h`（下次 `sim.py` 就覆盖回去了）。
3. 凡是 `option()/CONFIG_*` 开关，改完必须看 CACHE 确认落盘 —— 普通变量在
   add_subdirectory 之后设等于没设（P-0077）。
