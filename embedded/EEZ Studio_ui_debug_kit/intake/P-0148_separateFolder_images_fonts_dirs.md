# P-0148 · 图标/字体源码分目录：separateFolderForImagesAndFonts 与工具链路径联动

- **工程**：Design Watch（EEZ Studio 1.22 / LVGL 9.4，410×502）
- **日期**：2026-10-19
- **工具**：Trae
- **状态**：fixed
- **标签**：eez,构建产物,目录布局,separateFolderForImagesAndFonts,工具链路径,孤儿清理
- **关联提示词**：PR-0251 / PR-0252 / PR-0253

## 现象（看到什么）

EEZ 工程构建后 89 个 `ui_image_*.c` 与 7 个 `ui_font_*.c` 全部平铺在 `src/ui/` 根，
与 12 个头文件/核心文件（images.h / fonts.h / screens.c / ui.c …）混在一起，用户要求
"图标源码、字体源码分开目录管理，且只通过 EEZ 本身实现"。

## 复现（怎么稳定重现）

EEZ Studio → Settings → Build：`separateFolderForImagesAndFonts` 默认 `false` →
GUI Build 产出全部落 `destinationFolder`（`src/ui`）根。

## 根因（真正的原因）

EEZ **官方自带分目录开关**，不是没有设置。app.asar 反查证据：

- 图像写出路径 = `dest + (separateFolderForImagesAndFonts ? "images/" : "") + 名 + ".c"`
- 字体写出路径 = `dest + (separateFolderForImagesAndFonts ? "fonts/" : "") + "ui_font_" + 名 + ".c"`
- GUI 注册项 displayName："Store image and font files in a separate folder"（仅 LVGL 工程可勾）
- `images.h` / `fonts.h` 等 **build.files 模板清单文件不受影响，恒在根目录**；生成代码
  自包含（仅 `#include "lvgl.h"`），include 关系不变。

容易踩的点：**工程内工具链对产物路径有硬编码**。本项目 `eez_build.py` 的
`fonts_ready()` 硬编码字体落 `src/ui/` 根（P-0140 自愈链的判据）——不同步路径的话，
勾选后字体会被误判"未提取"而无限起 GUI；且 `watch.eez-project` 是生成器产物，
只在 GUI 勾选、不改生成器的话，下次重跑 `build_watch_ui.py` 会被覆盖回 false。

## 修复（做了什么）

1. **GUI 勾选** "Store image and font files in a separate folder"（用户定为所有工程默认推荐）。
2. **生成器持久化**：`design/build_watch_ui.py` build 设置处补
   `proj['settings']['build']['separateFolderForImagesAndFonts'] = True`（防重生成覆盖）。
3. **工具链同步**：`design/eez_build.py` `fonts_ready()` 校验路径 `src/ui` → `src/ui/fonts`，
   docstring 与 FONT-EXTRACT-INCOMPLETE 提示语同步。

## 证据（数字 / 命令输出）

勾选 + GUI Build 后实测：`src/ui/images/` 58 个 `ui_image_*.c`、`src/ui/fonts/` 7 个
`ui_font_*.c`、`src/ui/` 根 0 个散落产物；`fonts_ready() = True`；两脚本
`py_compile` 通过；工程 JSON 实测 `"separateFolderForImagesAndFonts": true`。

## 沉淀（新增断言 / 案例 / 文档）

- 推荐口径（用户 2026-10-19 定）：**所有 EEZ LVGL 工程默认勾选**该开关——构建产物
  按语义分目录（图标=images/、字体=fonts/），根目录只留头文件与核心文件。
- 启用检查单：① 勾选后立即跑一次 GUI Build 让文件迁移；② 生成器同步置位；
  ③ 全工程 grep `ui_image_*` / `ui_font_*` 硬编码路径（编译脚本 glob、字体校验、
  审计脚本）逐一同步；④ 仿真沙箱 CMake 若非递归 glob `src/ui/*.c`，需把子目录
  纳入源码清单（L3 出图前验证）。
