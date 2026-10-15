# IAR / Keil IDE 调试与编译问题合集（含 RTT Studio、编码问题）

> 适用：IAR（EWARM，含 8051/AVR/ARM）、Keil MDK（ARM）、RT-Thread Studio
> 来源：《问题解决和汇总 v1.2》"IAR / 单片机(IDE类) / RTT STUDIO"章节
> 目标：IDE 层面"编译能过但调试诡异 / 跳转失效 / 链接报错"的处置手册。

## 结论先行

- IAR "Go to Definition 失效" 三种情况对应三套修法，核心都是 **Generate browse information** 开关 + 重新编译 + 等绿色进度条走完。
- **编译优化等级 Medium/High 会让调试时全局/局部变量全部不可见**——调试期把优化调低。
- 查内存/堆栈问题第一步永远是 **打开 map 文件**（Linker→List 勾选生成）。
- 工程里出现诡异编译错误（missing closing quote、中文路径、乱码）先查**文件编码与路径特殊字符**。

## 1. IAR

### 1.1 Go to Definition 失效（三种情况）

| 现象 | 修法 |
|---|---|
| 菜单灰色 | Tools→Options→Project 勾选 Generate browse information，重新编译 |
| 单击有声音但不跳转 | 取消勾选→重新编译→再勾选→再重新编译（清除过期 browse info，四步缺一不可） |
| 提示 C 文件路径错误 | 同上四步（改过工程目录后 browse info 过期） |

无论哪种，编译后底部绿色进度条必须等它走完。

### 1.2 调试观察类

- **优化等级 Medium/High 后全局变量、静态/局部变量值都不可见**：调试时把优化等级调低（None/Low）。
- **单步时读寄存器值不正确**：给寄存器写值的过程中停下来，读出的数据不可靠且无法继续执行；断点放在合适的交互完成位置，或把值赋给变量观察。
- **调试窗口读不出数值**：改数据显示类型（如 HEX）即可读出。
- **断点太多删不动**：调试界面 View→Breakpoint 窗口，逐条 Delete（可长按）。
- **AVR 仿真中全局变量值不断乱变**：① 查堆栈溢出（Options→Linker→List 生成 map，看堆栈与 RAM 占用；Tools→Options→Messages 可显示资源占用）；② 整理结构体成员排列（float/int/char 混排受编译对齐影响）——整理后消失即对齐问题。

### 1.3 编译/链接类

| 报错 | 原因与修法 |
|---|---|
| `Error[Pe018]/Pe020/Pe140`（mpu_armv7.h） | IAR 不认 `__restrict`：宏改成 `#define __RESTRICT restrict` |
| `ELF/DWARF Error: Unsupported .debug_info format version:4` | 链接的库调试信息版本不兼容（高版本 IAR 生成）；换 gcc 编译的库正常 |
| `Error[Pe008]: missing closing quote` | 源文件含特殊字符/编码问题，改文件编码设置 |
| `Undefined external "?V8"/"?V9"/"?V10" referred in sb_exec`（zstack） | 栈相关配置，改为 8 |
| `Error[e104]: XDATA_N 放不下（CC2530，0x802 > 0x669）` | XDATA 溢出：减小堆 `INT_HEAP_LEN`（2048→更小） |
| `Error[Pe040]: expected an identifier` | 标识符重定义，屏蔽重复定义处 |
| `expected specifier-qualifier-list before '_READ_WRITE_RETURN_TYPE'` | 缺声明：`#include <sys\reent.h>`；注意头文件保护宏不要与其他文件冲突 |
| `Undefined external led_init (L6218E 类似)` | 工程目录里没添加对应 .c 文件（Keil 同类问题见下） |

### 1.4 未解决留档

- CC2530 配置 CLKCONCMD（0xC6）后数值读取超栈报警，疑似硬件报错，未解决；
- CLK 寄存器写 CLKSPD=16 时仿真器报错，未解决。

## 2. Keil MDK

| 报错/现象 | 原因与修法 |
|---|---|
| `error: #65: expected a ";"`（引用 xprintf 的 serial.h 时） | serial.h 缺少依赖的头文件（4 个），补上即好 |
| `L6218E: Undefined symbol led_init (referred from main.o)` | 头文件声明了但工程目录下没有/没加对应 .c |
| `L6050U: code size exceeds maximum` | 评估版限制，需正式授权 |
| `Error: Flash Download failed - Could not load ..\OBJ\Template.axf` | axf 是编译产物：先查有没有编译错误；axf 输出路径可在 Options→User→After Build/Rebuild Run# 指定，一般留空 |
| `warning: #3731-D: intrinsic is deprecated`（FreeRTOS/CMSIS 4.3.0 + AC5.06） | `__ldrex/__strex` 等内建函数被 AC5.06 弃用：忽略该警告，或把 CMSIS 包升级到 4.3.0 以上 |
| `最后一段缺少新行` warning | 文件末尾补一个空行 |
| 结构体成员自动提示失效 | 把前面的定义补完整后再写 |
| RT-Thread 工程在 Keil 打开乱码 | 右键工程→属性→编码改 GBK（源文件是 GBK 编码） |
| 旧版库函数用高版本编译器编译报 38 个错误 | 编译器版本选择切到 V5.06（Use default compiler version 改掉） |

## 3. RT-Thread Studio

- `arm-none-eabi-gcc: not found`：安装 gcc 工具链包。
- 通用 IDE 基础知识统一维护在《KEIL_MDK-IAR-GCC-MinGW软件基础知识.docx》。

## 4. CMSIS 组件速记（排包版本问题时用）

CMSIS 标准化 Cortex-M 硬件抽象：CORE（核心）、DSP（数学/滤波）、NN（神经网络推理）、RTOS/RTOS2 API、Driver、Compiler（AC5/AC6 扩展）、Device、File System、Graphics、Network、USB。遇到 #3731-D 类警告先看 CMSIS 包版本。
