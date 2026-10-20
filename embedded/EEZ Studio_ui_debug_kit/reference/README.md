# EEZ Studio 参考指南 — 知识库索引

本目录存放从 **EEZ Studio Reference Guide**（784 页 PDF）中结构化提炼的「软件使用经验」。
提炼目的：为**嵌入式 LVGL 9.4 设备 UI 工程生成**提供可检索、可落地的参考。

> **零丢失备份**：完整原始文本（未加工）在同目录上级的
> `reference_guide_raw.txt`（约 1.3 MB / 784 页全量文本，无图片）。
> **官方 PDF 本机存档**：`<kit>/EEZ-Studio-reference-guide.pdf`（784 页全图版，
> 2026-10-19 用户存档；查原文插图/表格用 PDF，查文字用 raw.txt 或 01~07 提炼版）。
> `01`~`07` 是在原始文本之上的**结构化提炼**，便于快速查阅；`08`~`11` 是**工程实践类**
> （手册不讲、落地必用），见下面第二张表。

## 手册结构 → 文档映射

| 手册章节 | 内容 | 提炼文档 | 行数 |
|---|---|---|---|
| C1–C5, P1–P7, P13 | 法律/概览/安装/特性/菜单、工程编辑器、EEZ Flow、工程编辑、设置 | `01_project_overview.md` | ~710 |
| P8–P12 | 变量、样式与配色、位图、字体（LVGL 重点）、文本/XLIFF | `02_styles_fonts_vars.md` | ~596 |
| A1–A46 | Actions：动画/文件/JSON/HTTP/仪器/循环/表达式…（含 **A43 LVGL**） | `03_actions_a1_a46.md` | ~1237 |
| A47–A92 | Actions：MQTT/TCP/UDP/串口/Python/键盘/页面导航…（**A53/A55/A72/A73/A75/A76/A78/A91** 重点） | `04_actions_a47_a92.md` | ~1209 |
| W1–W43 | Widgets：按钮/容器/下拉/图片/标签/列表…（**W10/W16/W20/W24/W30/W35/W42** LVGL 重点） | `05_widgets_part1.md` | ~926 |
| W44–W87 | Widgets：滑块/开关/Tabview/文本区/TileView…（**W56/W61/W67/W71/W74/W78/W80/W83/W84** LVGL 重点） | `06_widgets_part2.md` | ~817 |
| **（非手册）** | **`.eez-project` 工程 JSON 序列化语法速查**——手册不讲文件格式，本篇为实测字段级对照（控件/样式/事件/flow 组件/连线/表达式陷阱），AI 或脚本改工程 JSON 前必读 | `07_project_json_schema.md` | ~330 |

## 工程实践类（非手册提炼，落地必用）

| 主题 | 内容 | 文档 |
|---|---|---|
| 帧率 | LVGL 在 ESP32-P4 上的帧率天花板、有效/无效优化清单（本工程实测，含 PPA 必崩项） | `08_lvgl_esp32p4_frame_rate.md` |
| 构建/烧写 | 本工程的编译·烧写·调试作业卡：把 PLAYBOOK 的 `{占位符}` 填成这台机器上的真实值 | `09_build_flash_debug_lvgl_demo_ai.md` |
| ★ **硬件 ⇄ UI 分离** | **跨项目模板**。§0 先给**文件目录结构**（四角色目录树 + 每个目录怎么自证身份 + 依赖方向图 + 一条信号跨目录的流向 + 陌生工程 5 分钟认路），再讲四条不变式、四层归属、A/B/C 三通道判据、变量桥三条硬规矩、★平台分界三种机制的选择判据、线程模型配方、仿真镜像纪律、加信号清单、9 条反模式、机器检查清单 | `10_hw_ui_separation.md` |
| ★ **最小 EEZ 工程脚手架** | 从零搭可编译的最小 EEZ 模板：四块目录职责、三条硬规矩（native 不 REQUIRES ui / GLOB 需 reconfigure / 不写死生成对象句柄）、三大链接机制（CMP0079、lvgl__lvgl 依赖 lv_mem_psram、--undefined=lv_thread_init）、A/B 宏测量法与实测账单、与 P-0154 的三层拆分口径 | `11_minimal_eez_project_scaffold.md` |

## 本项目（eez-test，LVGL 9.4 / 800×480 横屏 / BGR）最常用入口

- **Widgets 与 json2eez 流水线相关**：`05_widgets_part1.md`（容器 W20 布局走 Style、图片 W30 缩放、标签 W35）、`06_widgets_part2.md`（滑块 W67、开关 W74、Tabview W78、文本区 W80）。
- **字体生成（gen_fonts.py 对应）**：`02_styles_fonts_vars.md` 的 P11.2 LVGL 字体（bpp / Ranges / Symbols）。
- **样式属性（样式层级 / 覆盖）**：`02_styles_fonts_vars.md` 的 P9；运行时覆盖见 `04_actions_a47_a92.md` 的 **A55 OverrideStyle**。
- **页面导航 / 事件 / 变量**：`04_actions_a47_a92.md` 的 **A78 ShowPage、A53 OnEvent、A73 SetVariable、A72 SetPageDirection**。
- **从 Flow 操作 LVGL 对象**：`03_actions_a1_a46.md` 的 **A43 LVGL**（对象几何/样式/标志、控件 API、动画）。

## 阅读约定

- 六个文档均保持**英文标识符原样**（属性名、枚举值、Action 名），描述文字为中文。
- 每个 Widget / Action 小节通常含：用途、属性表（名/类型/默认/含义）、输入/输出、示例、LVGL 关联要点。
- 原文中 LVGL 样式未逐项列出全部 72 个属性名（手册指向官方 LVGL style 文档），相关文档已明确标注，未臆造。
- **版本边界**：这份手册含 LVGL 8 时代的描述；本库当前 LVGL 项目以 **LVGL 9.4** 的头文件、
  生成 `screens.c` 和运行时实测为准。手册名词与 v9 正式 API 不一致时，文中必须标出旧名，
  不得把兼容别名当新代码配方。
- **WIP 边界**：手册里 “work in progress，后续在 custom code 实现” 只说明 Studio 当前
  的能力缺口，**不等于授权把 UI 写进 C**。EEZ-first 工程须先查事件/动作/调度/运行时四面；
  仍无解时说明原因并取得用户同意，才允许 C 侧例外。
