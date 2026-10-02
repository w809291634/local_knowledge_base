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
| PPA 旋转路径与帧率上限归属：8ms 刷屏=PPA 跨步写固有代价；SRM 改 NON_BLOCKING 实测 FPS 升但拖影（排序≠同步）；队列深 8 无效；on_trans_done 在 ISR；正解需双绘制缓冲；DRAW_UNIT_CNT=2 仅 +6fps | 19 |
| 异步 PPA 旋转落地（8ms 消除）：NON_BLOCKING 提交 + 独立 worker 补发 flush_ready + 计数信号量 + runtime mutex；含两次失败根因与完整修改清单 | 20 |
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
| xiaozhi OTA 版本检查：非数字 PROJECT_VER → std::stoi 未捕获异常 → 启动 abort；版本取值需高于官方，否则官方 OTA 覆盖自定义固件 | 18 |

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

## 18. xiaozhi OTA 版本检查：非数字 PROJECT_VER 导致启动即 abort（std::stoi 未捕获异常）

### 18.1 症状

启动日志走到版本检查后立即 abort（**不是** Brownout、**不是** PPA/TLSF 堆签名、**不是** Hardware fault）：

```
I (11369) Ota: Current version: ee0dbd3-dirty
I (11994) HttpClient: Established new connection to api.tenclass.net:443 protocol=https cost=479
I (13434) HttpClient: HTTP connection closed

abort() was called at PC 0x481f7e55 on core 0
--- 0x481f7e55: __cxxabiv1::__terminate(void (*)()) at libstdc++-v3/libsupc++/eh_terminate.cc:45
```

`__cxxabiv1::__terminate` = **C++ 未捕获异常**：`throw` → 栈展开找不到 handler → `std::terminate()` → `abort()`。见到这个符号先往"未捕获异常"方向查，别查驱动/堆。
（寄存器 dump 里的 `RA: esp_vApplicationTickHook`、`panic_abort` 是**表象**，不是根因。）

### 18.2 根因

- `Ota::ParseVersion()`（xiaozhi-esp32/main/ota.cc）把版本号按 `.` 切分，对每段调 `std::stoi()`：

```cpp
while (std::getline(ss, segment, '.')) {
    versionNumbers.push_back(std::stoi(segment));   // "ee0dbd3-dirty" → 抛 std::invalid_argument
}
```

- `ee0dbd3-dirty` 整串无前导数字 → `std::stoi` 必抛
- xiaozhi 的 OTA 路径**全工程没有 try/catch** → 未捕获 → `std::terminate()` → `abort()`
- 版本号来源：工程未设 `PROJECT_VER` 时，IDF 回退到 `git describe`（`<hash>` / `<hash>-dirty`）。上游 xiaozhi 用 git tag（形如 `1.7.5`）所以不踩
- **通用教训**：凡移植 xiaozhi 且应用版本号非数字（`ee0dbd3-dirty` 必崩；`1.2.3-rc1` 因首段可解析而侥幸），只要服务器下发 firmware 段就必崩

### 18.3 为什么"之前看起来是好的"——引信在服务器手里

崩点有**前置条件**（ota.cc 版本检查主体）：

```cpp
cJSON *firmware = cJSON_GetObjectItem(root, "firmware");
if (cJSON_IsObject(firmware)) {
    ...
    if (cJSON_IsString(version) && cJSON_IsString(url)) {
        has_new_version_ = IsNewVersionAvailable(current_version_, firmware_version_);  // ← 崩点
    }
} else {
    ESP_LOGW(TAG, "No firmware section found!");   // ← 响应无 firmware 段，安全返回、不崩
}
```

- 响应**无 `firmware` 段** → 打印 `No firmware section found!` → 跳过崩点，设备一切正常
- 响应**带 `firmware.version` + `firmware.url`** → 必崩

