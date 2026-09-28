# STM32 / HAL 库经典坑合集（初始化顺序 / 时钟 / printf / 中断 / HardFault）

> 适用：STM32（F1/F4 实测）+ HAL/标准库 + FreeRTOS/CLI，兼含 CC2530(ZStack) 个例
> 来源：《问题解决和汇总 v1.2》"单片机 / HardFault_Handler"章节（约 28 个实例）
> 目标：把"配置看不出问题但就是不工作"类的经典坑一次记牢。

## 结论先行

高频三板斧：① **时钟先使能才能写寄存器**（且用对时钟宏，别用睡眠模式时钟）；② **printf 重定向要 fputc + `struct __FILE` + `_sys_exit` 三件套**，缺后半会"点几次运行才跑"；③ **PA13/14/15、PB3/4 默认是 JTAG 引脚**，复用前必须释放，否则外设"莫名"不工作。

## 1. GPIO / 外设初始化

- **地址变量保持一致**：两段初始化（LED/BEEP）里 `GPIO_Init()` 的外设基址指针必须各自正确——写错会让地址区间互相覆盖，两个外设都不工作。
- **初始化顺序**：`GPIO_InitTypeDef GPIO_InitStructure;` 必须放在函数第一段，整体顺序不能乱。
- **蜂鸣器不响**：直接写 ODR 不行，要用 `GPIO_SetBits/GPIO_ResetBits` 置复位（实测验证）。
- **定时器中断里用完必须清中断标志**，否则跳不出中断服务函数。
- **中断服务函数里不要做 ADC 转换采集**：会造成定时器无法初始化、系统卡死。
- **extern 规则**：跨文件用的全局变量在 .c 定义、.h 里 extern 声明；函数内"先定义后赋值"，static 局部变量可保持数据不随函数退出丢失。

## 2. 时钟

- **串口配置无误却无法通信**：时钟使能用错了宏（用了睡眠模式下的时钟），换成正常运行时钟宏后正常。
- **HAL/RTT 时钟使能顺序**：只有先使能时钟才能修改寄存器；在 main 里使能不行——**要在驱动注册/初始化之前使能**（初始化函数内部自己使能最稳）。
- **时钟配置错误导致串口输出乱码**：`System_stm32f4xx.c` 开头的 PLL 参数（外部晶振 8MHz 时 PLL_M 25→8），**且必须同步改 `stm32f4xx.h` 的 `HSE_VALUE`**（25000000→8000000），两处一致后才正常。
- **PB3/PA13/PA14/PA15 默认 JTAG 功能**：TIM2 用 PB3、或把这些脚做 IO 用时，复用配置后仍需**失能 JTAG-DP**（代码里注释对应使能语句）；正常设计应避免这类冲突。
- **调试器用四线制 SWD**：st-link/jlink 通用，四根线对应接好即可。

## 3. printf / 半主机模式

现象：加入 printf 支持后，运行程序需要点几次运行按钮才跑。
原因：只定义了 `fputc`，缺标准库支持函数。三件套：

```c
struct __FILE { int handle; };
FILE __stdout;
void _sys_exit(int x) { x = x; }   /* 避免半主机模式 */
int fputc(int ch, FILE *f) { usart1_put(ch); }
```

## 4. HardFault / 内存踩踏

- **strcpy 硬件错误**：源字符串长度超出目标区域。实例（FreeRTOS CLI 移植）：串口工具发的命令自带 `\r\n`，程序把两者都当回车 → 命令处理两次 → 发送缓存被撑爆 → `_CLI_DMA_SendBuff[CLI_DMA_Send_len++]` 越界覆盖相邻的 `cInputString`（只有 50 字节）。教训：**DMA 一次性整串发送时缓存要给足，len 递增前检查边界**；用 cmbacktrace/跟踪工具从 strcpy 回溯。
- **初始化内存管理/FATFS 时硬件错误**：main 里 FATFS 测试把栈用爆。定位法：屏蔽文件系统代码段后正常 → 加大栈空间。
- **`FPU active!` + bus fault**：数组越界/指针非法访问，先查自己写的接口（详见 rt-thread-pitfalls.md 的 PC/LR 定位法）。
- **sprintf 全局变量导致 LCD 显示异常**：局部正常、挪到全局后被篡改（320 变 256），疑似内存踩踏，未解决——留档勿引用结论。

## 5. 工具链

- **CubeMX "copying libraries files" 卡死**：工程路径含特殊字符/中文，把工程拷到纯英文路径再生成。
- **F103 无法调试（jlink/st-link 均 `FAILED TO GET CPU status after 4 retries`）**：注释代码中相应调试配置语句后恢复（详见调试器篇/原文档截图）。
- **CC2530 XDATA 段放不下**（`Unable to place 2 block(s) ... in XDATA`）：减小 `INT_HEAP_LEN`。
- **库函数 + 编译器版本不匹配**：旧库用高版本编译器报几十个错，编译器版本切到 V5.06（详见 iar-keil-ide-issues.md）。
