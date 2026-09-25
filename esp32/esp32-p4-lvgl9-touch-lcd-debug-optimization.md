# ESP32-P4 + LVGL v9 Touch LCD Debug & Optimization Notes

Waveshare ESP32-P4-WIFI6-Touch-LCD-4.3 开发板（480x800 MIPI-DSI ST7701 屏 + GT911 触摸 + ESP-IDF v5.5.5 + LVGL v9.4 + esp_lvgl_adapter）调试经验总结。

## 1. 芯片修订 (rev) 问题

**症状**: `A fatal error occurred: bootloader.bin requires chip revision in range [v0.1 - v1.99] (this chip is revision v3.2)`。

**原因**: 工程 sdkconfig 里 `CONFIG_ESP32P4_SELECTS_REV_LESS_V3=y` + `CONFIG_ESP32P4_REV_MIN_1=y`（只支持 <3.0 芯片），而实体芯片是 rev v3.2。rev 3.x 与 <3.0 硬件差异巨大、互不兼容。

**修复**: 在 `sdkconfig.defaults` 里替换为：
```
CONFIG_ESP32P4_REV_MIN_301=y   # 支持 rev v3.1+，覆盖 v3.2
```
并删除旧 `sdkconfig` 后重新编译（defaults 不覆盖已生成的 sdkconfig）。注意：不同 rev 的 MIPI-DSI 时钟源不同，rev 变更后 bootloader 体积也会变化（见下节）。

## 2. 分区表偏移与 bootloader 体积

**症状**: `Bootloader binary size 0x60c0 bytes is too large for partition table offset 0x8000 (max 0x6000)`。

**原因**: 改用 rev v3.x 后 bootloader 略变大，超过 `0x8000` 处分区表允许的空间（bootloader 在 0x2000，空间 0x8000-0x2000=0x6000）。

**修复**: 分区表偏移后移：
```
CONFIG_PARTITION_TABLE_OFFSET=0x10000
```
并同步改 `partitions.csv` 中硬编码的 nvs 偏移（0x9000 → 0x11000），phy_init 改自动偏移。

## 3. MIPI-DSI PHY PLL 时钟源 abort（rev3 必踩）

**症状**: 启动后 `abort() ... _mipi_dsi_ll_set_phy_pllref_clock_source`，位于 `esp_lcd_new_dsi_bus`。

**原因**: BSP 里写死 `.phy_clk_src = MIPI_DSI_PHY_CLK_SRC_DEFAULT`，该宏恒等于 `MIPI_DSI_PHY_PLLREF_CLK_SRC_DEFAULT_LEGACY = PLL_F20M`，**仅对 rev<3.0 有效**。rev>=3.0 的 PLL 参考时钟选择器只接受 XTAL/APLL/CPLL/SPLL/MPLL，收到 F20M 落入 `default: abort()`。

**修复**: BSP 中改为 `.phy_clk_src = MIPI_DSI_PHY_PLLREF_CLK_SRC_XTAL`（rev3 用 XTAL），或设 `0` 让 IDF 按编译的芯片修订自动选择。

## 4. LVGL 绘制缓冲分配失败（heap_caps_aligned_alloc 无 fallback）

**症状**: `esp_lvgl:disp: alloc primary buffer 460800 bytes failed` -> `assert failed: bsp_display_start_with_config ... (disp = bsp_display_lcd_init(cfg))`。

**原因**: `esp_lvgl_adapter` 的 `display_manager_alloc_draw_buffer` 在 `use_psram=true` 时调用 `heap_caps_aligned_alloc(128, size, MALLOC_CAP_SPIRAM)`，**失败后没有 fallback 到普通 malloc**（aligned 失败直接返回 NULL）。PSRAM 上 128B 对齐的大块分配（>=230400B）实测失败。

**修复**: 用内部 RAM 小缓冲：`.use_psram = false`、`buffer_height=100`、`require_double_buffer=true`（100x800x2x2=320KB，内部 RAM 约 315KB 可用，分配成功）。**不要**用 `use_psram=true` 或加大 buffer_height（480/240 都会失败崩溃）。

## 5. 横屏旋转 + TRIPLE_PARTIAL 冻结 bug

**症状**: 初始化全部成功（显示/触摸/LVGL 任务无错误），首帧完整显示，但画面冻结不动。

**原因**: adapter 按 tear_avoid_mode 选择不同 flush 路径：
- `TRIPLE_PARTIAL + ROTATE_90` -> `flush_partial_rotate`：部分刷新 + 旋转 + 三缓冲轮转 + 未重绘区域复制，区域映射复杂，本 adapter 版本下增量刷新出错 -> 画面停在首帧
- `TRIPLE_FULL + ROTATE_90` -> `flush_full_rotate`：每帧全屏旋转刷新，逻辑简单稳定

**修复**: 改用 `TEAR_AVOID_MODE_TRIPLE_FULL`（保留横屏 ROTATE_90 + PPA）。代价：每帧全屏刷新，帧率略低于 partial 理论值，但稳定。