所以这是**潜伏崩溃，触发权在服务器侧**，与本地绘制/内存/任务配置改动无关，表现为"时好时坏、莫名其妙突然崩"。

**判别方法**：日志里搜 `No firmware section found!`——出现即那次没触发。

**旁证思路**：若设备曾长时间正常运行（如 5 分钟、MQTT 已连），说明当次 `CheckNewVersion()` 安全通过——因为 `InitializeProtocol()` 排在 `CheckNewVersion()` **之后**（application.cc 初始化序列），协议能起来就证明版本检查没走到崩点。

### 18.4 修复（改本工程自己的文件，不动 xiaozhi 树）

顶层 CMakeLists，在 `include($ENV{IDF_PATH}/tools/cmake/project.cmake)` **之前**：

```cmake
set(PROJECT_VER "9.9.9")
```

- 版本变成数字即可消除 crash
- **取值必须高于官方发布**，原因见 18.5

### 18.5 连带坑：自动升级会覆盖自定义固件（比崩溃更危险）

`Application::CheckNewVersion()`（xiaozhi-esp32/main/application.cc）：

```cpp
if (ota_->HasNewVersion()) {
    if (UpgradeFirmware(ota_->GetFirmwareUrl(), ota_->GetFirmwareVersion())) {
        return; // 无任何用户确认
    }
}
```

而 `CONFIG_OTA_URL` 默认官方 `https://api.tenclass.net/xiaozhi/ota/` → 若把 `PROJECT_VER` 设成**低于官方**的值（如 `1.0.0`），设备启动后会被刷成官方 xiaozhi 固件，**覆盖自定义 UI 工程**（本例：EEZ 11 屏全没）。

- 残留风险：ota.cc 中 `firmware.force == 1` 会**绕过版本比较**强制升级，`9.9.9` 挡不住 → 只能改 xiaozhi 源码或更换 OTA URL
- **不能直接关掉版本检查**：该 OTA 接口同时是**服务器配置下发通道**（MQTT/websocket 地址、激活码），AI 对话依赖它，关掉就连不上服务

### 18.6 验证

| 服务器响应 | 预期日志 | 结果 |
| --- | --- | --- |
| 带 firmware 段 | `Current is the latest version` | 继续启动，不升级、不崩 |
| 不带 firmware 段 | `No firmware section found!` | 继续启动，不崩 |

两种路径都不再 abort；另可见 `Ota: Current version: 9.9.9`。

## 19. PPA 旋转路径与帧率上限的归属：非阻塞实测 + 多核渲染实测

> **更正（见 §20）**：本节 19.4 / 19.6 所写"只有一块绘制缓冲 fb2、所以必须串行、要重构才可能"是**错的**——`TRIPLE_FULL` 实际注册 **2 块**绘制缓冲，8ms 已被消除；§19.6 "补丁要避让 adapter 的 render_mode/flush_ready 机制"仍成立，但结论改为**可做**。

背景：§8「帧率优化清单（已到顶）」、§9「横屏必须软件旋转」、§16.2「PPA 关闭后可试多核渲染（未实测）」三条都指向同一个未解问题——**帧率上限到底卡在哪一段**。本节是 2026-10-02 的实测收口，把「8ms 刷屏时间」的归属和处置讲清。

### 19.1 实测数据（EEZ 11 屏 UI；TRIPLE_FULL + ROTATE_90；400MHz / PSRAM 200M）

| 项 | 数值 |
| --- | --- |
| LVGL 软件渲染 | 23 ms/帧 |
| 刷屏（flush，含 PPA 旋转） | 8 ms/帧 |
| 合计 | 31 ms → 理论 32 fps |
| FPS 实测（单 draw unit） | **27** |
| 差额 | ~6 ms，疑似 `LV_DEF_REFR_PERIOD=13ms` 的节拍量化 |

### 19.2 刷屏那 8ms 已经是 PPA 硬件，不是软件旋转

