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

## 15. 经验分类索引（芯片级 / 板卡级 / 通用级）

按适用范围分类，便于不同项目对号入座：

### 【P4 芯片级】（换板卡仍适用，只要是 ESP32-P4）
| 经验 | 节 |
| --- | --- |
| 芯片修订 rev v3.1+ 配置 CONFIG_ESP32P4_REV_MIN_301 | 1 |
| 分区表偏移 0x10000（bootloader 体积超限） | 2 |
| MIPI-DSI PHY PLL 时钟源必须用 0/XTAL（rev3 必踩 abort） | 3 |
| PPA 加速强制 LV_DRAW_SW_DRAW_UNIT_CNT=1（不能多核渲染） | 8 |
| use_psram=true 大块 128B 对齐分配不可靠（无 fallback） | 4 |
| buffer_height 480/240 双缓冲失败 | 4 |
| L2 缓存 256KB / 128B 行（影响 PSRAM 对齐与 msync） | 全文 |
| SPIRAM XIP from PSRAM + -O2 + IRAM 优化组合 | 8 |
| esp_lvgl_adapter 旋转路径行为（TRIPLE_FULL 稳定 / TRIPLE_PARTIAL 冻结） | 5 |
| LVGL PPA 绘制单元 DMA 越界写堆（需 enable_ppa_accel=false） | 16 |
| 内部 RAM 账：L2MEM 768KB / cache 256KB / 堆仅 373KB | 17 |
| LVGL 内存走 PSRAM：CUSTOM_MALLOC + lv_mem_psram 组件 + --undefined 链接 | 17 |
| 内部存储器全景（HP/LP 域、HP SPM、LP SRAM） | 17 |

### 【板卡级】（Waveshare ESP32-P4-WIFI6-Touch-LCD-4.3，换板卡要改）
| 经验 | 节 |
| --- | --- |
| GT911 触摸复位时序（GPIO23 独立 RST，手动 50ms+150ms 复位） | 7 |
| 控制台 UART 引脚 GPIO37/38、背光 26、LCD RST 27、触摸 I2C 8/7、SD、I2S 引脚 | 12、全文 |
| 板卡启动日志特征（cpu_start 报 console UART 引脚） | 全文 |

### 【通用级】（任意 ESP32 工程，非 P4 专属）
| 经验 | 节 |
| --- | --- |
| 控制台移植 7 步清单（CMakeLists/board_config/board/main/Kconfig/defaults） | 13 |
| LVGL 自定义 malloc（CUSTOM_MALLOC）通用实现与静态库链接坑 | 17 |
| 串口只改波特率无效，必须 UART CUSTOM+引脚 | 12.1 |
| FreeRTOS 内核扩展（TCB cpuUsagePercent + vTask*） | 12.3 |
| 控制台任务栈 8KB+ 、PSRAM/内部可配、优先级不宜过高 | 12.2、踩坑 |
| CPU 监控堆损坏历史风险 | 12.3、踩坑 |
| Kconfig.projbuild 正斜杠路径（反斜杠被当转义） | 13、踩坑 |
| 构建/监视器环境、COM 口占用、sdkconfig 重生 | 11 |

适用判断：
- 新项目同样是 P4 芯片，但板卡不同 → 只须使用【芯片级】+【通用级】，【板卡级】引脚按新板卡改
- 非 P4 苯（如 S3）→ 只用【通用级】；芯片级项目中 DSI/PPA/PSRAM 等按实际芯片核对

## 16. LVGL PPA 绘制单元 DMA 越界写 → PSRAM 堆损坏崩溃（禁用 enable_ppa_accel 解决）

**症状**: 启用 PPA（`.enable_ppa_accel = true`）时，启动后约 0.5s（LVGL 首帧整屏刷新期间）出现 `Guru Meditation Error: Core 0 panic'ed (Store access fault)`，崩溃栈在 TLSF 堆管理（`remove_free_block` / `block_trim_used` / `tlsf_malloc`，realloc 路径）。禁用 PPA 后完全稳定。

**根因**: `esp_lvgl_adapter`（managed_components，v9 bridge）的 LVGL PPA 绘制单元 `lvgl_ppa_accel_v9.c` 的 fill/blend DMA 路径在帧缓冲边界越界写，覆盖 fb2 之后的 PSRAM 堆空闲块。

