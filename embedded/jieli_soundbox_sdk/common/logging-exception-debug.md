# 日志、断言与异常现场定位（杰理 SDK 通用）

## 1. 日志的六级别与"运行时开关"

`include_lib/system/debug.h`：`LOG_VERBOSE(v)` / `LOG_INFO(i)` / `LOG_DEBUG(d)` / `LOG_WARN(w)` / `LOG_ERROR(e)` / `LOG_CHAR(c)`
（`:13-18`）。

**`LOG_MODE` 实际取 `LOG_BY_CONST`（`:51`）—— 即开关由运行时常量控制，不是编译期裁剪。**
用法是两段式：

```c
// 源文件里
#define LOG_TAG_CONST  APP
#define LOG_TAG        "[APP]"
#define LOG_ERROR_ENABLE
#define LOG_DEBUG_ENABLE
#define LOG_INFO_ENABLE
#define LOG_CLI_ENABLE
#include "debug.h"

// log_config 目录里对应的 .c（如 apps/soundbox/log_config/lib_system_config.c）
const char log_tag_const_d_APP AT(.LOG_TAG_CONST) = CONFIG_DEBUG_LIB(TRUE);
```

- **开关不在源文件里改，而在 `log_config/*.c` 里改常量**，改完要重编。
- 没有定义 `LOG_TAG_CONST` 时 `LOG_IS_ENABLE(x) = 1`（`:43`），即默认全开。
- 总开关：`apps/soundbox/include/app_config.h:9-15` —— `CONFIG_RELEASE_ENABLE` 时 `LIB_DEBUG=0`，否则 1；
  `CONFIG_DEBUG_LIB(x)` 展开为 `(x & LIB_DEBUG)`。
  **release 版无论怎么设都不输出**（`CONFIG_RELEASE` 在 Makefile 的 `-D` 里，见 `sdk-layout-build-and-flash.md`）。
- `CONFIG_DEBUG_ENABLE` 关闭时 `apps/common/debug/debug.c:6-61` 把 `putchar/puts/printf/put_buf/log_print`
  实现为**空函数** → release 零开销；`debug_lite.c` 提供 `CONFIG_DEBUG_LITE_ENABLE` 的轻量版本。

## 2. 串口 log 的物理参数（先确认这些再谈看 log）

demo 板：`TCFG_UART0_TX_PORT = IO_PORT_DP`（USB DM/DP 虚拟串口）、`RX = NO_CONFIG_PORT`（单发）、
`TCFG_UART0_BAUDRATE = 460800`（`board_ac695x_demo_cfg.h:45-48`）；初始化在 `board_ac695x_demo.c:855-864`。
**注意波特率是 460800 而不是常见的 115200**；115200 那组是**在线调音/配置工具**用的口。

- **异常现场打印的波特率/端口在 `isd_config.ini`** 的 `VDBG1_PORT`（port + 波特率编码）里，
  与运行期 UART0 log 不是同一套配置。
- 一份真实开机 log 样本可以直接对照学习：工程里的 `log.md`（含 `setup_arch`、`[SDFILE]VM size`、`sdfile mount succ`、
  `[BOARD]Power init`、`[USER_CFG]` 一串、`aec_cfg mic_gain/dac_gain`、`cur---1/new+++3` 模式切换）。
  **学会按 log 前缀 `[SDFILE]/[BOARD]/[USER_CFG]/[APP]` 反查打印点，是这套 SDK 最高效的读码方式。**

## 3. 断言（assert）的两种行为 —— 现场完全不同

`include_lib/driver/cpu/br23/asm/cpu.h:245-258`：

| `config_asser` | 行为 | 现象 |
|---|---|---|
| = 1 | 打印 `file / line` + `ASSERT-FAILD:`，然后 `cpu_assert_debug()` **停住** | 设备卡住不动，log 里能看到文件名与行号 |
| = 0（release 默认） | 直接 `cpu_reset()` | **表现为莫名复位**，没有任何断言信息 |

- 该常量在 `apps/soundbox/log_config/lib_system_config.c:23-27`，`CONFIG_RELEASE_ENABLE` 时为 0。
- **调试偶发复位时，先把 `config_asser` 打开**（手册《异常调试介绍》第 2 步就是它）。
- 异常入口：`cpu/br23/setup.c:52` 的 `exception_irq_handler` → `exception_analyze()`（`asm/debug.h:7`），
  注册在 `setup.c:246/248`；**但 `setup.c` 里那段解析实现整段被 `#if 0` 关掉，真实现在闭源库**。

## 4. 反汇编定位异常现场（手册《异常调试介绍》全部有效内容，共 3 步）

1. 在 `cpu/br23/tools/download.c` 里加一行生成反汇编清单：
   `%OBJDUMP% -D -address-mask=0x1ffffff -print-dbg %ELFFILE% > %ELFFILE%.lst`
   （**当前代码里这行存在但被注释**：`download.c:131`，且输出名是 `sdk.lst`，与文档写的 `sdk.1st` 不一致 —— 以代码为准。）
2. 把 `lib_system_config.c` 的 `const int config_asser = 1;` 打开。
3. 跑出异常后，按打印出的地址去 `.lst` 里查。

### 异常打印字段怎么读
打印的寄存器组：`usp / ssp / sp / Stack / rets / reti / retx / rete / psr / icfg /
sem_post_rets_addr / sem_rets_addr / mutex_rets_addr`；首行有 `0x5A5A5A5A5A5A` 与 `JL_LRCT->CON`。

- **`reti` = 异常触发位置**（当前 PC）；**`rets` = 异常位置返回地址**。
- 文档用蓝框标出的 `0x01E4BAB8 → 0x01E5D1C2 → 0x01E4BABC → 0x01E4BAC6` 是**异常触发前的 PC 调用链**。
- 文档明确警告：**"异常触发有可能不是第一现场"** —— 调用链要逐层往回核，不能只认 `reti`。
- `0x5A5A5A5A` 的含义（看起来是栈填充/哨兵值）**文档未解释**。
- 文档只给了"串口 log + lst 反汇编"这一条路；**JTAG/仿真、hardfault 专章、栈溢出专章：文档未提及**。
  栈相关的间接线索只能从 `Stack` 字段和 `0x5A5A5A` 猜，不可当依据。

## 5. 与死机相关的其他已知约束

- 任务栈必须是 **32 的倍数**（`task_table.c:5`）；栈给小了的典型表现就是随机 hardfault / 跑飞。
- 不可屏蔽中断优先级 6 以上不开屏蔽（手册能力表）。
- `IRQ_TIME2_IDX`（led7/数码管扫描）在 `TCFG_LED7_RUN_RAM` 时优先级为 **6**（关总中断仍能进），
  见 `apps/soundbox/board/br23/irq_config.c:12-17`。
- RT-Thread 侧的经验（`embedded/rt-thread/rt-thread-pitfalls.md`）里"PC 落在非代码段=调了未设置的函数指针"
  这类定位法在杰理上同理：**先看 PC/LR 落在哪个段，再去 `.lst` 对**。