`esp_lvgl_adapter` 的 PPA SRM 客户端在 `CONFIG_SOC_PPA_SUPPORTED` 下**无条件注册**（v9 bridge 的 hw_resource 初始化），所以旋转走 PPA；CPU 软件旋转 `display_rotate_copy_region()` 不执行。

8 ms 换算 ≈ 768KB×2 / 8ms ≈ **190 MB/s**。90° 旋转对**目标缓冲是跨步写**（每个目标行只写 1 个像素），PSRAM 最怕这种访问模式——**游转的固有代价，不是配置没调好**，也没有可调参数（SRM 的 scale/swap 全 DISABLED，`mode` 写死在组件里）。

### 19.3 关键实验：把 SRM 改成 NON_BLOCKING

**改动点必须打对函数**：`rotate_copy_region()` 内的 `oper_config.mode`（v9 bridge）。同文件另有 `rotate_copy_strided_region()`，**FULL 刷屏路径不走它**——改错那一处会得到"完全没变化"的假结论（本次实测踩过，浪费了一轮编译）。

```c
.mode = PPA_TRANS_MODE_NON_BLOCKING,   // 原 PPA_TRANS_MODE_BLOCKING
```

**实测结果**：FPS 明显提升，但**画面出现拖影**。一次实验同时证明两件事：
1. 那 8 ms **确实在关键路径上**（LVGL 任务真的在原地等它）；
2. 缺的不是队列，而是**完成时点通知 + 缓冲复用门控**。

### 19.4 为什么"有队列"也救不了：排序 ≠ 同步（≠ 所有权）

- **队列是真实存在的**：`LVGL_PORT_PPA_MAX_PENDING_TRANS = 8`（`lvgl_port_alignment.h`，不是默认的 1）；驱动侧也有每引擎信号量 + `trans_stailq` 事务队列。
- 但 `NON_BLOCKING` 只做"把描述符与 `in.buffer`/`out.buffer` **指针**推进队列后返回"；**DMA 是在执行时才去读 `in.buffer`**。队列只能保证事务之间的先后，**没有任何机制阻止 CPU 在这 8 ms 内改写那块源缓冲**。
- 本路径的源缓冲 **fb2 同时就是 LVGL 的绘制缓冲**（`draw_buf_primary = frame_buffers[2]`，见 §17.5）→ 下一帧渲染与旋转并发读写同一块内存 → 拖影。
- 结论：**队列保证顺序，不保证数据安全**；把 pending 从 8 调到 16 只会让在途引用更多、竞态更随机。

### 19.5 为什么"补上 on_trans_done"也不涨帧率

- 完成信息在系统里**是存在的**：驱动内部靠 2D-DMA 回调归还槽位；用户通知是另一条可选通道（`ppa_client->done_cb = cbs->on_trans_done`）。
- 但该回调运行在 **ISR 上下文**（2D-DMA 通道回调，返回 `bool need_yield`），**不能**在其中做 `display_lcd_blit_full()` 或 `lv_display_flush_ready()`，必须信号量/任务通知转发。
- 更要紧的是：**单绘制缓冲**下 `flush_ready` 必须等旋转完成才放行 → 帧周期回到 23+8 = 31 ms → **FPS 退回 27**。它只换来"那 8 ms 里 lvgl 任务能跑别的 timer"（触摸、`ui_tick` 更跟手），**不涨帧率**。

### 19.6 正解需要"双绘制缓冲"，但不是配置项

只有让旋转的源缓冲**不再被 LVGL 写**（两块轮转），才能同时拿到"快"与"不拖影"：渲染第 N+1 帧进 B，同时旋转 A。

但 adapter 的 flush **自己就在操纵 LVGL 的渲染模式**：`disp->render_mode` 在 `LV_DISPLAY_RENDER_MODE_FULL` / `DIRECT` 之间切换，并递归 `lv_refr_now()` 强制整屏重绘，还自行调用 `display_manager_flush_ready(disp)`（full-copy 探针机制）。往里加第二块绘制缓冲会与这套逻辑冲突，且很可能破坏现有撕裂规避 → 属**组件内重构**，不是加一块 buffer 那么简单。

