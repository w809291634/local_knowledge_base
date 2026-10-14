# AGENTS.md — 模板化文档生成规则（本目录适用）

> **工具无关**的规则入口：Trae / Claude Code / Cursor / Codex 等均可读取。
> Claude Code 可在 `CLAUDE.md` 写 `@AGENTS.md`；Cursor 在 `.cursor/rules/*.mdc` 引用本文件。
> 本目录方法**不针对某一项目**，适用于任何版式固定、内容按项目替换的文档族。

## 适用场景

按公司既定版式批量生成 / 迭代 Word 文档族，例如：医疗器械软件研究资料（PEMS：软件确认计划、
软件体系构架、软件需求说明书、软件详细设计说明、软件确认报告、软件描述文档、软件验证计划、
软件验证报告）、产品技术要求、说明书、验证/确认记录、设计文档等。

## 硬约束（违反即返工）

1. **数据唯一**：型号/部件/指标/编号/厂商只写在 `config.json`；禁止在脚本或文档里另写一套。
2. **格式靠继承**：以参考文档 `.docx` 为模板「就地替换」，**禁止从零拼 Word**
   （会丢封面大标题、浮动封面表、目录域、页眉页脚、分节）。
3. **封面独立成页**；封面后不得出现空白页。
4. **输出到新版本目录**（`*_V{n}/`），永不覆盖源文档与历史版本。
5. **相同代码只写一份**：公共处理封装在 `tools/docx_ops.py`，项目只提供配置。

## 每次交付前必做（4 步）

```
1) python tools/build_docs.py --config config.json         # 重新生成
2) python tools/consistency_check.py --config config.json   # 主键/关键字对账
3) soffice --headless --convert-to pdf --outdir out "某份.docx"   # 一次只转一份
   → 抽 PDF 首页文本：封面独立页 + 无空白页 + 页眉编号正确
4) 人工核对：图（图文一致）、签署栏、交叉引用文件名、他项目残留
```

## 详细规范

| 文件 | 内容 |
|---|---|
| `template-doc-methodology.md` | 总纲：十条通用原则 |
| `template-inheritance-in-place-replace.md` | 核心方法：就地替换 |
| `cover-pagination-and-sections.md` | 封面/分页/分节三大风险点 |
| `consistency-gate.md` | 多文档一致性对账 |
| `iteration-and-versioning.md` | 迭代与版本管理 |
| `multi-ai-tool-adaptation.md` | 一套内容适配多 AI 工具 |
| `pitfalls.md` | 环境/格式坑 |
| `dod-checklist.md` | 交付质量清单（DoD） |
| `case-study-medical-laser-03GSR2607002.md` | 落地实例（含项目数据） |
| `tools/docx_ops.py` | 通用原语库（统一封装，跨项目复用） |
| `tools/build_docs.py` / `config.example.json` | 配置驱动的生成入口 |
| `tools/consistency_check.py` | 配置驱动的一致性检查 |

## 环境

- Python 3 + `python-docx`；`.doc` 转换需 `pywin32`（Word 或 WPS）。
- 渲染校验用 LibreOffice（`soffice --headless`）。