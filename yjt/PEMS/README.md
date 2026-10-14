# 模板化文档生成（通用方法论）

本目录沉淀「按固定版式批量生成并迭代 Word 文档族」的方法、脚本与踩坑。
**方法通用，不绑定某一项目**；项目专有信息只放在 `case-study-*.md` 与 `config.json` 里。

## 文件

| 文件 | 内容 |
|---|---|
| `AGENTS.md` | **规则入口**（工具无关，AI 工具先读这个） |
| `template-doc-methodology.md` | 总纲：十条通用原则 + 适用边界 |
| `template-inheritance-in-place-replace.md` | 核心方法：以参考文档「就地替换」 |
| `cover-pagination-and-sections.md` | 封面/分页/分节三大高风险点 |
| `consistency-gate.md` | 多文档同数据一致性对账 + 说明书/代码/注意事项三方收口 |
| `iteration-and-versioning.md` | 迭代机制与版本管理 |
| `multi-ai-tool-adaptation.md` | 一套内容适配多种 AI 工具 |
| `pitfalls.md` | 环境与格式坑 |
| `dod-checklist.md` | 交付质量清单（Definition of Done） |
| `diagram-generation-and-figure-insertion.md` | 配图生成与 Word 插图替换（绘图三原则、三个插图坑、自检与校验） |
| `case-study-medical-laser-03GSR2607002.md` | 落地实例（含项目数据，可替换） |
| `tools/docx_ops.py` | 通用原语库（统一封装共用函数） |
| `tools/fig_tools.py` | 配图绘制原语（框图/流程图/拓扑图；1 单位=1 英寸、边界精确、箭头端点自动算） |
| `tools/build_docs.py` | 配置驱动的生成入口 |
| `tools/config.example.json` | 配置模板 |
| `tools/consistency_check.py` | 配置驱动的一致性检查 |

## 一句话总纲

**先定基线 → 以模板就地替换生成 → 脚本对账 + 渲染对拍 → 人工核对图与签署 → 版本快照归档。**

## 换项目三步

1. 复制本目录（方法论与 `tools/` 无需改动）。
2. 新建 `config.json`：填项目号、产品/部件名、清单数据、指标、版本、编号、术语替换表。
3. 指定参考模板（只读），依次跑 `build_docs.py` → `consistency_check.py` → 渲染对拍 → 人工核图与签署。

## 质量与格式补充

- `one-pass-quality-gate.md`：事实基线、自动质量闸门、证据/签署状态与发布归档。
- `reference-format-profile-current-templates.md`：当前 PEMS 参考模板的格式档案。
- `reference-document-format-and-diagram-requirements.md`：参考文档的格式深度与必备框图要求。
- `diagram-generation-and-figure-insertion.md`：配图怎么画才不重叠/不指错，以及插图替换进 Word 的坑与校验。