**处置**：按 §16.2 的原则不长期打补丁（升级会被覆盖），作为**上游需求**反馈。

### 19.7 多核渲染实测：`LV_DRAW_SW_DRAW_UNIT_CNT = 2`

§16.2 记为"理论可试（未实测）"，现已实测：

- **前提满足**：绘制 PPA 已关（§16）+ `LV_OS_FREERTOS`；LVGL Kconfig 只要求 `>1 requires an operating system enabled in LV_USE_OS`。
- **结果：FPS 仅 +6fps，远非成倍。**
- **原因**：① 该方式只并行"渲染/绘制"那一段（约 23/31 帧时间），旋转与扫描输出仍是串行（Amdahl）；② 绘制段本身是**带宽受限**而非算力受限——fb0/1/2、LVGL 对象、XIP 代码都在 PSRAM，两个 draw unit 只是互相抢同一条 PSRAM 总线。
- **Kconfig 坑**：`LV_DRAW_THREAD_PRIO` 的 `range 0 4`，写 `5` 会被**静默忽略**并回落到默认 3（本工程 `sdkconfig.defaults` 曾写 5，表现为 `sdkconfig` 里是 3）。

### 19.8 本次处置（已落地）

| 动作 | 值 | 理由 |
| --- | --- | --- |
| v9 bridge 的 SRM `mode` | 回退 `PPA_TRANS_MODE_BLOCKING` | 保正确性，避免拖影 |
| `CONFIG_LV_DEF_REFR_PERIOD` | 13 → **10** | 收那 ~6 ms 节拍量化（§8 记的调优值），预计 27 → ~31 fps |

`LV_DRAW_SW_DRAW_UNIT_CNT=2` 保留（+6fps 是真实收益），代价是每个 draw unit 一个线程栈（`LV_DRAW_THREAD_STACK_SIZE`，内部 RAM）。

## 20. 异步 PPA 旋转落地记录：8ms 刷屏时间被消除（含修改清单）

**结果**：`TRIPLE_FULL + ROTATE_90` 下，原本串行占用的 ~8ms 刷屏（PPA SRM 旋转）已被**完全隐藏**，LVGL 任务不再等待它。本节同时**更正 §19.4/§19.6 的错误前提**，并给出可复现的修改清单（补丁在托管组件内，组件升级会覆盖，故必须留档）。

### 20.1 更正 §19 的两处错误

| §19 原结论 | 实际 | 证据 |
| --- | --- | --- |
| "FULL+旋转下只有一块绘制缓冲 fb2，所以必须串行" | **错。`TRIPLE_FULL` 注册 2 块绘制缓冲** | `display_manager_required_buffer_count()` 对 `TRIPLE_FULL` 直接 `return 2`；`lv_display_set_buffers(disp, draw_buf_primary, draw_buf_secondary, buf_bytes, ...)` |
| "要同时拿到快与不拖影需重构成双缓冲，属上游重构、不可做" | **错。缓冲本来就有，只差"完成时点 + 独立补发上下文"** | 见 20.3 |

§19.6 里"adapter 自己操纵 `render_mode` / `lv_refr_now` / `flush_ready`，补丁要避让"这点**仍然成立**；但结论从"不可做"改为"**可做**"。

### 20.2 为什么"有队列 + 有双缓冲"还不够

