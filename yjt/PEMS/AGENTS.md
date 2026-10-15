# AGENTS.md — 模板化文档生成规则（本目录适用）

> **工具无关**的规则入口：Trae / Claude Code / Cursor / Codex 等均可读取。
> Claude Code 可在 `CLAUDE.md` 写 `@AGENTS.md`；Cursor 在 `.cursor/rules/*.mdc` 引用本文件。
> 本目录方法**不针对某一项目**，适用于任何版式固定、内容按项目替换的文档族。

## 适用场景

按公司既定版式批量生成 / 迭代 Word 文档族，例如：医疗器械软件研究资料（PEMS：软件确认计划、
软件体系构架、软件需求说明书、软件详细设计说明、软件确认报告、软件描述文档、软件验证计划、
软件验证报告）、产品技术要求、说明书、验证/确认记录、设计文档等。

## 硬约束（违反即返工）

1. **数据唯一**：项目事实仅写入当前项目指定的主事实文件（`facts.yaml`、`facts.json` 或受控 `config.json` 三选一）；禁止在脚本、经验库或文档中另写一套。
2. **格式靠继承**：以参考文档 `.docx` 为模板「就地替换」，**禁止从零拼 Word**
   （会丢封面大标题、浮动封面表、目录域、页眉页脚、分节）。
3. **封面独立成页**；封面后不得出现空白页。
4. **输出到新版本目录**（`*_V{n}/`），永不覆盖源文档与历史版本。
5. **相同代码只写一份**：公共处理封装在 `tools/docx_ops.py`，项目只提供配置。
6. **三方收口**：每轮输出文档后，必须核对 **说明书 / 代码 / 注意事项** 三者一致性，
   冲突未清零不得发布（规则见 `consistency-gate.md` 第 5 节）。

## 每次交付前必做（6 步）

```
1) 使用当前项目主事实文件生成；调用本库脚本时执行 `python tools/build_docs.py --config <project-config.json>`，确认输出目录中的 `manifest.json` 已记录配置、事实文件、模板和产物的哈希。
2) 运行一致性检查；调用本库脚本时执行 `python tools/consistency_check.py --config <project-config.json>`。跨文档对比必须按 `scope` 分组，禁止把本来不应包含同一型号或术语的文档强行判为不一致。
3) soffice --headless --convert-to pdf --outdir out "某份.docx"   # 一次只转一份
   → 抽 PDF 首页文本：封面独立页 + 无空白页 + 页眉编号正确
4) 人工核对：图（图文一致）、签署栏、交叉引用文件名、他项目残留
5) **用 Word 只读打开每一份产物并记录页数**（LibreOffice 与 python-docx 都不报的损坏，Word 会报；
   典型诱因见 `pitfalls.md` 第 6/7 节）
6) 三方收口：说明书 / 代码 / 注意事项 逐参数核对 → 冲突清零（consistency-gate.md 第 5 节）
```

## 详细规范

| 文件 | 内容 |
|---|---|
| `template-doc-methodology.md` | 总纲：十条通用原则 |
| `template-inheritance-in-place-replace.md` | 核心方法：就地替换 |
| `cover-pagination-and-sections.md` | 封面/分页/分节三大风险点 |
| `consistency-gate.md` | 多文档一致性对账 + 说明书/代码/注意事项**三方收口** |
| `iteration-and-versioning.md` | 迭代与版本管理 |
| `multi-ai-tool-adaptation.md` | 一套内容适配多 AI 工具 |
| `pitfalls.md` | 环境/格式坑 |
| `dod-checklist.md` | 交付质量清单（DoD） |
| `font-and-style-normalization.md` | 字体字号统一（正文/标题/表格/图题分区，样式默认值与配图字体一起改） |
| `diagram-generation-and-figure-insertion.md` | 配图生成与插图替换（绘图三原则、插图五坑、自检与校验） |
| `case-study-anonymized.md` | 落地实例（含项目数据） |
| `tools/docx_ops.py` | 通用原语库（统一封装，跨项目复用） |
| `tools/fig_tools.py` | 配图绘制原语（框图/流程图；边界精确、箭头端点自动算） |
| `tools/build_docs.py` / `config.example.json` | 配置驱动的生成入口 |
| `tools/consistency_check.py` | 配置驱动的一致性检查 |
| `tools/release_ops.py` | 全 XML 文本扫描、页眉页脚/文本框受控替换、哈希与发布清单原语 |

