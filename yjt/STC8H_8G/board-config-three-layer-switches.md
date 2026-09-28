# STC8G/8H SDK：board_config.h 三层开关架构与编译期静态检查

> 适用：STC8G/8H 全系列（STC8H1K08/1K16/1K17 等）+ Keil C51 + STC 官方外设库（stc8g_8h_lib）+ common/drv 驱动框架
> 来源工程：STC8G_8H_SDK（公司公用 SDK：STC8H1K08/1K16 模板、laser-hair-84-e、test_gm-light-pressure）
> 目标：把「三层宏开关怎么分层、漏开依赖怎么在编译期报错、配置宏怎么分区」这套做法固化，新工程照搬不踩坑。

## 结论先行

配置只有一张 `board_config.h`，三层宏开关从上往下开：**库模块级 ENABLE → 库实例级 USE → drv 驱动层 USE**，层与层互不联动。漏开依赖不靠猜——文件末尾一段 `#if defined(A) && !defined(B) → #error` 静态检查区块，把缺的配置用人话在编译期直接报出来。无法用 `#error` 强制的（Timer0/Timer1 资源占用、GPIO 端口开关），用注释写死固定操作流程替代。

## 1. 三层开关架构

| 层级 | 宏前缀 | 控制什么 | 注意 |
|---|---|---|---|
| 库模块级 | `BOARD_CFG_STC8G_H_LIB_ENABLE_XXX` | `stc8g_8h_lib/` 里整个模块（`STC8G_H_UART.c` 等）要不要编译 | 最外层，关了下面两层全失效（链接错误） |
| 库实例级 | `BOARD_CONFIG_STC8G_8H_LIB_USE_XXX` | 库文件里 `UART1`/`PWM1`/`Timer0~4` 等常量是否定义，进而裁掉 `#ifdef UARTn {...}` 分支 | **前缀是 `BOARD_CONFIG` 不是 `BOARD_CFG`**，历史遗留、极易看漏 |
| drv 驱动层 | `BOARD_CFG_COMM_DRV_USE_XXX` | `drv_xxx.c` 要不要初始化对应实例 | 它的 switch/case 引用第 2 层常量，第 2 层没开却开了这层 → `undefined identifier`，报错位置隔一层难定位 |

不是所有外设都有实例级：UART/PWM/Timer/GPIO 有；ADC 没有（`Get_ADCResult(channel)` 运行时传参选通道，16 通道共用一份采样时序，天然无两层配置不一致问题）。

### PWM 额外多一层：组 vs 通道

- 组开关 `USE_PWMA/PWMB`：控制公共寄存器初始化（周期/死区/总开关/计数器）+ `NVIC_PWM_Init()`。
- 通道开关 `USE_PWM_CH1~CH8`：控制单通道 `PWM_Configuration(PWMn, ...)` 和引脚切换。
- **通道必须依赖所属组**（CH1~4→PWMA，CH5~8→PWMB），只开一边呼吸灯都不工作。静态检查区块里逐通道写了双重 `#error`。

### GPIO 特例：实例级裁剪没有编译期安全网

`GPIO_Inilize()` 按端口裁分支（`USE_P0~P7`）实测省 378~403 字节 ROM，但 `comm_drv_gpio_init(port, pin, mode)` 是运行时传参、没有 switch/case——**`USE_Pn` 没开而代码在用，不报任何编译错误或警告**，只是静默跳过该端口初始化（寄存器停复位态），且返回值 `FAIL` 没人接。处理办法写死在注释里：

> 改前先 `grep comm_drv_gpio_init(GPIO_Pn, ...)` 的实际调用点，核对 `board_config.h` 对应 `USE_Pn` 有没有开。不能像 Timer/UART 那样"编译过了就是对的"。

## 2. 静态依赖检查区块（编译期兜底）

`board_config.h` 末尾约 60 行 `#if defined(A) && !defined(B) → #error`，报错信息直接写"需要先打开 XXX"。已覆盖：

