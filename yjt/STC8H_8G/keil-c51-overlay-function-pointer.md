# Keil C51：OVERLAY 优化看不见函数指针调用——回调局部变量覆盖调用方（严重）

> 适用：一切 Keil C51（BL51/LX51）工程，不限 STC；只要代码里存在函数指针调用（回调/状态机表/pubsub/软定时器）就适用
> 来源工程：STC8G_8H_SDK（2026-08-04 INPUT_SCAN + softTimer_Update 实际死过一次）
> 目标：把「为什么会死、规则怎么定、怎么自动化验证、哪些替代方案已排除不用再试」一次讲清。

## 结论先行

**规则：任何"通过函数指针调用别的函数"的函数（调度者），自己的局部变量必须声明 `static`。** 这类 bug 编译 0 Error 0 Warning，只有跑起来才暴露，且是否触发与对象个数、调用层数强相关——测一次没崩不代表没问题。SDK 已配自动检查脚本 `check_overlay_safety.py`，编译后跑一遍即可，免维护函数名单。

## 1. 原理

BL51/LX51 靠静态调用图做 overlay（不同时执行的函数共享局部变量存储空间，省 DATA/BIT）。这张图只认源码里看得到符号名的**直接调用**；函数指针调用（`obj->func()`、`arr[i].func()`、`(*fp)()`、回调注册）是**不可见的边**。如果 A 通过函数指针调 B，链接器可能把 A、B 的局部变量分到同一块 DATA 地址——B 一写自己的局部变量就覆盖 A 正在用的循环变量/指针。

## 2. 规则细则

- 按调用点算，不按嵌套深度算——每多一处间接调用都要单独处理。
- 被调用的回调本身**不用**加 `static`（除非它自己又通过函数指针调别的函数，那它变成新的调度者，规则再套一层）。
- `static` 不支持重入：加了 static 的调度函数只能固定在主循环里调，**不能再被中断嵌套调用**，否则中断那次调用会冲掉主循环还没用完的局部变量。这条要写在函数头注释里。

## 3. SDK 的落地方式：宏开关体系

四个开关集中在 `board_config.h`，**默认全为 1（安全）**：

```c
#define BOARD_CFG_COMM_DRV_INPUT_SCAN_STATIC_LOCALS          1  /* drv_inputex Input_Scan() */
#define BOARD_CFG_COMM_DRV_INPUT_LITE_SCAN_STATIC_LOCALS     1  /* drv_inputex_lite InputLite_Scan() */
#define BOARD_CFG_COMM_DRV_OUTPUT_STATIC_LOCALS              1  /* drv_outputex OutGroupScan()/OutsStatusUpdate() */
#define BOARD_CFG_COMM_DRV_SOFT_TIMER_UPDATE_STATIC_LOCALS   1  /* apl_soft_timer softTimer_Update() */
```

实现侧（`drv_input_lite.c` / `apl_soft_timer.c`）：

```c
#if BOARD_CFG_COMM_DRV_INPUT_LITE_SCAN_STATIC_LOCALS
#define INPUT_LITE_SCAN_STATIC static
#else
#define INPUT_LITE_SCAN_STATIC
#endif

void InputLite_Scan(void)
{
    INPUT_LITE_SCAN_STATIC uint8_t i;
    INPUT_LITE_SCAN_STATIC input_lite_obj_t xdata *obj;
    ...
}
```

关掉开关前必须用脚本验证过；开关存在只是为了极端省 DATA 时的逃生口，不是常规操作。

## 4. 自动验证脚本 check_overlay_safety.py（三项检查）

用法：`python check_overlay_safety.py Listings/<工程>.map`；退出码 1 = 有确认碰撞。

- **Check 1（核心）**：自动扫描 `Source/` + `common/` 源码，用 4 种正则发现调度函数（`obj->f()`、`arr[i].f()`、`(*fp)()`、函数指针数组 `subs[id](...)`）；再用"函数名裸词出现且后面不跟括号"识别地址被取用、可能作回调的函数；与 `.map` 里 `OVERLAY MAP OF MODULE` 段逐函数的 `DATA_GROUP` 交叉比对，**地址区间重叠即报 `[风险]`**。安全标志：调度函数的 DATA_GROUP 应为 `-----`（已移出覆盖池）。免维护名单，新增回调/调度函数不用改脚本。
- **Check 2**：从 `Program Size: data=...` 解析 SMALL 模型 128 字节 DATA 余量，剩余 ≤8 字节告警。
- **Check 3**：统计 `.map` 里 `?C?...PTR...` 通用指针运行时分派符号的总字节数（只提示），数字偏大说明哪里新写了未加存储区限定符的指针。

脚本只做静态文本扫描，会漏报/误报宏展开的诡异写法——报告要肉眼复核，"没问题"也不能替代实机验证。

## 5. 已排除的替代方案（不用再试）

| 方案 | 为什么不行 |
|---|---|
| 改 `.uvproj` 的 `OverlayString` 声明调用边 | 能修，但配置在项目文件里，重新生成/覆盖就丢，且要手工维护名单 |
| 全局 `NOOVERLAY` | 局部变量总量超 SMALL 模型 128 字节 DATA，链接溢出 |
| 回调标 `reentrant` | 库函数（如 printf）本身不是 reentrant 躲不开，还拉回已优化掉的软件栈开销 |
| `#pragma NOOVERLAY` | Keil C51 不支持，被忽略 |
| 只改回调侧不改调用方 | 回调地址常被自己模块内部更深的调用链钉死，应用层改不了；**永远优先改调用方/框架侧** |

## 6. 关联坑：DATA 空间紧张时的配套做法

- 调度函数里"重量级"局部数组（如 11 字节的进制转换 buf）直接挪 `xdata`，不参与 overlay 争用（apl_kprintf 的做法）。
- 指向 xdata 对象的指针**必须写明 `xdata`**（`input_lite_obj_t xdata *`），否则退化成 3 字节通用指针、每次访问走 `?C?PSTOPTR` 运行时分派，白占几百字节 ROM。
