# STC8G/8H SDK 工作流纪律：验证三件套 / 编码 / 工程文件 / 并发 / 提交规范

> 适用：STC8G/8H SDK 及所有下游 Keil C51 工程
> 来源工程：STC8G_8H_SDK（project/stc8h_project/工程通用提示词.md + CLAUDE.md + .trae/rules）
> 目标：改动前必读清单 + 改完必做验证，固化成流程，不靠记忆。

## 结论先行

**验证三件套**是硬性收尾：UV4 命令行编译 0 Error → `check_overlay_safety.py` 无 overlay 碰撞 → 看 Program Size 的 data/code 是否异常。改动前四条必读：GBK 文件用 GBK 方式改；新增 .c/.h 同步加 .uvproj；`data` 不能当名字；调度函数局部变量 static。

## 1. 改动前必读

1. **函数指针回调**（状态机表/软定时器/pubsub）：发起间接调用的调度函数局部变量必须 `static`，否则 OVERLAY 可能分到同一块 DATA，0 Error 但运行时死机。详见 `keil-c51-overlay-function-pointer.md`。
2. **编码**：见下面第 2 节，改错编码会静默乱码或匹配失败。
3. **新增 `.c/.h` 记得同步加进 `.uvproj`**——忘了报 `UNRESOLVED EXTERNAL`，报错位置跟真正缺的东西隔一层，很难看出来的那种。
4. **`data` 不能当变量/形参名**（C51 关键字），一律叫 `dat`。
5. **给 `...` 传指针一律 3 字节通用指针**，别凭直觉判断变参字节数。详见 `keil-c51-language-pitfalls.md`。
6. **多会话并发改同一文件会互相覆盖、不报错**，保存前 `git diff` 确认自己的改动还在。

## 2. 文件编码分区（易踩）

| 文件 | 编码 | 改法 |
|---|---|---|
| `board_config.h`、`stc8g_8h_lib/*.c/.h` | **GBK + CRLF** | `io.open(path, encoding='gbk', newline='')` 读写；UTF-8 假设的工具会静默乱码/匹配失败 |
| `Source/*.c/.h`、`common/apl`、`common/drv` | 通常 UTF-8 | 正常读写 |

## 3. 验证三件套（改完必做）

```bash
# 1. 命令行编译, 确认 0 Error
UV4.exe -j0 -r <工程>.uvproj -o build.log

# 2. overlay 安全校验, 退出码必须 0
python check_overlay_safety.py Listings/<工程>.map

# 3. 看 build.log 末尾 Program Size: data/xdata/code 有无异常
#    SMALL 模型 data 上限 128 字节, 超 90% 就要留意, 别等真溢出
```

## 4. 外设复用端口：位掩码重叠检查

**事故**：加 ADC 示例时写 `comm_drv_gpio_init(GPIO_P1, GPIO_Pin_All, GPIO_HighZ)`，`GPIO_Pin_All` 把 PWM1（P1.0/P1.1）、PWM2（P1.2/P1.3）已在用的引脚也设成高阻输入，**覆盖了 PWM 输出**。

**规则**：新加驱动示例只要与其他驱动共用端口，先看位掩码是否全占了；改成只设自己的引脚（如 `GPIO_Pin_HIGH` = P1.4~P1.7），示例通道也错开（ADC_CH4~CH7，避开 PWM 占的 CH0~CH3）。

## 5. 定时器资源占用约定（人工确认项）

- **Timer0**：apl_soft_timer 的 1ms 系统 tick，不可挪用（两处都初始化 Timer0 会互相覆盖配置）。
- **Timer1**：`UART1_BRT = BRT_Timer1` 波特率发生器，不可挪用。
- 这两条无法 `#error` 强检（`BRT_Timer1` 常量在预处理 board_config.h 时取不到值），只能注释提醒、改动前人工确认。模板里已写死注释："已被占用，不要打开"。

## 6. git 提交信息格式

```
<工程名>：<更新类别>：<更新描述>
```

- 中文；更新类别：文档 / 代码 / 修复 / 其他。
- 示例：`common：代码：新增软件定时器LITE模式及相关驱动适配，可减少ROM`

## 7. 经验沉淀位置（SDK 内部）

| 文件 | 内容 |
|---|---|
| `project/stc8h_project/CLAUDE.md` | 核心技术坑复盘（三层配置/OVERLAY/变参/TM1650/GPIO 安全网），改 SDK 前必读 |
| `project/stc8h_project/工程通用提示词.md` | 模块勾选清单 + 本工作流原文 |
| `STC8H1Kxx_template/MDK/check_overlay_safety.py` | overlay 自动体检脚本（每个工程 MDK 目录一份） |
| `yjt/STC8H_8G/stc8h-rom-budget-and-keil-optimize.md` | ROM 预算怎么看、Keil 编译/链接选项怎么选（含实测数据与验证四件套，2026-09-28） |

本知识库同目录其余文件是上述 CLAUDE.md 各专题的整理版。


## 8. 补记（2026-09-28 实测）

1. **"没有新增警告"必须用全量重编判定**：`UV4 -b`（增量）只重编改动过的文件，**未重编的文件不产生警告**，日志里会出现 "0 Warning(s)" 的假象；同一次改动换 `UV4 -r` 全量重编，7 条历史警告又都出现。**验证三件套里"确认 0 Error / 警告无新增"要用 `-r`。**
2. **动手前先确认"改什么对象"**：同一句"帮我优化一下打印""这个逻辑写简单点"，可能指改代码、也可能指改文档。**先问一句"是改代码还是改文档"，比事后回退便宜得多**（本次两边各返工过一次）。
3. **共享 SDK 里的公共组件（printf、定时器框架）不要优先动**：省空间的正确顺序是"配置 → 源码 → 公共库"；公共组件牵动其它工程，且往往是使用方明确不希望被改的部分。详见 `stc8h-rom-budget-and-keil-optimize.md`。