**证据链**（全部吻合）:
- 禁用 PPA → 稳定；启用 → 必崩（唯一变量）
- 被覆盖的 TLSF free-list 链值为 `0xAEABAFDE`/`0xECBBABAA` 等 —— 典型 RGB565 像素颜色，即 DMA 写穿的像素数据
- 损坏点紧邻 fb2 尾部之后 4~16KB（fb2 = LVGL 渲染目标 = DSI 第 3 帧缓冲，连续分配在 PSRAM 堆内，其后即堆空闲块）
- 崩溃发生于下一次 malloc/realloc 遍历 free 块时（remove_free_block / block_trim_used 处解引用被覆盖指针）

### 16.1 PPA 在显示链路中的两个独立岗位

显示一帧走两步，PPA 在两步里各有一个**独立注册的客户端、独立的开关**：

| 岗位 | 环节 | 由谁控制 | 状态 |
| --- | --- | --- | --- |
| ① 绘制 fill/blend | LVGL 把 UI 算成像素写进 fb2 | **`.enable_ppa_accel`** | 必须 `false`（安全） |
| ② 旋转 SRM | bridge 把竖排 fb2 旋转 90° 成横屏写进 fb0/fb1 | 不受该开关影响，无条件注册（`PPA_OPERATION_SRM`） | `true`（安全保留） |

- 横屏方向由第②步（`rotate_copy_region`）产生，与第①步用什么画无关 → **关掉绘制 PPA 不影响横屏**
- 第②步有 CPU 兜底（`display_rotate_image`），最坏只是慢，不会失效
- `enable_ppa_accel` 只控制 `lvgl_port_ppa_v9_init`（绘制单元 fill/blend 加速）

### 16.2 为什么绘制 PPA 越界、CPU 与旋转不越界

**绘制 fill/blend 越界的数字根因**:
- 一行 480px × 2B = **960B/行**；128B 缓存/DMA 块 = 64 像素；960 ÷ 128 = **7.5 块/行，除不尽**
- 整帧 768000B = 128 × 6000 能整除，但 PPA 是**按行/按块**操作：块 = 不定长脏区（`blend_area ∩ clip_area`），动画时右/下边缘随机落点，某块边缘一旦顶在缓冲末端，行凑整（960B 非 128 倍数）就跨出缓冲 0~127B
- 整屏刷新每秒几十帧，每帧多跨一点 → 累计成实测 4~16KB 损坏区

**为什么 CPU 路径不坏**: 软件渲染严格按 `dest_w × dest_h` 循环、用真实 `layer_stride` 逐像素写，物理上没有"凑整块"动作，写不出缓冲末尾。

**为什么旋转（SRM）不越界**（不是靠整除，单行同样除不尽）:

| | 块形态 | 行宽能否整除 128 | 越界？ |
| --- | --- | --- | --- |
| 绘制 fill/blend | 不定长脏块，边缘悬空 | 960B ÷ 128 = 7.5 ✗ | **越界** |
| 旋转 SRM | **整帧固定块**，边缘=缓冲边界 | 1600B ÷ 128 = 12.5 ✗（也除不尽） | 不越界 |

旋转安全靠的是：块 = 整帧、目标 offset 固定、每帧行为 100% 一致 → 目标块恰好填满整个缓冲，行凑整被限制在块内行与行之间消化，**边缘从不悬空**，填满即止。而 fill/blend 的任意脏块边缘随时可能恰好贴到缓冲末端 → 凑整出格。

### 16.3 关键数字（板上实锤）

| 项 | 值 |
| --- | --- |
| fb0 / fb1 / fb2 地址 | `0x48170A80` / `0x4822C300` / `0x482E7B80` |
| 请求大小 | 480×800×2 = 768000 B |
| 实际占用（相邻间隔） | 768128 B（768000 + 128 TLSF 头/对齐） |
| fb2 数据区末端 | `0x483A3380` |
| 损坏区 | fb2 末端 +4~16KB ≈ `0x483A4380 ~ 0x483A7380` |
| fill 的 buffer_size | `ALIGN_UP(768000, 128)` = 768000（精确等于数据区） |
| 旋转的 buffer_size | `heap_caps_get_allocated_size(to)`（分配器实际值，未实测打印） |

