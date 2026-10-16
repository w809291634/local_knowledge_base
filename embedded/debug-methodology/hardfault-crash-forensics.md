# 死机与异常取证（HardFault / 栈溢出 / 内存越界）

> 本篇是从《单片机外设和调试基础知识.docx》的"单片机调试基础方法"章提炼，与已有的
> `debug-methodology.md`（四种通用打法）、`rt-thread-pitfalls.md`（PC/LR 定位法）、
> `logging-exception-debug.md`（杰理侧反汇编与异常字段）互补，**共同构成"崩溃现场怎么读"的一套完整方法**。
> 新增来源：`embedded/mcu-peripherals/` 精读，2026-10-16。

## 1. 硬件错误（跑飞/复位/卡死）的定位顺序

| 步 | 做法 | 判读 |
|---|---|---|
| ① | 看 **callstack** | 有栈就直接定位到调用点 |
| ② | 没有打印、callstack 也出不来时 | **逐个关线程**（一次停一个任务）复现 —— 二分式缩小到具体线程 |
| ③ | 引入 **`cm_backtrace`** 软件包 | 打印调用栈、任务名、栈用量 |
| ④ | 查出错时的 `stack` 信息 | 原理可看 `pxCurrentTCB->pxStack`、`pcTaskName`（FreeRTOS 语境） |
| ⑤ | 查内存操作 | **没有出现报错时，重点盯 `memset` / `memcpy`** —— 尤其中 `memset` 长度写错打到别处的空指针区 |

> 步骤 ⑤ 是原作者反复踩出来的经验：**没有异常信息 ≠ 没问题，多半是越界写把别的结构写坏了**。

## 2. `memset` 长度写错这一类（可直接抄进自检清单）

```c
memset(&sta_info_tab[i], 0, sizeof sta_info_tab);   // ✗ 清的是整个数组（实测 sizeof=140，单个元素=28）
memset(&sta_info_tab[i], 0, sizeof(sta_info_t));    // ✓ 正确：按元素类型
```
症状：加一行代码后别的数据莫名归零 / 状态机随机错乱。
**自检法**：`memset/memcpy` 的第三个参数**一律用类型名或 `sizeof(*p)`**，不要用数组名；
对"元素 i 起清零"的写法做一次 `sizeof` 打印验证。

## 3. 栈溢出的判据（Cortex-M 全满降栈）

| 项 | 正确读法 |
|---|---|
| 溢出判据 | **SP < 栈的最低地址**（即栈底警戒线）才溢出。文档把最低地址叫"栈起始地址"并说"向上增长"，**方向写反** `⚠校核见 mcu-peripherals/ERRATA B` |
| 先看 PC | PC 落在**非代码段**（尤其是 `0`）⇒ 执行了 0 地址函数（回调函数指针没设置就调用） |
| 再看 LR | LR ⇒ 调用出错函数的位置 |
| 看 xPSR | Mode（Thumb 位必须为 1）、Privilege |
| 修法 | 栈 1KB → 4KB/8KB；禁大局部数组（改 static 或全局）；必要时动态分配 |
| SP 对齐 | SP 低 2 位恒 0（4 字节对齐） |

与 `embedded/rt-thread/rt-thread-pitfalls.md` 的结论一致：**RT-Thread 里
`assertion failed at function: rt_thread_sleep/rt_thread_control/rt_timer_*` 绝大多数就是线程栈溢出**。

## 4. 异常现场的寄存器清单（调试器怎么读）

| 寄存器 | 含义 |
|---|---|
| `R0~R12` | 通用寄存器；**16 位 Thumb 指令只能访问 R0~R7** |
| `R13/R14/R15` | = SP / LR / PC |
| `xPSR` | = APSR + IPSR + EPSR 合并；IPSR 给出当前异常号 |
| `MSP/PSP` | **banked**，同一时刻只可见一个（由 CONTROL 决定） |
| `S0~S31` | 只有 FPU 使能才存在（M4F/M7） |
| 异常现场打印（杰理侧同款） | `usp/ssp/sp/Stack/rets/reti/retx/rete/psr/icfg/sem_post_rets_addr/sem_rets_addr/mutex_rets_addr`；**`reti`=异常触发位置（当前 PC），`rets`=返回地址**；调用链要逐层回核，"**异常触发有可能不是第一现场**" |

## 4.1 截图层补充（第 1 章，2026-10-16 逐张读）

原文"异常现场怎么读"只有两张截图有实值，文字层没有 ⇒ 录下来当**读法样板**。

### (a) Keil `Registers` 窗口的 HardFault 现场（ch01/013）

| 寄存器 | 截图值 | 当场读法 |
|---|---|---|
| `R0` | `0x2004AF64` | 落在 SRAM ⇒ 多半是**结构体/缓冲区指针**，可拿去 Memory 窗口看内容 |
| `R1` | `0x2002E488` | 同上，SRAM |
| `R2` | `0x000000F0` | 小整数 ⇒ 像**长度/计数**（`memset` 第三参这类） |
| `R3` | `0x00000037` | 小整数 |
| `R4` | `0x2004B036` | SRAM，与 R0 相差 0xD2 ⇒ 同一块缓冲内 |
| `R5` | `0x00000018` | 24，像 size |
| `R6` | `0x00000001` | 常量/标志 |
| `R7` | `0x0000005E` | |
| `R8~R11` | `0x20009676` / `0x2000EDB8` / `0x0003813` / `0x00000002` | |
| `R12` | `0x80000000` | **不在任何合法段**（既非 flash 也非 SRAM）⇒ 若它被当地址用就是坏指针 |
| `R13 (SP)` | `0x2004AF80` | 与 R0/R4 同区 ⇒ **栈就在那块缓冲附近**，符合"越界写/深递归"形态 |
| `R14 (LR)` | `0x0FFFFFE9` | **EXC_RETURN 值**（`0xFFFFFFF9` 系）⇒ 说明是从异常里取的返回标记，**不是函数返回地址**；此时真正的返回地址在**栈帧里的 LR**，要手工出栈看 |
| `R15 (PC)` | `0x080003A2` | 在 flash 代码段 ⇒ 不是"PC=0 跑飞"型，属"执行到某条合法指令崩了"，直接反汇编该行 |
| `xPSR` | `0x21000003` | 低 9 位 `IPSR=3` ⇒ **HardFault**；bit24=1 ⇒ Thumb 位正常 |
| 下方 `Mode / Privilege / Stack` | `Handler` / `Privileged` / `MSP` | 与 `EXC_RETURN=...F9`（用 MSP）互相印证 |

