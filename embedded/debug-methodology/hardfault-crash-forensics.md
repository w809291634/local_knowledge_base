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