**修复/配置**: BSP 显示配置（esp32_p4_wifi6_touch_lcd_4_3.c `bsp_display_lcd_init`）：
```c
.profile = {
    ...
    .enable_ppa_accel = false,   // 必须关闭；PPA 只加速不透明 fill/大面积 blend，
                                 // 小面积(<100px)/半透明/带 mask 本就走 CPU fallback，损失有限
},
```

**注意**:
- 这是官方 `espressif__esp_lvgl_adapter`（managed_components，v9 bridge）的 PPA 适配缺陷，与 **FULL 模式 + ROTATE_90 + 整屏刷新** 组合强相关（整屏刷新时 dirty 块才顶到缓冲末端；部分刷新/无旋转不触发）；勿在本机打补丁（组件升级会被覆盖），如需恢复 PPA 加速应升级组件或向 Espressif 反馈
- 与第 8 节呼应：PPA 还强制 `LV_DRAW_SW_DRAW_UNIT_CNT=1`（不能开多核渲染），本就有互斥限制；若 PPA 关闭，理论上可尝试 `DRAW_UNIT_CNT=2` 多核渲染作为替代加速（未实测）
- bridge 旋转路径（flush_full_rotate 的 PPA rotate）与本缺陷相互独立，不受该开关影响（profile 的 `enable_ppa_accel` 只控制 LVGL 绘制单元 PPA）
- 排查堆损坏通用经验：优先怀疑紧邻大缓冲（帧缓冲/DMA buffer）末端的越界写；被覆盖的空闲链值若为像素颜色，基本可锁定是显示路径 DMA 写穿

## 17. LVGL 内存管理：内部 RAM 耗尽分析与 PSRAM 方案（LVGL 对象走外部 RAM）

### 17.1 症状与诊断

`mem` 显示 Internal SRAM Free 仅 ~10KB（甚至 23B），但 PSRAM 29MB 空闲；`tasks` 命令报 `Failed to allocate memory for task status array`（内部堆碎片无法申请连续块）。启动日志加 `heap_caps_get_*` 打印后确诊：

```
INT:    free=23/373783 B     ← 内部堆 373783B 几乎耗尽
SPIRAM: free=29762968/32090496 B  ← 外部 32MB 闲着
LVGL pool: total=0            ← LV_MEM_CUSTOM（系统 malloc）模式，LVGL 无自带池，对象全走内部堆
```

**结论**：内部 RAM 被"LVGL 对象/样式（EEZ 11 屏）+ 系统"占满。绘制缓冲本就在 PSRAM，**LVGL 对象走系统 malloc（内部优先）才是真正大头**。

### 17.2 内部 RAM 账（ESP32-P4）

| 项 | 值 |
| --- | --- |
| HP L2MEM 总量 | 768 KB（200MHz，代码+数据+堆） |
| L2 cache 配置 | `CONFIG_CACHE_L2_CACHE_256KB`（256KB 划给 cache） |
| 系统可用 SRAM | ~512 KB（768-256） |
| 堆（heap） | ~373 KB（其余 ~137KB 被静态/任务栈/驱动占） |
| 实测 | 内部堆被 UI 占用 → 仅剩 23B~10KB |

- 与 PSRAM（32MB，`0x48000000-0x4BFFFFFF`）相比，内部堆 373KB 根本装不下 EEZ 11 屏 UI（2~4MB）→ **LVGL 内存必须走 PSRAM**
- ESP32-P4 内部存储器全景：HP ROM 128KB / **HP L2MEM 768KB** / LP ROM 16KB / LP SRAM 32KB / HP SPM 8KB / eFuse 4Kbit；HP=高性能域（跑主程序，400MHz 双核），LP=低功耗域（40MHz 唤醒监听）

### 17.3 方案：LVGL CUSTOM_MALLOC + lv_mem_psram 组件（全部对象走 PSRAM）