- PPA 队列真实存在（`LVGL_PORT_PPA_MAX_PENDING_TRANS = 8`，`lvgl_port_alignment.h`），但 `NON_BLOCKING` 只是"把描述符与 `in.buffer`/`out.buffer` **指针**推进队列后返回"；**DMA 在执行时才读 `in.buffer`** → 队列保证**顺序**，不保证**数据安全**（CPU 可改写 DMA 正在读的缓冲）。把 pending 调大只会让竞态更随机。
- 完成信息在驱动里是有的（每引擎信号量 + `trans_stailq` 自归还），用户通知是**可选**通道：`ppa_client->done_cb = cbs->on_trans_done`。
- **该回调运行在 ISR 上下文**（2D-DMA 通道回调，返回 `bool need_yield`）→ 回调里只能给信号量，**不能**做 blit / `flush_ready`。

### 20.3 落地设计（4 个要素，缺一不可）

| # | 要素 | 解决的问题 |
| --- | --- | --- |
| 1 | 旋转用 `PPA_TRANS_MODE_NON_BLOCKING` 提交，flush 回调**立即返回** | LVGL 任务不再等那 8ms |
| 2 | **独立任务**（`ppa_rot`，prio 7 > LVGL 任务 prio 6）在旋转完成后做 blit + `flush_ready` | 补发者必须能**独立于 LVGL 任务**运行（见 20.4 失败 2 的死锁） |
| 3 | **计数**信号量（上限 4），**不是二值** | 2 块绘制缓冲最多 2 笔在途；二值会丢计数 → 某缓冲永远拿不到 `flush_ready` → 卡帧 |
| 4 | mutex 保护 adapter 的 `impl->runtime` / `toggle_fb`（worker 的 blit ↔ LVGL 侧 `display_runtime_acquire_next_buffer`） | 跨任务竞态（worker 与 lvgl 任务同时改同一结构） |
| 附加 | `flush_ready` 推迟到旋转完成才发 | ① 面板不再被叫去扫描半成品 → **消拖影**；② LVGL 不会重画旋转正在读的源缓冲 → **结构性安全**，不是靠时序巧合 |

### 20.4 两次失败与根因（本节最有价值的部分）

**失败 1：改错函数（白编译一次）。** v9 bridge 里同时存在 `rotate_copy_region()` 与 `rotate_copy_strided_region()`；横屏 FULL 刷屏走**前者**（由 `flush_full_rotate()` 调用），后者是 stride 旁支。改到后者 → 得到"完全没变化"的假结论。
→ **教训：动 adapter 前先确认调用链**（本例 dispatch → `flush_full_rotate` → `rotate_copy_region`），不要按函数名猜。

**失败 2：把补发 `flush_ready` 放进 LVGL 任务 → 死锁 + 任务看门狗复位。**
症状：`task_wdt: CPU 1: lvgl`，栈顶 `wait_for_flushing at lv_refr.c:1442`（来自 `resolution_change_event_cb` → `lv_refr_now`）。
根因：`wait_for_flushing()` 会**在 LVGL 任务内同步忙等** `flushing` 标志；若把补发者做成"同一任务里的 lv_timer"，任务卡在忙等里 → 定时器永不执行 → 自锁。
→ **教训：`flush_ready` 必须由能独立于 LVGL 任务运行的上下文补发**（独立任务），不能是同任务定时器。

**顺带纠正一个机制理解（决定这条路能否成立）：**

```c
/* lv_refr.c:1019 */ if(!lv_display_is_double_buffered(disp_refr)) { wait_for_flushing(disp_refr); }        /* 单缓冲才等 */
/* lv_refr.c:1374 */ if(lv_display_is_double_buffered(disp))        { wait_for_flushing(disp_refr); }        /* 仅两块都被占用时才等 */
```

即：**双缓冲 + 及时补发 `flush_ready` 时，正常渲染路径不会等待** —— 这正是 8ms 能被隐藏的前提。还有一条实证：早期"只把模式翻成 NON_BLOCKING（`flush_ready` 仍同步）"时 FPS 就涨了 → 证明 flush 回调一返回，LVGL 就去渲染下一帧了，没有别的隐含等待。

### 20.5 修改清单（托管组件内，升级会被覆盖）

