# B23 UI 占用实测（把 UI 部署进 P4 模板编译 + ui_size_report）

> **检索别名**：UI 占多少空间 / 固件多大 / flash 占用 / 图片占空间 / 精灵帧太大 /
> rodata 6MB / app.bin 大小 / ui_size_report / idf.py size / 部署到 P4 模板 /
> 估算 UI 体积 / 4MB flash 放不下 / 压缩图片 / ARGB8888 占用。

**一句话**：UI 体积只认**最终链接结果**，不认源码求和、更不认 .a 磁盘大小；
在 P4 模板里编一遍 + 跑工程自带的 `ui_size_report.py`，一次给全（分组/逐文件/RAM）。

## 前提

- 本机 P4 模板：`D:\esp32_8266_files\esp-idf-v5.5.5_ol\examples\idf_v555_my_exps\p4_touch_lcd4_3_exp\lvgl_demo_template_no_flow`
  （32MB flash / 8MB OTA app 分区；`eez-test/src`＝EEZ 组件根，内含 `ui/` 与 `native/`；自带 `ui_size_report.py`）。
- **模板不在本机时，先请用户提供同板型示例工程**（或至少告知 flash 分区），别拿源码求和冒充固件占用。
- 工具链：IDF 5.5.5 + `D:\esp32_8266_files\esp-idf-tools_for_idf_v5_5_5`
  （`export.bat` 在 Git Bash 里会报 "for Windows CMD.EXE shell only"，直接写 bat 设环境最稳）。

## 步骤（可复制）

1. **备份**目标工程：`mv eez-test/src/ui eez-test/src/ui_template_backup`、`cp main/main.c main/main.c.bak`。
2. **拷入被测 UI**：`cp -r <工程>/src/ui eez-test/src/ui`；
   ★ 必须把备份里的 `CMakeLists.txt`（EEZ 导出的 GLOB_RECURSE 版）**拷回新 ui 目录**，否则 cmake 报
   `Failed to resolve component 'ui'`。
3. **关掉模板自带的 demo**：`main.c` 里 `APP_RUN_LV_DEMO 1 → 0`（保留 `APP_ENABLE_EEZ_UI 1`）。
4. **构建**（写 `_build.bat`，不要依赖 export.bat）：
   ```bat
   @echo off
   set MSYSTEM=
   set IDF_PATH=D:\esp32_8266_files\esp-idf-v5.5.5_ol
   set IDF_TOOLS_PATH=D:\esp32_8266_files\esp-idf-tools_for_idf_v5_5_5
   set PATH=%IDF_TOOLS_PATH%\tools\riscv32-esp-elf\esp-14.2.0_20260121\riscv32-esp-elf\bin;%IDF_TOOLS_PATH%\tools\ninja\1.12.1;%IDF_TOOLS_PATH%\tools\cmake\3.30.2\bin;%IDF_TOOLS_PATH%\python_env\idf5.5_py3.11_env\Scripts;%PATH%
   "%IDF_TOOLS_PATH%\python_env\idf5.5_py3.11_env\Scripts\python.exe" "%IDF_PATH%\tools\idf.py" --no-hints build
   ```
5. **出报告**：`<IDF python> ui_size_report.py > size_report.txt`（读 `build/*.map` 交给 `esp_idf_size`
   出**最终链接后**的分组/逐文件/RAM；自动从 build/CMakeCache 找 python）。

## 判读口径

- app.bin 是**烧写大小**；分组表里 "EEZ 生成 UI" 才是 UI 成本；`.a` 磁盘大小含调试符号，不能当结论。
- 图片在 flash 里是**未压缩原始像素**：ARGB8888＝`w×h×4` 字节/帧（60×60＝14.1KB）。
  `.eez-project` 里的 2.5MB 是 PNG base64（压缩态），构建后展开进 rodata——别拿它当占用。
- 常用压缩对照：ARGB8565（3B/px，省 25%）< 8bit 索引（省 ~75%）< 4bit 索引（省 ~87%，≤16 色易色带）
  < Lottie/ThorVG（无帧，矢量最省最清晰，但要 `LV_USE_THORVG` + 原生 `lv_lottie`）。

## watch2 实测（2026-11-03，466×466 圆表 UI，14 页精灵）

| 项 | 值 |
|---|---|
| app.bin | 6.69MB（8MB 分区用 83.6%） |
| **EEZ 生成 UI** | **6.00MB（89.7%）**：精灵帧 421 张 ≈5.65MB（单帧 14.1KB）、字体 ≈0.25MB、screens 68.6KB |
| LVGL 内核 / IDF / 显示适配 | 295.8KB / 200.9KB / 35.1KB |
| 内部 RAM (bss+data) | 186.4KB（LVGL 堆在 PSRAM） |

## 坑

1. Git Bash 里 `cmd //c export.bat` 会因 `MSYSTEM` 被拒 → 写 bat 先 `set MSYSTEM=`。
2. 换 ui 目录必须带 `CMakeLists.txt`（GLOB 在 configure 期求值，新增文件后要重新 configure）。
3. 466 圆表 UI 跑在 4.3" 横屏上只用于**量体积**，位置/裁切不代表真机观感。
4. 恢复：把 `ui_template_backup` 换回 `ui`、`main.c.bak` 还原即可。

## 精灵帧压缩实测（2026-11-03，watch2）

| 步 | 做法 | 精灵帧 | EEZ UI | app.bin |
| --- | --- | --- | --- | --- |
| 基线 | ARGB8888 / 421 帧 | 5.65MB | 6.00MB | 6.69MB |
| ① bpp16 | `RGB565A8` 10.8KB/帧 | 4.24MB | — | — |
| ② bpp8 | `I8` 调色板（256 色）4.6KB/帧 | 2.26MB* | 2.17MB | 2.86MB |
| ③ 自烘 **I4** | palette 64B + 4bit 索引 = 1.86KB/帧；CLI 后覆写 `ui_image_sp_*.c` | — | — | — |
| ④ 抽帧 ≤20 | 生成器与烘焙器共用 `sample_indices` | **0.45MB** | **1.03MB** | **1.72MB** |

- EEZ 位图 bpp 实测对应：32=ARGB8888 / 16=RGB565A8 / 8=I8 / 4=A8（只留透明度、丢颜色）。
- I4 布局：data 开头 `lv_color32_t` 调色板（B,G,R,A），随后 4bit 索引（高 nibble=偶数像素，LVGL bin_decoder 口径）；
  透明像素=索引 0；调色板用「帧合成到页面底色后取 15 色」，AA 边缘按深底预混避免暗边。
- 管线：`build_watch_ui → cli_build → eez_font_bake → bake_sprite_i4`（I4 必须最后跑，否则被 CLI 覆盖）。
- 代价：每页 20 帧比 33~45 帧顿一点；色彩限于 16 色/帧（本套素材以纯色/线描为主，肉眼几乎无差）。
