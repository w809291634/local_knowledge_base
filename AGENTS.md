# AGENTS.md — 本地经验库入口（工具无关，先读这个再动手）

> 适用于 Trae / Claude Code / Cursor / Qoder / Codex 等任何会读规则文件的 AI 工具，也适用于人。
> 目的只有一个：**让人和 AI 都能一步找到"以前踩过的坑"，并且不把新旧位置搞混。**

## 1. 本仓库有两套内容，别混

| | 位置 | 索引 |
|---|---|---|
| 上游 TIL 英文小笔记 | 仓库根几十个技术栈目录（`python/`、`linux/`、`windows/`、`vscode/`…） | 根 `README.md` 的分类索引（同时收录下面三个自建章节） |
| 自建中文经验库 | `embedded/`、`yjt/` | `embedded/README.md` + `yjt/README.md`（两棵树的索引）；`yjt/PEMS/AGENTS.md`（文档族硬约束）← 真正的入口 |

根 `README.md` 里有三个自建章节：**`### Embedded`、`### UI Debug Kit`、`### YJT`**（Categories 列表里有对应锚点）。
**新增或移动自建内容时，这三节要同步改**，否则索引就变成断链——2026-10-15 那次 `ui_debug_kit/` 前缀失效就是这么来的。

## 2. 查找顺序（按任务进对应入口）

| 任务 | 先读 |
|---|---|
| 嵌入式通用排查方法、调试器、IDE、STM32/RT-Thread/C51 坑 | `embedded/README.md` |
| ESP32 / ESP-IDF 构建、LVGL 帧率与显示调试 | `embedded/esp32/`（入口：`embedded/README.md` 第 1 节） |
| UI 效果对照、生成式 UI 的回归门禁（EEZ Studio、LVGL、各类前端） | `embedded/EEZ Studio_ui_debug_kit/README.md` → `PLAYBOOK.md` |
| 杰理（Jieli）蓝牙音频 SoC / soundbox SDK / AC695N | `embedded/jieli_soundbox_sdk/README.md`（先分"跨型号 `common/`"还是"`<型号>_<内核>/`"） |
| 单片机外设（串口/I2C/SPI/CAN/定时器/ADC/DMA/时钟）、各家芯片差异、调试取证 | `embedded/mcu-peripherals/README.md` + `embedded/mcu-chip-families/README.md`；**要代码骨架看同目录 `recipes-*.md`；引用个人 study_doc 前先查 `embedded/mcu-peripherals/ERRATA-*.md`；要判断"这条库里有没有"先查 `embedded/mcu-peripherals/COVERAGE-覆盖度与缺口.md`（源 docx 的图片层尚未提取）** |
| 模板化 Word 文档族（医疗器械注册 PEMS、技术要求、说明书、验证/确认记录） | `yjt/PEMS/AGENTS.md`（硬约束）+ `yjt/PEMS/README.md`（文件索引） |
| 具体芯片/项目经验（Keil C51 / STC8H、CH571 BLE、参数标定查表） | `yjt/README.md`（按目录分区索引） |

## 3. 新笔记落哪

- 只在一款芯片 / 一个工程上成立 → `yjt/<芯片或项目名>/`。
- 跨项目可复用的方法论与工具 → `embedded/<主题>/`，**一个主题一个文件夹**，不要在 `embedded/` 根平铺。
- 判据模糊就问一句："换一颗芯片这条还成立吗？"成立进 `embedded/`，不成立进 `yjt/`。
- 详细内容规则（每条最少说什么）见 `yjt/PEMS/reference-document-format-and-diagram-requirements.md` 与 `embedded/README.md`。

## 4. 三条硬规矩

1. **机器相关绝对路径按 A / B 两类处置**（对照表与细则见 `embedded/README.md` 第 6 节）。
   **A 类只与用户名绑定**（`.workbuddy\...`、`AppData\Local\...`、`D:\esp32_8266_files\` 下的 IDF 根与工程根等）：
   把用户名换成当前用户、实测存在即可直接用，不必每次问。
   **B 类每台电脑都不一样**（PC 仿真器根、LVGL 内核源码目录、临时脚本目录、官方参照工程位置）：
   **使用相关经验前必须让用户指定这台机器上的真值**；
   库里出现的字符串只是来源机样本，一律按 `{占位符}` 看待，禁止扫盘猜、禁止照抄执行；
   问到的真值写进**工程侧配置**，不回填经验正文（正文只留占位符与做法）。
   例外：IDF 工具包 / `IDF_TOOLS_PATH` / `IDF_PYTHON_ENV_PATH` 由本机 IDF 安装与用户环境自行解决，**已配好，不作为待办提醒**。
2. **引用路径统一写仓库根相对形式**（`embedded/esp32/xxx.md`）。改目录结构时，
   同时处理两类断链：文字里的路径标签、Markdown 链接里的 `../` 深度。
3. **记录区只增不改。** `intake/`、`prompts/` 是证据与流水：编号只增，结论被推翻就**追加**更正段，原文保留；
   要指路就在追加段里写新位置。手册类文件（`skills.md`、`reference/`）里的失效路径才就地改。

## 5. 提交信息

中文，格式 `<工程名>：<更新类别>：<更新描述>`，更新类别取 文档 / 代码 / 修复 / 其他
（见 `.trae/rules/git-commit-message.md`）。移动/重命名请在描述里写明"移动"，方便日后按路径追历史。

## 6. 结构变更记录与仍欠的事

已收口（2026-10-15）：`esp32/` 与 `EEZ Studio_ui_debug_kit/` 并入 `embedded/`；原平铺在 `embedded/` 根的
6 篇笔记已按主题归入 `debug-methodology/`、`debugger/`、`ide/`、`rt-thread/`、`stm32/`；
`keil-c51-pdata-overlay.md` 归一到 `yjt/STC8H_8G/`（C51 三篇分工见 `yjt/README.md` 第 2 节）；
`embedded/README.md` 与 `yjt/README.md` 两份索引已建。移动时受影响的 2 处引用（`debug-methodology.md`
的 `../../python/...` 链接深度、`stm32-hal-pitfalls.md` 对 rt-thread 篇的指代）已同步修正。

仍欠（需要人来定，AI 不要猜）：
- 那批 ESP32/EEZ 文档里的机器路径只做了**标注**，没换成本机真值；若这些工程今后还要在当前机器上跑，
  需实测 IDF / Python / LVGL 源码 / PC 仿真模板的真实路径后回填并标日期。
- AC695N（杰理 soundbox SDK）的学习经验尚未入库。按第 3 节：跨项目方法论进 `embedded/<主题>/`，
  只跟这颗芯片/这套 SDK 绑定的进 `yjt/ac695n_soundbox/`。
