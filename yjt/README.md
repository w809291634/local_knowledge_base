# yjt/ — 按芯片/项目归档的经验库索引

> 与 `embedded/` 的分工：**这里放"换一颗芯片就不成立"的经验**，跨项目可复用的方法论与工具进 `embedded/`。
> 判据和落库规矩见仓库根 `AGENTS.md` 与本文件末尾第 5 节。最后更新：2026-10-15。

## 1. `PEMS/` — 模板化 Word 文档族方法论（体量最大，单独有入口）

生成/迭代医疗器械注册文档族（软件研究资料 PEMS、产品技术要求、说明书、验证/确认记录）的规则与脚本库。

- **先读 `yjt/PEMS/AGENTS.md`**（工具无关的硬约束与交付前 6 步），文件索引看 `yjt/PEMS/README.md`。
- 关键规则文件：`one-pass-quality-gate.md`（事实基线 + 自动闸门 + 证据/签署状态）、
  `generality-boundaries-and-precedence.md`（事实来源优先级；**经验库不得含项目事实**）、
  `consistency-gate.md`（多文档对账 + 说明书/代码/注意事项三方收口）、
  `reference-document-format-and-diagram-requirements.md`、`diagram-generation-and-figure-insertion.md`、
  `cover-pagination-and-sections.md`、`docx-fields-and-toc-repair.md`、`font-and-style-normalization.md`、
  `template-inheritance-in-place-replace.md`、`iteration-and-versioning.md`、`multi-ai-tool-adaptation.md`、
  `pitfalls.md`、`dod-checklist.md`、`case-study-anonymized.md`。
- 可复用脚本在 `yjt/PEMS/tools/`：`docx_ops.py`（封面/分节/目录域/插图/校验原语）、`fig_tools.py`（框图绘制，1 单位=1 英寸）、
  `build_docs.py`、`consistency_check.py`、`release_ops.py`。**用 `sys.path.insert` 直接 import，别再写第二份。**

## 2. `STC8H_8G/` — Keil C51 / STC8G-8H 全系列（7 篇）

| 文件 | 一句话 |
|---|---|
| `board-config-three-layer-switches.md` | `board_config.h` 三层开关架构与编译期静态检查 |
| `drv-tm1650-software-i2c.md` | TM1650 数码管为何必须软件 I2C，影子寄存器与逐位验证做法 |
| `keil-c51-language-pitfalls.md` | C51 语言层坑：变参 3 字节通用指针 / `data` 关键字 / 指针存储区限定 / CONST 段 / tick 撕裂 |
| `keil-c51-overlay-function-pointer.md` | ★ OVERLAY 优化看不见函数指针调用 ⇒ 回调局部变量覆盖调用方（严重） |
| `keil-c51-pdata-overlay.md` | COMPACT 模型下 `L18 pdata 跨页` 与 `L15 Overlay 重入` 是两类独立问题（2026-10-15 自 `embedded/` 移入） |
| `stc8h-rom-budget-and-keil-optimize.md` | 8 KB Flash 容量怎么看、Keil 编译/链接选项怎么选（含实测） |
| `workflow-verification-discipline.md` | 工作流纪律：验证三件套 / 编码 / 工程文件 / 并发 / 提交规范 |

三篇 C51 编译链接类文章的分工：语言层 / 链接器 Overlay 机制 / 内存模型警告。**今后 C51 相关经验统一进这个目录。**

## 3. `ch571/` — 沁恒 CH573/CH57x BLE（2 篇）

| 文件 | 一句话 |
|---|---|
| `ble-device-id-rollcode-nv.md` | BLE 设备 ID 的滚码 NV 格式、控制台/BLE 写法与校验（SimpleProfile 0xFFF0/0xFFF6） |
| `port-rollcode-device-id-to-new-project.md` | 把"滚码设备 ID"移植进新 CH571 工程的实战（MounRiver 2.5.0 + letter-shell） |

## 4. `MultiParam/` — 参数标定与查表（1 篇）

| 文件 | 一句话 |
|---|---|
| `glu-range-lookup-off-by-one-lo.md` | ★ 分段线性查表循环少算一轮 ⇒ 插值全 0 ⇒ 除零 ⇒ 高浓度全部误报 LO（严重） |

## 5. `ac695n_soundbox/` — 杰理 AC695N 项目自写代码（1 篇）

| 文件 | 一句话 |
|---|---|
| `user_apps-custom-drivers.md` | RF315 遥控解码与学习状态机、DMX512 一发一收（Break 手法拉低 + 开串口充当 MAB）、7 脚断码屏主/子界面与倒计时刷新套路、**PB05/PB01 引脚冲突表**、`strcmp` 判 UART 事件的疑似 bug、14 条提交的开发节奏 |

杰理 SDK 本身的通用机制（框架、驱动、配置、OTA、协议）**不在这里**，在
`embedded/jieli_soundbox_sdk/`；这一篇只收"只在本工程成立"的实现与踩坑。

## 6. 落库规矩（与 `embedded/README.md` 第 4 节配套）

- 换一颗芯片这条还成立吗？**不成立 → 放这里**（按 `<芯片或项目名>/` 建目录）；成立 → 放 `embedded/<主题>/`。
- 一个主题一个文件夹，文件夹内按"文件名即结论关键词"命名，严重坑在标题里加 ★。
- 每条经验最少写清：症状 / 根因 / 判据或修法 / 来源工程与日期。头部沿用现有 `> 适用：… > 来源：…` 两行格式。
- 引用本库其他文件一律写仓库根相对路径（`yjt/STC8H_8G/xxx.md`）；改目录时同步检查文字里的路径标签和 Markdown 链接的 `../` 深度。
