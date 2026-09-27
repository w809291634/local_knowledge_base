# EEZ Studio 参考指南 — 知识库索引

本目录存放从 **EEZ Studio Reference Guide**（784 页 PDF）中结构化提炼的「软件使用经验」。
提炼目的：为**嵌入式 LVGL 9.4 设备 UI 工程生成**提供可检索、可落地的参考。

> **零丢失备份**：完整原始文本（未加工）在同目录上级的
> `reference_guide_raw.txt`（约 1.3 MB / 784 页全量文本，无图片）。
> 本目录的 6 个 `.md` 是在原始文本之上的**结构化提炼**，便于快速查阅。

## 手册结构 → 文档映射

| 手册章节 | 内容 | 提炼文档 | 行数 |
|---|---|---|---|
| C1–C5, P1–P7, P13 | 法律/概览/安装/特性/菜单、工程编辑器、EEZ Flow、工程编辑、设置 | `01_project_overview.md` | ~710 |
| P8–P12 | 变量、样式与配色、位图、字体（LVGL 重点）、文本/XLIFF | `02_styles_fonts_vars.md` | ~596 |
| A1–A46 | Actions：动画/文件/JSON/HTTP/仪器/循环/表达式…（含 **A43 LVGL**） | `03_actions_a1_a46.md` | ~1237 |
| A47–A92 | Actions：MQTT/TCP/UDP/串口/Python/键盘/页面导航…（**A53/A55/A72/A73/A75/A76/A78/A91** 重点） | `04_actions_a47_a92.md` | ~1209 |
| W1–W43 | Widgets：按钮/容器/下拉/图片/标签/列表…（**W10/W16/W20/W24/W30/W35/W42** LVGL 重点） | `05_widgets_part1.md` | ~926 |
| W44–W87 | Widgets：滑块/开关/Tabview/文本区/TileView…（**W56/W61/W67/W71/W74/W78/W80/W83/W84** LVGL 重点） | `06_widgets_part2.md` | ~817 |

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
