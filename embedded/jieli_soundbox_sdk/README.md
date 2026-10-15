# jieli_soundbox_sdk/ — 杰理（Jieli）Soundbox SDK 经验库

> 来源：AC695N soundbox SDK release 3.1.0（内核 **BR23**），文档 `doc/` 11 份 PDF + 全部代码。
> 采集日期：2026-10-15。**目录里的文件路径一律写成 SDK 内相对路径**（如 `apps/soundbox/app_main.c`、
> `Makefile:217`），工程根位置属"只与用户名绑定"的 A 类路径，换机按当前用户实测即可。

## 目录结构与型号区分原则

```
jieli_soundbox_sdk/
├── README.md          ← 本文件
├── common/            ← 跨型号通用：杰理 SDK 的打法、框架接口、坑
└── ac695n_br23/       ← 型号绑定：AC695N/AC696N + BR23 内核的资源表、板级差异、版本史
```

- **判据**：一条经验换到 AC696N / AC70xx / 别的内核上还成立吗？成立进 `common/`，只在 BR23/AC695x 成立进 `ac695n_br23/`。
- **新增型号**：建 `ac696n_br23/`、`ac700n_br2x/` 这样的 `<型号系列>_<内核>/` 目录，不要往 `common/` 里塞型号条件。
- 内核名（BR23）与型号名（AC695N）**不是一回事**：编译宏是 `CONFIG_CPU_BR23`，烧录参数是 `-dev br23`，
  而 AC695N/AC696N 是同一份 SDK 覆盖的两个芯片系列（手册 Ch7 明确覆盖两系列）。
- **项目绑定的自写驱动**（本工程的 SEG/RF/DMX512 实现与引脚冲突）不在这里，见 `yjt/README.md` → `yjt/ac695n_soundbox/`。

## common/ 条目索引

| 文件 | 讲什么 | 什么时候查 |
|---|---|---|
| `sdk-layout-build-and-flash.md` | 分层与开源/闭源边界、工具链、Windows/Linux 编译、`download.bat` 产物链、烧录命令、新增 `.c` 要登记哪几处 | 第一次搭环境、改了不生效、要加文件 |
| `config-three-layers-and-macro-mutex.md` | `CONFIG_BOARD_*` / `TCFG_*` / `app_config.h` 三层关系与联动覆盖，官方互斥组合（`#error`）清单 | 换板级、开新功能、编译报 `#error` |
| `app-task-state-machine.md` | 上电到进模式的完整启动链、任务状态机骨架、新增一个模式的 5 步、系统事件分派规则 | 加新模式、查"为什么没进某模式" |
| `key-and-event-flow.md` | 按键从中断/扫描到被消费的完整链路、事件表结构、新增一种按键源要改的 5 处 | 加按键、改按键行为、接遥控 |
| `config-storage-vm-sdfile-syscfg.md` | VM / syscfg / SDFILE / 量产配置 bin 的分工、读写 API、对齐与禁中断约束、VM 整理卡顿 | 存参数、掉电保存、读配置 |
| `peripheral-drivers-cookbook.md` | UART/SPI/IIC/PWM/ADC/定时器/充电/端口唤醒的入口函数、自带 `*_test.c` 在哪、硬件脚位表、被独占的资源 | 驱动任意外设 |
| `led7-display-and-ui-framework.md` | 断码屏/数码管：led7 软件扫描原理、显示 API 清单、字符与段-脚表在哪、UI 框架注册与刷新机制、`ui_user` 返回值语义、与 lcd_seg3x9 的差异 | 接数码管/断码 LCD、做界面刷新 |
| `audio-pipeline-and-effects.md` | 解码/编码/音效三条链的数据流、格式表、EQ/DRC/混响/AEC 开关与联动、在线调音全流程 | 调音、加音效、查卡顿 |
| `logging-exception-debug.md` | 日志 6 级与运行时常量开关、release 零开销机制、断言两种行为、异常现场字段读法与反汇编定位 | 看 log、定位死机/复位 |
| `power-consumption-debug.md` | 进不了低功耗怎么查、三种定时器对功耗的本质差别、唤醒源、实测电流表、漏电排查顺序 | 待机电流大、掉电快 |
| `ota-dual-backup-update.md` | 单/双备份差别与回滚原理、双备份要改的 ini 与 SDK 常量、`json.txt`/VID/PID/MD5/ufw 命名、客户自定义协议的 3 个接口 | 做 OTA、做升级、改分区 |
| `protocol-integration-rcsp-app-tuya.md` | RCSP/杰理 OTA 协议帧与 opcode、第三方 AI 协议中间层（GMA/MMA/DMA/TME/AMA）、涂鸦 BLE、天猫精灵 Mesh，以及它们的互斥关系 | 接 APP、接语音平台、接涂鸦 |
| `online-config-tool-mass-production.md` | 音箱配置工具能改什么、`.jlxproj` 入口本质、`cfg_tool.bin`/`tone.cfg` 怎么生成、开发端与终端权限屏蔽、量产烧录路径 | 改蓝牙名/音量/提示音、量产 |

## ac695n_br23/ 条目索引

| 文件 | 讲什么 |
|---|---|
| `chip-resources-and-board-variants.md` | BR23 能力表（解码/编码/按键/DAC/TWS/时钟/中断优先级）、19 个板级对应的型号与方案、已知型号差异点 |
| `version-history-3.1.0.md` | 1.0.0→3.1.0 演进与 A/B/C 问题分级、各版本工具链与配套工具版本、累积编号的读法 |

## 已知盲区（别当已知）

- 手册 Chapter 10「客户常见问题反馈解答」Q1/Q2 **正文是空的**（p63），没有可沉淀内容。
- 功耗文档只给 LDO/DCDC 两列实测，**未给型号差异表**；两份音效 PDF 的"性能要求"章节**正文为空**。
- LDAC/aptX 在 `audio_base.h` 有枚举，但 BR23 侧实现与开关**未见说明**。
- `SDK/README.md` 只有一句"用户程序在./apps/user_apps路径下"，与实际不符（真实主程序在 `apps/soundbox/`）。
- 双备份 PDF 正文只有两个小标题，其余全是截图；原理部分靠代码补证，已在条目里标注来源。