- UART1~4、Timer0~4 逐实例：驱动层开关 → 库层 `USE_XXX`
- 任意 UART/Timer/PWM 驱动开关 → 对应库模块级 `ENABLE_XXX`
- PWM：组→库层组；通道→库层通道 **且** 所属组驱动层开关
- GPIO 库模块强制常开（drv_gpio 只要参与编译就必须 `GPIO_Inilize()`）
- ADC：驱动开关 → `ENABLE_ADC`
- 跨层：`USE_INPUT/INPUT_LITE/OUTPUT` → 必须先开 `USE_SOFT_TIMER`（依赖 `tickCnt_Get()`）
- NVIC 综合检查：任意 UART/Timer/PWM/ADC 驱动开关 → `ENABLE_NVIC`（初始化都调 `NVIC_xxx_Init()`）

**无法强检、只能注释提醒的两条**：Timer0 被 apl_soft_timer 的 1ms tick 占用不可挪用；Timer1 被 `UART1_BRT = BRT_Timer1` 占用做波特率。原因：`BRT_Timer1` 这类常量在预处理 `board_config.h` 时对应的库头文件还没 include、取不到值，`#if` 表达不了。新增开关时记得同步在这个区块补检查。

## 3. 配置宏分区规则：按"有没有引脚选择"，不按"有没有实例编号"

- **"STC8G/8H 库用户驱动配置"区**：`USE_XXX` 开关 + 与走线无关的行为参数（如 ADC 采样时间/转换速度）。
- **"Driver pin config"区**：`PIN_SEL`/`BAUD`/`SPEED`/`DUTY`/`DEADTIME` 等硬件映射参数。换硬件版本只改这一个区。

判断标准是**这个驱动有没有"引脚选择"**：ADC 没有 → 全留一处；I2C 虽然也没有实例编号，但有引脚选择 → 仍拆两区（跟 UART/PWM 一个模式）。用"有没有实例编号"判断会分错。

## 4. 实例级裁剪的 ROM 收益（实测）

| 裁剪项 | 收益 | 备注 |
|---|---|---|
| `Timer_Inilize()` 按 `USE_TIMERn` 裁分支 | code -499 字节 | 2026-08-04，只开 Timer0；写法照抄 PWM 模式，每分支包 `#ifdef` |
| `GPIO_Inilize()` 按 `USE_Pn` 裁分支 | -403 字节（laser-hair-84-e 只开 P1/P3）；-378 字节（模板开 P0/P1/P3） | 2026-08-06；每分支内加 `return SUCCESS;`，无命中落 `return FAIL;` |

裁剪后每分支内部必须有返回值兜底，否则未命中端口时行为未定义。

## 5. 命名与目录约定

- 目录/文件：`common/drv/drv_xxx/drv_xxx.{c,h}`、`common/apl/apl_xxx/apl_xxx.{c,h}`，统一 `drv_`/`apl_` 前缀，目录名=文件名。
- 公开函数统一 `comm_drv_xxx_init(...)` 前缀，避免与第三方库/HAL 撞名。
- Include guard：`__COMM_DRV_XXX_H__` / `__APL_XXX_H__`。

## 6. 打印双方案一键切换

`board_config.h` 一个数字开关 `BOARD_CFG_COMM_PRINTF_BACKEND`：1=自研 kprintf，2=STC 库官方 printf。两套互不撞符——kprintf 的字符输出原语特意不叫 `putchar`（叫 `kprintf_putchar`），可以同时开、各走各的 UART。省 ROM 时砍格式项（不支持 `%X`/`%c`，用错只静默不出字符、不崩）。

## 7. 经验沉淀位置（本 SDK 内部）

- `project/stc8h_project/CLAUDE.md` — 核心技术坑复盘（本文件多数内容的原始出处）
- `project/stc8h_project/工程通用提示词.md` — 模块勾选清单 + 验证三件套工作流
- 改本 SDK 前先读这两份。