**配置**（sdkconfig.defaults 已固化，删 sdkconfig 重生成也保留）：
```
CONFIG_LV_USE_CUSTOM_MALLOC=y     # 关 CLIB_MALLOC，开 CUSTOM_MALLOC
```

**实现**：独立组件 `components/lv_mem_psram/`（CMakeLists REQUIRES lvgl__lvgl），提供 LVGL CUSTOM_MALLOC 要求的全部 core 符号，统一 `heap_caps_malloc(MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT)`：
`lv_mem_init`（空）、`lv_malloc_core` / `lv_free_core` / `lv_realloc_core` / `lv_calloc_core`、`lv_mem_monitor_core`（报告 PSRAM 概览）、`lv_mem_test_core`（返回 LV_RESULT_OK）。

**关键坑（链接顺序）**：LVGL 静态库 `liblvgl__lvgl.a` 需要 core 符号；`lv_mem_psram` 组件 .a 若"符号无引用"会被跳过 → `undefined reference to lv_malloc_core`。
- ❌ 强制引用数组（`__attribute__((used))` 引用函数指针）——能用但 hack，且必须放在 main.c（自身引用无效）
- ✅ **规范解法**：顶层 CMakeLists 在 `project()` 之后给最终链接目标加选项（必须用 `${PROJECT_NAME}.elf`，不是 `${PROJECT_NAME}`）：
```cmake
target_link_options(${PROJECT_NAME}.elf PRIVATE
    "-Wl,--undefined=lv_mem_init"
    "-Wl,--undefined=lv_malloc_core"
    "-Wl,--undefined=lv_free_core"
    "-Wl,--undefined=lv_realloc_core"
    "-Wl,--undefined=lv_calloc_core"
    "-Wl,--undefined=lv_mem_monitor_core"
    "-Wl,--undefined=lv_mem_test_core")
```
- ❌ `--undefined` 加在组件库 `target_link_options(${COMPONENT_LIB} ...)` **不传播**到最终链接，无效
- ⚠️ 环境：直接 `python idf.py build`（不走 export）会报 `ESP_ROM_ELF_DIR environment variable is not defined`，需先设 `$env:ESP_ROM_ELF_DIR = "$env:IDF_PATH\components\esp_rom\esp32p4"`

**验证**：烧录后 `mem` 的 Internal SRAM Free 应大幅上涨（LVGL 对象全部进 PSRAM）。

### 17.4 为什么 UI 需要 2~4MB 内存

- **EEZ 生成代码全量创建**：`eez_flow_init` 末尾 `create_screens()` 把 11 个屏的全部控件一次性创建（screens.c：`create_screen_main()...create_screen_notifications()` 无条件下全建），之后 `replacePageHook(1,...)` 只切显示，**其余屏对象常驻内存**
- **每对象结构 ~400~500B**：`lv_obj_t` 基结构 ~240B（坐标/标志/样式槽/事件/子对象链/扩展）+ 样式 ~200B（padding/背景/边框/阴影/半径…）+ 动画 ~100B；3300 对象 ≈ 1.3~1.7MB
- **叠加项**：图片解码缓冲（PNG/JPG 按分辨率×色深）、字体位图缓存、渲染临时层（mask/layer）、flex/grid 布局数据 → 全算 2~4MB
- **EEZ 无"按需/懒加载创建屏"配置**：生成代码硬编码全建，工程里没有开关能阻止；要省只能手改生成文件（`create_screens()` 只建首屏 + 交互式懒建），与"不改生成文件"约定冲突 → 不推荐，PSRAM 下 2~4MB 无压力

### 17.5 相关要点

- 绘制缓冲（DSI 帧缓冲 fb0/1/2 与 draw_buf=fb2）**本就在 PSRAM**（FULL+旋转下 draw_buf_primary=frame_buffers[2]），`use_psram` 开关只影响非 FULL 模式；实测改 use_psram 内部无变化，证明显示缓冲从不占内部
- `CONFIG_SPIRAM_MALLOC_ALWAYSINTERNAL=16384`（<16KB malloc 强制内部）保持默认，配合 CUSTOM_MALLOC 即可定向解决 LVGL 对象
- 后续若加 WiFi（esp_wifi_remote/esp_hosted）需内部 RAM，此方案腾出的空间正好可用