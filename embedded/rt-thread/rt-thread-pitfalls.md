# RT-Thread 踩坑合集：hard fault 定位 / 线程栈溢出 / 定时器上下文 / emWin 案例

> 适用：RT-Thread（4.x 实测）+ Cortex-M（STM32F4 等）+ emWin 场景
> 来源：《问题解决和汇总 v1.2》"rtthread / RTT STUDIO"章节（约 15 个实例）
> 目标：把 hard fault 定位方法、栈溢出的统一根因、定时器回调上下文限制固化下来。

## 结论先行

- RT-Thread 里 `assertion failed at function:rt_thread_sleep/rt_thread_control/rt_timer_*` **绝大多数是线程栈溢出**——启动时占用很小，一跑业务（按键处理、JSON 发送）就涨满，第一反应加大线程栈。
- hard fault 定位先看 **PC 和 LR**：PC 落在非代码段（尤其 0）→ 执行了 0 地址函数（回调未设置就调用函数指针）；LR → 调用出错函数的位置。配合 **cmbacktrace** 软件包可打印完整调用栈。
- `RT_TIMER_FLAG_HARD_TIMER` 的超时回调跑在 **tick 中断上下文**，回调里不能调 `rt_mutex_take` 等 "shall not be used in ISR" 的 API；要互斥就换 `SOFT_TIMER`（timer 线程上下文）。

## 1. hard fault 定位方法

### 1.1 寄存器读法

- **PC**（程序计数器，下一条指令地址）：PC=0 或任何非代码段地址都不正常——通常是回调函数未设置就直接执行了函数指针。
- **LR**（R14，子程序返回地址）：记录 PC 执行后的返回地址，即**调用错误函数的位置**，从这里回溯。
- 硬件错误三大来源：内存溢出/访问越界、堆栈溢出、中断处理错误。R0-R12 是通用寄存器；Cortex-M 有双堆栈指针 MSP（内核/异常用）与 PSP（应用用），堆栈 4 字节对齐。
- RTT 下 hard fault 会进入 `rt_hw_hard_fault_exception()` 打印寄存器现场（psr/r0-r12/lr/pc + 线程名）。

### 1.2 cmbacktrace 实操（完整案例）

- 安装 cmbacktrace 软件包，基本免配置，打印设为 UTF-8 中文；每次 hard fault 会刷新 `rtthread.elf`，用 cmd/git-bash 执行其 addr2line 解析脚本即可得到出错源码行。
- 实战案例（emWin gui 线程 hard fault，反复换页触发）：解析指向 `stateBarDLG.c` 的 `GUI_SetBkColor` 前一段画图代码；用"不断触发消息"验证稳定性；屏蔽后消失。最终根因是**两个窗口都用了 `WM_CreateTimer(...,1000,0)`，定时器消息与 key 线程的换页消息冲突 + GUI 线程优先级过低（15，低于 key 的 8）**——提高 GUI 线程优先级后解决。
- 排查小技巧：在嫌疑消息发送处加 `rt_kprintf` 后死机消失，往往是时序/优先级问题的信号。
- emWin 规则：处理 `WM_PAINT` 时回调除重绘外不得调用 `WM_SelectWindow/WM_Paint/WM_DeleteWindow/WM_CreateWindow/WM_Move/WM_Resize` 等改窗口属性的函数。

## 2. 线程栈溢出（assertion failed 系列的统一根因）

| 现象 | 实例 | 处理 |
|---|---|---|
| `rt_thread_sleep` assertion | gui 线程栈 1024 太小 | 加大到 2048 |
| `rt_timer_control` assertion（按键后） | key 线程未按键时栈占用 17%，点按键/tab 后猛涨 | 加大 key 线程栈 |
| `rt_timer_stop` assertion + `thread:sensor stack overflow` | 发送 JSON（`{"method":"sensor",...}`）时溢出 | 加大 sensor 线程栈 |
| `rt_thread_control` assertion | tcp 接收线程溢出，看堆栈定位线程 | 同上 |

规律：`rt_thread_create(..., stack_size, priority, slice)` 的 stack_size 宁大勿小；启动占用小不代表运行时占用小。

## 3. 定时器回调上下文（HARD_TIMER vs SOFT_TIMER）

- `RT_TIMER_FLAG_HARD_TIMER`：超时回调在**滴答时钟中断服务例程**上下文执行——里面不能互斥量、不能阻塞；
- `RT_TIMER_FLAG_SOFT_TIMER`：回调在系统 **timer 线程**上下文执行（timer 线程由 `timer.c` 在系统初始化时创建）。
- 事故：在硬定时器超时回调里启动了涉及互斥/线程的操作 → `Function[rt_mutex_take] shall not be used in ISR`。改用软件定时器（回调来自 timer 线程）后正常。

## 4. 其他坑

- **定时器/线程不要在别的线程里删**：`rt_timer_control/rt_timer_stop` assertion 的另一来源是跨线程删除对象；删除动作放到对象所属上下文（线程外）。
- **rt_kprintf 打印不了浮点数**：`kservice.c` 的 `rt_kprintf` 默认不支持 `%f`，在文件头部加 `#include <stdio.h>` 后可打印。
- **RTC 时间戳溢出**：向系统注册 RTC 设备后时间显示错乱——系统时间戳用**有符号 long（32 位）**，表示 1970 前后，最大 2,147,483,647（2038 年溢出）；直接读 RTC 芯片数据正确、经系统转换后错乱，就是时间戳范围/负值处理问题。
- **串口卡死在 `while (__HAL_UART_GET_FLAG(..., UART_FLAG_TC) == RESET)`**：`TXE`=发送数据寄存器空（可写下一个字节），`TC`=发送移位寄存器全部移完；初始化/关闭时机要分清用哪个标志。
- **空指针访问**（出现"切换到 mac 窗口"类异常画面）：`eth_zy->net->netMac` 未判空——在可疑点前打断点单步，先怀疑前一段代码。
- **`FPU active!` + bus fault（PRECISERR）**：不是系统问题，是自己函数内部数组越界/指针非法访问；先检查自己的接口。
- **同一 SPI 总线重复挂载**：`rt_hw_spi_device_attach` 对同一总线设备挂载多次会出错。
- **W25Qxx 读 ID 后 hard fault on main**：排查顺序——main 是否 include `<rtthread.h>`；线程栈是否够；SPI 挂载是否重复；清掉全部断点再试。

## 5. RTT STUDIO

- 编译报 `sh: arm-none-eabi-gcc: not found`：未装/未配置 gcc 工具链，安装 arm-none-eabi-gcc 包。
- Keil/MDK/IAR/GCC/MinGW 基础知识统一维护在《KEIL_MDK-IAR-GCC-MinGW软件基础知识.docx》。