## 环境

- Python 3 + `python-docx`；`.doc` 转换需 `pywin32`（Word 或 WPS）。
- 配图需 `matplotlib`（中文字体用 SimHei/Microsoft YaHei；**文档正文统一宋体时，图内也要改用 SimSun 重绘**，否则一眼看出不统一，见 `font-and-style-normalization.md`）。
- 渲染校验用 LibreOffice（`soffice --headless`）。

## 质量闸门补充（2026-10-14）

- 编写前冻结项目事实基线；用户新增确认先回写 YAML 或受控变更记录，再生成文档。
- 未命中的替换槽位、事实冲突、旧项目残留、缺少必要图示或未提供实测证据时，必须阻断发布。
- `build_docs.py` 默认拒绝覆盖已有输出；仅在确认同一版本目录需要重建时才显式使用 `--force`。每次交付保留生成的 `manifest.json` 与一致性检查报告。
- 草稿、待执行、待审核和受控发布分开管理；无证据不填通过结论、签署人或测试日期。
- 适用文档必须有当前项目的架构图、关键流程/状态图、硬件关系/拓扑图或可用性任务流程图；图示逐页渲染核对。
- 配图先过机器自检（文本宽度预警 + 内嵌图片哈希/宽高比校验），再人工逐张看 PNG（脚本读不到图内文字）。
- **字体基线要"分区 + 二遍"**：正文/表格/图题各有字号档，标题与封面只统一字体不改字号；
  字体统一必须在**目录刷新之后**再跑一遍（Word 保存会抹掉显式 `rFonts` 与等价样式字号）。
  覆盖正文、表格单元格、空 run、样式默认值四处，配图回绘图脚本换字体重绘。
  见 `font-and-style-normalization.md` §6/§7 与 `tools/docx_ops.py:unify_document_fonts`。
- 承接旧稿做块对齐时：空段先剔除、封面区与目录域禁止插入、刷新后比对目录条目数，
  超阈值还原备份（`pitfalls.md` §11/§12）。
- **承接与槽位是两条写入轨道，必须互相查重**：写前用"本轮正文池"拦承接／插入，写后全量扫
  `dup_kind` 四形态（exact／near／same-lead／contained），优先级 本轮正文 > 模板原样 > 承接；
  两段都是模板原样时只报不删，去重前确认独有事实已并入保留段（`pitfalls.md` §16）。
- **段落版式按"生效版式"对齐**：本轮新写段以就近模板段为锚点，先双向对齐 `pStyle` 再抄其直接
  pPr；只读段落 pPr、用多数派或互相参照都会误伤模板（`pitfalls.md` §18、
  `font-and-style-normalization.md` §8）。闸门两条：无重复正文段、本轮正文段版式与锚点一致。
- 同锚点多段插入必须按顺序 `append`；闸门校验承接段先后与来源版一致（`pitfalls.md` §17）。
- 渲染复用只在"PDF 不比 docx 旧"时成立；页码补丁必须在渲染之后跑（`pitfalls.md` §19）。
- 详细规则见 `one-pass-quality-gate.md`、`reference-format-profile-template.md`、`reference-document-format-and-diagram-requirements.md` 和 `diagram-generation-and-figure-insertion.md`。

## 通用性边界

- 通用经验库不得写入具体项目名称、项目号、型号、芯片、版本、阈值、人员、测试结果或结论。
- 案例、历史文档和格式档案仅用于方法与版式参考，不能作为新项目事实来源。
- 事实来源、证据边界、必备图示和发布条件遵循 generality-boundaries-and-precedence.md。