文件：`managed_components/espressif__esp_lvgl_adapter/src/display/bridge/v9/lvgl_bridge_v9.c`

| # | 位置 | 改动 |
| --- | --- | --- |
| 1 | 文件顶部 LVGL v9 区域（新增异步设施） | `#define V9_ROT_QUEUE_LEN 4`；`v9_rot_item_t{impl, next_fb, disp}`；SPSC 环 `s_rot_queue[]` + `volatile s_rot_head`（worker 写）/`volatile s_rot_tail`（LVGL 写）；`s_rot_done_sem`（**计数**，上限 4）；`s_rot_rt_mutex`；`s_rot_initialized`；`v9_rot_push()` / `v9_rot_pop()`；`v9_rot_worker()`；`v9_rot_async_init()`（懒创建 `xSemaphoreCreateCounting(4,0)` + `xSemaphoreCreateMutex()` + `xTaskCreate(v9_rot_worker,"ppa_rot",3072,NULL,7,NULL)`） |
| 2 | `#if CONFIG_SOC_PPA_SUPPORTED` 区域内 | `v9_ppa_srm_done_cb()`：`IRAM_ATTR`，判空后仅 `xSemaphoreGiveFromISR(s_rot_done_sem,&hp)`，返回 `hp == pdTRUE` |
| 3 | SRM 客户端创建处（紧随 `ppa_register_client` 之后） | `ppa_event_callbacks_t rot_cbs = { .on_trans_done = v9_ppa_srm_done_cb };` + `ppa_client_register_event_callbacks(hw_resource.ppa_handle, &rot_cbs);` |
| 4 | `rotate_copy_region()` 的前向声明与定义 | 返回类型 `void` → `bool`；参数末尾加 `bool non_blocking`；`.mode = non_blocking ? PPA_TRANS_MODE_NON_BLOCKING : PPA_TRANS_MODE_BLOCKING`；PPA 分支 `return true;`（已异步提交），CPU 兜底末尾 `return false;`（已同步完成）；保留 `IRAM_ATTR` |
| 5 | 另两处调用点（`display_bridge_v9_flush_triple_diff`、`flush_dirty_copy`） | 显式传 `false` 保持同步：`(void)rotate_copy_region(..., color_bytes, false);` |
| 6 | `display_bridge_v9_flush_full_rotate()` | 顺序改为：`v9_rot_async_init()` → **持 mutex** 取 `next_fb` → `rotate_copy_region(..., true)` → 成功则组装 `v9_rot_item_t{impl,next_fb,disp}` 入队（`v9_rot_push`）；**本函数内不再 blit、不再 `flush_ready`**；`!submitted`（PPA 不可用）与队列满时走同步兜底（持 mutex blit + `flush_ready`） |

**已知未处理项**：`v9_rot_async_init()` 若创建信号量/mutex/任务失败（仅启动期堆耗尽时可能），`s_rot_initialized` 仍为 false，后续 `xSemaphoreTake(NULL)` 会触发断言。正常启动不会走到；若要彻底安全需再加约 15 行降级分支（退回全同步路径）。

### 20.6 仍未验证的点（诚实标注）

- `display_lcd_blit_full()` / `display_manager_flush_ready()` 从**非 LVGL 任务**调用是否线程安全——实测运行正常，但**无正式保证**。
- worker 持 `s_rot_rt_mutex` 期间若 `display_lcd_blit_full()` 内部阻塞，LVGL 侧的 `acquire` 会一并等待（从现有代码看它不等待：等待是 flush 里另起的一步 `ulTaskNotifyTake`，而 `flush_full_rotate` 内没有）。
- 队列满/超时兜底会产生一次"多余计数"，理论上让 worker 提前处理未完成项；2 块缓冲下不会触发。
- SPSC 环用 `volatile` 索引（生产者/消费者各只写一个索引），未加内存屏障。
