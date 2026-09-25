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

## 7. 触摸初始化失败（热重启几乎100%复现）

板卡参考：https://docs.waveshare.net/ESP32-P4-WIFI6-Touch-LCD-4.3/FAQ/

**症状**: 启动日志出现：
```text
i2c transaction failed -> GT911 read error! -> esp_lcd_touch_new_i2c_gt911: GT911 init failed -> Touch controller GT911 initialization failed! (0x103)
```
触摸不可用。**断电冷启动基本成功；软件复位（SW_CPU_RESET）、RTS 复位等热重启后几乎 100% 失败**。

**根因**: ESP-IDF GT911 驱动（managed_components/espressif__esp_lcd_touch_gt911）内置复位 `touch_gt911_reset` 在复位脉冲（10ms 低 + 10ms 高）后**仅等约 20ms 就读取配置**（`touch_gt911_read_cfg` 读 0x8140 产品 ID）。冷启动时触摸早已上电就绪故读取成功；热重启时触摸处于"上电未复位"状态，复位后 20ms 内未就绪，I2C 读超时失败。

**板卡引脚要点**（容易踩坑）：
- 触摸复位 RST = **GPIO23**（独立引脚；BSP 源码里 `// Shared with LCD reset` 注释有误导，LCD 复位实际是 GPIO27）
- 触摸 INT = `GPIO_NUM_NC`（未接）→ 驱动永远走 `I2C address initialization procedure skipped - using default GT9xx setup` 路径，不会做 INT 选址握手

**修复**（components/esp32_p4_wifi6_touch_lcd_4_3/esp32_p4_wifi6_touch_lcd_4_3.c 的 `bsp_touch_new`）：
1) 创建触摸前手动规范复位：GPIO23 拉低 50ms → 拉高 → 等待 150ms（GT911 完整启动时间）
2) `tp_cfg.rst_gpio_num` 设为 `GPIO_NUM_NC`，让驱动跳过自身过短的 20ms 复位（rst=NC 时 `touch_gt911_reset` 不动作，直接读配置，此时触摸已就绪）
3) 保留 5 次"探测 + `esp_lcd_touch_new_i2c_gt911`"重试（间隔 100-200ms）兜底

**验证**: 修复后连续多次热重启触摸均稳定初始化成功。

**备选（不做根因修复时）**: 若允许触摸缺省运行，可将 `bsp_display_indev_init` 改为容错（失败仅 ESP_LOGW 不 assert，并让 `bsp_display_start_with_config` 不 BSP_NULL_CHECK indev）。

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

## 12. 控制台 + CPU 使用率适配（UART 自定义引脚/波特率 + FreeRTOS 内核扩展）

### 12.1 控制台 UART（只改波特率无效，必须 CUSTOM 模式）

sdkconfig.defaults：
```
# CONFIG_ESP_CONSOLE_UART_DEFAULT is not set
CONFIG_ESP_CONSOLE_UART_CUSTOM=y
CONFIG_ESP_CONSOLE_UART_CUSTOM_NUM_0=y
CONFIG_ESP_CONSOLE_UART_TX_GPIO=37
CONFIG_ESP_CONSOLE_UART_RX_GPIO=38
CONFIG_ESP_CONSOLE_UART_BAUDRATE=961200
```
- P4 板卡调试串口 = GPIO37(TX)/38(RX)（cpu_start 日志报 "GPIO 38 and 37 are used as console UART I/O pins"，TX/RX 以接线实测为准）
- 监视器：idf.py -p COM20 monitor -b 961200
- 只设 CONFIG_ESP_CONSOLE_UART_BAUDRATE 不会生效：DEFAULT 模式走 ROM 控制台配置，必须切 CUSTOM 显式指定引脚+波特率重建 UART0

### 12.2 控制台任务栈内存位置可配

components/board_config/board_config.h：
```
#define BOARD_CONFIG_CONSOLE_TASK_STACK_SIZE           8192
#define BOARD_CONFIG_CONSOLE_TASK_PRIOR                10
#define BOARD_CONFIG_CONSOLE_TASK_CPU                  0
#define BOARD_CONFIG_CONSOLE_TASK_STACK_IN_PSRAM       1   // 1=PSRAM(MALLOC_CAP_SPIRAM)，0=内部RAM
```
apl_console.c 任务创建按宏选择 MALLOC_CAP_SPIRAM / MALLOC_CAP_INTERNAL。

### 12.3 CPU 使用率监控（修改了 IDF FreeRTOS 内核，全局生效）