**可复用的三条判读规则**：
1. `LR = 0x0FFFFFFEx` 形态 ⇒ 这是异常返回魔数，**别把它当调用者地址**；去 SP 处按 8 字长取栈帧（R0~R3、R12、LR、PC、xPSR）。
2. `xPSR` 低 9 位直接给异常号（3=HardFault），比"猜是不是死机"快。
3. `Mode=Handler + Stack=MSP` ⇒ 崩在**中断上下文**，排查方向是 ISR 里调了阻塞/长耗时 API（见 §6 最后一行）。

### (b) 用 `Debug register` 窗口直接读外设寄存器（ch01/001）

同一窗口里并排开两个外设（截图是 `TIM4` 与 `TIM6`）做对照：

| 观察 | 结论 |
|---|---|
| 左边 `TIM4`：`CR1=0x00000005`、`CNT` 非 0、`PSC=0x00000001`、`ARR=0x000044AD` 量级 | 定时器**真的在跑**（CR1 的 CEN+UDIS 位、CNT 在计） |
| 右边 `TIM6`：`CR1/SMCR/DIER/CCR*` 全 0，只有 `SR=0x00000001`、`DIER=0x00000001` | 使能了中断但 **CR1 没置 CEN ⇒ 计数器没启动**；`SR` bit0=UIF 已挂起 ⇒ "配了不跑/不进中断"的典型形态 |

⇒ **用法**：怀疑"配置没生效"时，不要只看代码，直接在调试器里开 `Debug register` 窗口把两个定时器并排比，
`CNT` 会不会动、`CR1.CEN`、`DIER`、`SR` 四个点一眼就能分出"没启动 / 没使能中断 / 标志没清"。

### (c) `memset` 类越界的现场形态（ch01/002）

截图是 Keil 停在 `GUI__memset`（emWin 的清零函数）时，左侧开反汇编窗口、右侧开 Locals 的对照画面。
可复用的只有一条：**emWin/GUI 场景下"画面莫名花掉、控件数据归零"，先看是不是 `memset` 长度参数错（§2），
断点打在 `GUI__memset` 上比打在自己业务函数上更早看到越界写**（截图字号过小，其余细节未提取，`⚠校核D`）。

## 5. 让断言把话说清楚（调试前必开）

| 配置 | 行为 |
|---|---|
| `config_asser = 1` | 打印 `file / line` + `ASSERT-FAILD:` 后 `cpu_assert_debug()` **停住** |
| `config_asser = 0`（release 默认） | 直接 `cpu_reset()` ⇒ **表现为莫名复位、零信息** |
| 杰理侧位置 | `apps/soundbox/log_config/lib_system_config.c`；`CONFIG_RELEASE_ENABLE` 时为 0 |
| 配套动作 | 在构建脚本里打开反汇编导出（`objdump -D -address-mask=… -print-dbg %ELFFILE% > %.lst`），出异常后按地址查 `.lst` |

**调试偶发复位的固定开局**：先把 assert 打开 + 生成 `.lst`，再复现。

## 6. 屏蔽手段与"崩在哪一层"的对应

| 现象 | 可能层 | 依据 |
|---|---|---|
| 进 HardFault 且 PC=0 | 函数指针未初始化就被调用（回调/状态机表/pubsub） | §3 |
| 随机复位、无日志 | 断言被编译成 `cpu_reset`，或 `PRIMASK` 下长时间关中断触发看门狗 | §5 |
| 数据莫名被清 | `memset/memcpy` 长度错 | §2 |
| 只在高负载时崩 | 任务栈不足（栈必须 32 的倍数，见杰理 `task_table.c`）/ FreeRTOS `configCHECK_FOR_STACK_OVERFLOW` | §3 |
| 中断里调用 API 后死锁 | 中断优先级数值低于 `configMAX_SYSCALL_INTERRUPT_PRIORITY`，或在 ISR 里调 `HAL_Delay` | 见 `mcu-peripherals/clock-gpio-nvic-exti.md` §4/§5 |

## 7. 可选增强（原文提法已核对）

- **开启栈保护（如 `-fstack-protector`）可检测栈溢出** `⚠校核`：该项检测的是缓冲区溢出（canary 被改），
  **不能可靠发现深递归/静态栈越界**；裸机还需要编译器/链接器提供 canary 支持。当作"辅助"而非"判据"。
- MPU 做区域保护（把空闲区设为不可写）能更早暴露越界写；注意 **CM7 的 MPU region 最小 32 字节**
  （文档两处写 256 字节，与其自身另一处"最小 32"矛盾，`⚠校核B`）。
- `assert_param` 由 `USE_FULL_ASSERT` 控制，失败会进 `assert_failed(__FILE__,__LINE__)` 死循环；
  **发布版必须关掉**。