**注意**: `TEAR_AVOID_MODE_NONE + ROTATE_90` 不被支持（display_manager.c 直接报错返回）。

## 6. LVGL 触摸方向校正（横屏）

横屏 ROTATE_90 时触摸坐标需对应变换（main.c 的 touch_flags）：
- 上下反 -> `mirror_y=1`
- 左右反 -> `mirror_x=1`
- 旋转 90 度基础组合：`swap_xy=1` + 按实际镜像补 mirror_x/mirror_y

## 7. 触摸偶发初始化失败

**症状**: `GT911 read error / Touch controller GT911 initialization failed`（偶发，重启可恢复）。

**处理**: 若允许触摸缺省运行，可将 `bsp_display_indev_init` 改为容错（失败仅 ESP_LOGW 不 assert，并让 `bsp_display_start_with_config` 不 BSP_NULL_CHECK indev）。用户实测触摸可用则保持原版。

## 8. 帧率优化清单（横屏+PPA 约束下已到顶）

| 项 | 配置 | 说明 |
| --- | --- | --- |
| CPU | `ESP_DEFAULT_CPU_FREQ_MHZ=400` | CPLL 最高 400MHz，无法再高 |
| 编译器 | `COMPILER_OPTIMIZATION_PERF` (-O2) | IDF 无 -O3；LTO 也未提供 |
| 断言 | `COMPILER_OPTIMIZATION_ASSERTIONS_DISABLE=y` | 关闭编译断言省性能 |
| SPIRAM | 200MHz + XIP from PSRAM | 最高档 |
| 缓冲 | 100 行内部 RAM 双缓冲 | PSRAM 大缓冲被第 4 节堵死 |
| PPA | `enable_ppa_accel=true` | 硬件 blend/fill；**PPA 强制 `LV_DRAW_SW_DRAW_UNIT_CNT=1`**，不能开多核渲染 |
| 渲染 | 关闭复杂渐变、阴影缓存16、圆形缓存8、刷新周期10ms、渲染线程栈32KB、优先级5 | |
| LVGL 内部断言 | ASSERT_STYLE/MEM_INTEGRITY/OBJ 全关 | |

**已排除的提速路径**：
- `LV_OS_NONE` + 手动互斥循环：不会提速（锁非瓶颈，adapter 本就用锁+循环），且破坏 adapter 撕裂规避/PPA 同步
- 多核 `DRAW_UNIT_CNT=2`：与 PPA 互斥，P4 上 PPA 收益更大
- MIPI DSI lane 提速：500Mbps x2lane 带宽已远超需求，非瓶颈

## 9. 面板是否支持"原生横屏"

**不支持**。ST7701 是 RGB/MIPI-DSI video mode 面板，物理像素 480x800 竖排，MADCTL(0x36) 只能镜像翻转，**无 90 度行列交换硬件**。横屏（800x480）必须软件旋转（adapter 的 `display_rotate_image` 逐块旋转，CPU 开销），这是横屏帧率瓶颈的物理来源，无法消除。

## 10. EEZ Studio UI 集成（零拷贝引用）

工程 `lvgl_demo_ai` 内嵌 `eez-test/src/ui`（EEZ 生成的 11 屏 UI）：
- **直接引用**：不复制，在 `eez-test/src/ui/CMakeLists.txt` 定义 `ui` 组件，顶层 CMakeLists 的 `EXTRA_COMPONENT_DIRS` 加 `./eez-test/src`，IDF 把 `src/ui` 识别为组件
- 组件 CMakeLists 用 `file(GLOB ...)` 收集 *.c/*.cpp（**不能用 CONFIGURE_DEPENDS**，IDF 脚本模式不支持）
- 入口：`ui_init()` 初始化，`lv_timer_create` 周期驱动 `ui_tick()`（5ms）
- EEZ 切屏 API：`eez_flow_set_screen(screenId, animType, speed, delay)`，screenId 用 `SCREEN_ID_*` 枚举
- `lv_demo_widgets()` 自动轮播：`lv_demo_widgets_start_slideshow()`

## 11. 环境/构建经验

- IDF 工具链在 `D:\esp32_8266_files\esp-idf-tools_for_idf_v5_5_5`（export.ps1 默认找错路径，需设 `IDF_TOOLS_PATH`/`IDF_PYTHON_ENV_PATH`）
- 构建：设置 PATH（riscv32-esp-elf/bin、cmake、ninja、python venv）后 `python $IDF_PATH/tools/idf.py build`
- 烧录/监视：`idf.py -p COM20 flash/monitor`；COM20 (CH343) 会被残留 `idf.py monitor` 进程占用，需先杀进程释放
- ninja 缓存损坏报 `failed recompaction: Permission denied` 时清 `build/.ninja_*` 重试
- 每次改 `sdkconfig.defaults` 必须删旧 `sdkconfig` 再编译才生效