改动点（IDF 全局源码，影响所有使用该 IDF 副本的工程）：
- FreeRTOS-Kernel/include/freertos/FreeRTOS.h：TCB dummy 区增加 float cpuUsagePercent（受 configGENERATE_RUN_TIME_STATS 守卫）
- FreeRTOS-Kernel/tasks.c：tskTCB 增加 float cpuUsagePercent；文件末尾新增 vTaskGetStackSize（读 uxSizeOfStack 返回真实栈大小）/vTaskResetRunTimeCounter（ulRunTimeCounter=0）/vTaskSetCpuUsagePercent/vTaskGetCpuUsagePercent（CPU 类受 configGENERATE_RUN_TIME_STATS 守卫）
- 需 CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS=y

使用方：
- components/board/board.c：vTimerCallback（1s 软件定时器，uxTaskGetSystemState 遍历任务 → vTaskSetCpuUsagePercent/vTaskResetRunTimeCounter）+ setupCpuUsageMonitor()，在 hw_board_init() 里按 CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS 调用
- common/APL/apl_console_cmd_system 的 tasks 命令：vTaskGetStackSize + vTaskGetCpuUsagePercent 显示
- board_extra.c 已移除（符号由内核直接提供）

注意：该监控每秒 uxTaskGetSystemState + pvPortMalloc，历史上曾与 TLSF 堆越界写损坏关联；若复现堆崩溃，先 #if 0 禁用排查。

## 13. 控制台/CPU 使用率移植通用清单（跨项目复用）

以下改动适用于任何基于该 IDF 副本 + common/APL 模板的 ESP32 工程（不限 P4 板卡）：

### 移植步骤
1. 顶层 CMakeLists.txt：
   - set(APL_DIR "$ENV{IDF_PATH}/examples/<版本目录>/common/APL")、DRV_DIR 同理（版本目录按实际，如 idf_v555_my_exps）
   - add_component_dirs() 注册 apl_console、apl_console_cmd_nvs/system/wifi、apl_utility（需要时加 drv_*）
   - 注意：include(project.cmake) 之后只能用 list(APPEND EXTRA_COMPONENT_DIRS ...) 追加，不要 set 覆盖，否则 APL/DRV 组件丢失
2. components/board_config：board_config.h（按板卡改引脚 + 任务宏）+ board.h；CMakeLists 用 idf_component_register(SRCS "" INCLUDE_DIRS .)
3. components/board：board.c（hw_board_init：CONFIG_APP_ENABLE_CONSOLE 下 apl_console_init + RUN_TIME_STATS 下 setupCpuUsageMonitor）+ CMakeLists REQUIRES board_config apl_console apl_utility
4. main：main.c 调 hw_board_init()（或 apl_console_init()，二选一避免双重初始化）；main/CMakeLists REQUIRES 加 apl_console
5. main/Kconfig.projbuild：orsource 用正斜杠路径引 Kconfig.apl_console（反斜杠会被当转义符导致静默跳过）
6. sdkconfig.defaults：CONFIG_APP_ENABLE_CONSOLE=y、CONFIG_CONSOLE_IGNORE_EMPTY_LINES=y、CONFIG_ESP_CONSOLE_UART_CUSTOM=y + CUSTOM_NUM_0=y + TX/RX GPIO（按板卡！）+ 波特率、CONFIG_FREERTOS_GENERATE_RUN_TIME_STATS=y（CPU 使用率需要）
7. vTask* 符号：由 IDF FreeRTOS 内核直接提供（见 12.3），无需再建 board_extra

### 按板卡必改项
- 控制台 UART 引脚/波特率（P4: 37/38 或 38/37 实测；S3 例: 43/44）
- board_config.h 引脚宏（触摸/背光/复位/SD/I2S 等）
- 波特率建议与监视器一致（如 961200 / 1000000）

### 注意
- FreeRTOS 内核修改（TCB cpuUsagePercent + 4 函数）是 IDF 全局的，所有工程共享，升级/替换 IDF 副本需重打补丁
- CPU 监控历史上与堆损坏相关，移植后可先用 #if 0 关掉验证稳定

## 14. 技能化：控制台移植知识已封装为 TRAE 技能

为跨项目复用，已将 12/13 节的知识封装为技能：
- 名称：`esp32-console-porting`
- 位置：项目 `.trae/skills/esp32-console-porting/SKILL.md`
- 内容：7 步移植清单、UART CUSTOM 配置（只改波特率无效）、FreeRTOS 内核扩展（TCB cpuUsagePercent + 4 个 vTask 函数）、按板卡必改项、踩坑与安全项
- 触发条件：新工程移植控制台/串口配置/CPU 使用率或相关异常排查时自动加载
- 注意：技能在当前工作区 `.trae/skills/` 下，仅当前工程可见；若需全局可用，可拷贝至用户全局技能目录
