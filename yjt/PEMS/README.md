# 模板化文档生成（通用方法论）

本目录沉淀「按固定版式批量生成并迭代 Word 文档族」的方法、脚本与踩坑。
**方法通用，不绑定某一项目**；项目专有信息仅保存在项目目录的受控事实文件与证据索引中。经验库中的案例必须匿名化，仅说明方法。

## 文件

| 文件 | 内容 |
|---|---|
| `AGENTS.md` | **规则入口**（工具无关，AI 工具先读这个） |
| `template-doc-methodology.md` | 总纲：十条通用原则 + 适用边界 |
| `template-inheritance-in-place-replace.md` | 核心方法：以参考文档「就地替换」 |
| `cover-pagination-and-sections.md` | 封面/分页/分节高风险点（含"目录后垫片空段""各节页宽不一致"；§8 空白页与段前冒点的「定位—修复—复验」五步流程） |
| `docx-fields-and-toc-repair.md` | 域（Field）与目录修复：TOC 坏的三形态、诊断、补壳、"更新目录"会拍平域壳的教训 |
| `consistency-gate.md` | 多文档同数据一致性对账 + 说明书/代码/注意事项三方收口 |
| `iteration-and-versioning.md` | 迭代机制与版本管理 |
| `multi-ai-tool-adaptation.md` | 一套内容适配多种 AI 工具 |
| `pitfalls.md` | 环境与格式坑（含"Word 判文件损坏"三坑、文本框节点级替换；§38–§42 分页控制属性误用、双重分页空白页、布尔属性 `w:val`、中文 PDF 空白页判据、标题/图题判据收紧；§45–§50 分页时序与形态、空段三种命运、域平衡与页数核账、闸门误报、无头实例瞬时失败；§51 表格左边框四类根因与列宽污染、§52 封面留白统一、§53 标题编号机制三态混用；§54 只有大标题分页与目录页码同步、§55 标题分档/零缩进/封面大标题被压、§56 空白页另外三种形态；§57 新判据入库后回扫旧脚本、§58 判据降级必须失败退出、§59 补空段时序与显式写零；§60 用户要求全表带边框时规则 D 让位、§61 连续回车顶页造成的空白块、§62 补空格正则要按最长合法前缀；§63 封面居中偏上的可行做法、§64 lxml 真值与配置解析器键模式两类静默失效；§65 自动编号的字形藏在 numbering.xml 的 lvl/rPr、§66 标题统一要量到渲染层（逐字 bbox 三条判据）、§67 插入正文段不要克隆供体（"文字正文·样式标题"两条链路都不管）） |
| `dod-checklist.md` | 交付质量清单（Definition of Done）；F 组为分页与标题树终检 7 条 |
| `font-and-style-normalization.md` | 字体字号统一：正文/标题/表格/图题分区，样式默认值与配图字体一起改；§10 文档族内标题字号统一（以参照文档取基线、逐级别多数派、四条护栏） |
| `diagram-generation-and-figure-insertion.md` | 配图生成与 Word 插图替换（绘图三原则、五个插图坑、自检与校验） |
| `case-study-anonymized.md` | 匿名化落地实例（仅保留方法，不是项目事实来源） |
| `tools/docx_ops.py` | 通用原语库（统一封装共用函数；分页/标题树闸门 `pagination_audit` 与同源修复 `pagination_repair`（共用判据 `chapter_pad_map` / `sect_breaks_page_el`）、渲染判据 `page_ink_coverage` / `grade_pages_by_ink`、样式链生效级别 `effective_outline`、表格版式体检与修复 `audit_table_geometry` / `normalize_table_geometry`、封面留白统一 `set_cover_spacers`、标题字号族内统一 `heading_format_profile_from` / `normalize_heading_format` / 跨档闸门 `check_heading_tiers`、编号机制审计 `heading_numbering_mechanisms`） |
| `tools/para_ops.py` | 段落级原语：重复段判据（四形态）、生效版式比对与锚点对齐、承接顺序 |
| `tools/fig_tools.py` | 配图绘制原语（框图/流程图/拓扑图；1 单位=1 英寸、边界精确、箭头端点自动算） |
| `tools/build_docs.py` | 配置驱动的生成入口 |
| `tools/config.example.json` | 配置模板 |
| `tools/consistency_check.py` | 配置驱动的一致性检查 |
| `tools/release_ops.py` | 全 XML 文本扫描、页眉页脚/文本框受控替换、哈希与发布清单原语 |

## 一句话总纲

**先定基线 → 以模板就地替换生成 → 脚本对账 + 渲染对拍 → 人工核对图与签署 → 版本快照归档。**

## 换项目三步

1. 复制本目录（方法论与 `tools/` 无需改动）。
2. 建立项目主事实文件（YAML、JSON 或受控配置文件三选一）：填项目元数据、型号/配置、指标、版本、编号、术语和证据索引；调用本库脚本时生成适配的配置 JSON。
3. 指定参考模板（只读），依次跑 `build_docs.py`（核对 `manifest.json`）→ `consistency_check.py`（按 `scope` 对账）→ 渲染对拍 → 人工核图与签署。

## 质量与格式补充

- generality-boundaries-and-precedence.md：通用规则边界、证据优先级和案例隔离要求。

- `one-pass-quality-gate.md`：事实基线、自动质量闸门、证据/签署状态与发布归档。
- `reference-format-profile-template.md`：项目模板格式档案的空白文字模板。
- `reference-document-format-and-diagram-requirements.md`：参考文档的格式深度与必备框图要求。
- `diagram-generation-and-figure-insertion.md`：配图怎么画才不重叠/不指错，以及插图替换进 Word 的坑与校验。

## 工具使用边界

- `build_docs.py` 只接受主事实文件和项目配置提供的内容；模板只读，输出目录必须是新版本目录。已有输出默认会被拒绝，只有经过确认的重建才使用 `--force`。
- `manifest.json` 是本轮交付的可追溯快照：保留项目配置、主事实文件、模板和产物的 SHA-256 哈希；不要手工修改它。
- `global_subs` 会在正文、表格、页眉页脚和可见 Word XML 中复核替换；对于浮动文本框等非标准槽位，应把替换项登记在 `xml_subs`，再由残留词检查确认。
- `consistency_check.py` 的 `scope` 是比较边界。只有属于同一事实范围的文档才互相比较型号、版本或术语集合。
