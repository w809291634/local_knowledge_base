# 模板化文档生成（通用方法论）

本目录沉淀「按固定版式批量生成并迭代 Word 文档族」的方法、脚本与踩坑。
**方法通用，不绑定某一项目**；项目专有信息仅保存在项目目录的受控事实文件与证据索引中。经验库中的案例必须匿名化，仅说明方法。

## 文件

| 文件 | 内容 |
|---|---|
| `AGENTS.md` | **规则入口**（工具无关，AI 工具先读这个） |
| `authoring-workflow-and-experience-index.md` | **编写流程总编排**：S0~S10 阶段（动作/完成判据/该读条目/停手条件）、十条铁律、交付物最小集、续接与会话纪律、开工六项资料清单（3 项必填、3 项可选）、参考资料优先级、§1.3 严格格式执行及阶段证据、任务提示词、症状→先读哪一条反查表、机器环境占位符、一票否决清单 |
| `template-inheritance-in-place-replace.md` | 核心方法：以参考文档「就地替换」 |
| `template-format-audit-2026-10.md` | 九份模板的格式符合性审计：逐份结论表、27 张越版心表、通道差异（LO 造空白页/静默失败）、保留·生成时修·待裁决三分类 |
| `pems.config.json` | **通用口径唯一可改处**：交付族成员、各文档默认 `template_version`、026 基线件与 SHA-256、版本写法策略、HASH 策略、代码行数口径、页数判据口径、文件编号与用例编号格式、闸门默认项。改默认只改这里，md 只做解释与快照 |
| `template-baselines.md` | **公司模板版式基线族入口**：九份文档的版号总表（页眉原值、WPS/Word 页数、目录形态、是否入库）、零残留入库判定、页数判据口径（最终渲染 + `NUMPAGES`）、建档方法 |
| `template-baseline-rdXXX-<版号>.md` | 各文档各版号的独立版式基线档案（已建：026 2.1_v1/v2/v3、028 2.1、029 2.1、030 2.1、032 1.0/2.1、057 1.0/3.0、068 1.0、069 1.0）；一份只描述一个版号（同版号多实例用 `_v1`/`_v2` 区分），判据互不通用 |
| `template-baseline-deletions.md` | 基线件总表与指针：九份模板的原件/基线件双哈希、档级、通用残留计数口径；逐条变更清单在基件同目录的 `…_基线.md` |
| `templates/<版号>/*.docx` | 基线件（按版号分子目录，**模板库共 9 份**；交付族为 8 份、不含 RD-057，每份配同目录 `…_基线.md` 变更清单）。**RD-026 默认用 2.1_v3**（格式档案档，`templates/2.1/…_v3.docx`；同目录 v1/v2 仅历史对账），**RD-068/069 默认用 1.0_v2**（`templates/1.0/…_v2.docx`；1.0 原版仅历史对账）；其余为格式档案档（含残留，不得当空白模板用）。两档均登记基线件与来源原件的 SHA-256 |
| `content_templates/*.docx` | **内容结构模板**（与 `templates/` 分开，不计入模板库九份）：登记"章节结构＋文字句式＋表格形态"的参照件，含项目残留。已入库：**RD-026 2.1_v3**（docx 与默认模板同一份，仅存说明）、**RD-032 2.1**、**RD-069 1.0**；生成时照结构与句式，事实按项目 `facts.yaml` 替换。路径与哈希在 `pems.config.json` → `content_structure` |
| `personnel_rosters/` | **人员花名册（私有）**：按单位分目录、文件名带版本日期；含身份证号等敏感信息，已 gitignore，不得提交或写入交付文档。S1 只取「姓名｜部门｜职位」，先出五类候选名单交注册人确认后再写入文档；版本索引见 `personnel_rosters/INDEX.md` |
| `reference-document-format-and-diagram-requirements.md` | **格式要求唯一写入口（新增／修改一律回此文件对应分类节）**：第六节分类索引；其下按「分类规则 -- X」一级标题分类管理（封面／目录／标题树／正文／字号／字体颜色／表格／单元格对齐／页眉页脚／分页／页面设置／图示图题／字体与版式），各类详细要求为二级标题；**字号数值唯一登记处为「分类规则 -- 字号」** |
| `consistency-gate.md` | 多文档同数据一致性对账 + 说明书/代码/注意事项三方收口 |
| `iteration-and-versioning.md` | 迭代机制与版本管理 |
| `pitfalls.md` | 环境与格式坑（含"Word 判文件损坏"三坑、文本框节点级替换；§38–§42 分页控制属性误用、双重分页空白页、布尔属性 `w:val`、中文 PDF 空白页判据、标题/图题判据收紧；§45–§50 分页时序与形态、空段三种命运、域平衡与页数核账、闸门误报、无头实例瞬时失败；§51 表格几何异常（负缩进/浮动/单元格 nil/列宽污染）、§52 封面留白统一、§53 标题编号机制三态混用；§54 只有大标题分页与目录页码同步、§55 标题分档/零缩进/封面大标题被压、§56 空白页另外三种形态；§57 新判据入库后回扫旧脚本、§58 判据降级必须失败退出、§59 补空段时序与显式写零；§61 连续回车顶页造成的空白块、§62 补空格正则要按最长合法前缀；§63 封面居中 14pt 与空行法、§64 lxml 真值与配置解析器键模式两类静默失效；§65 自动编号的字形藏在 numbering.xml 的 lvl/rPr、§66 标题统一要量到渲染层（逐字 bbox 三条判据）、§67 插入正文段不要克隆供体（"文字正文·样式标题"两条链路都不管）、§68 闸门全绿不等于文档没错（正文字号/标题间距/表头底纹/眉脚残留/编号字形五类盲区，生效值审计分三层）、§69 改完反而更糟的三个坑（按索引批量删元素自我移位、点名替换的时序与幂等、图片清理挂在"要插图"条件上）、§70 把"留空"改成"实值"引出的三类新缺陷（否定说明命中自家禁用词、台账值混解释拼出重复短语、带括注组合值被说两遍；禁用词表与台账要成对更新）、§71 注册人要求"结果列填结论"时判据改白名单而非整条关闭（列名从表头解析＋豁免列必须填齐＋清空白名单必须全部命中）、§72 对账表的每个 ✅ 必须可被脚本反查（正向来源→产物＋反向产物数字→来源双向对账，有意不写也要占行留理由）；§73 模板里的架构图可能不是图（VML 形状 + 正文段缩进硬排版：残留要扫正文段、图区动不得、换项目不能靠替换图片）；§74 数图不能只数 `inline_shapes`（VML 图不计，WPS 稿会判成零图，判据要 media 与引用双口径）；§75 校验器必须读交付物本身（读过程副本会全绿但绿的是副本；换版先重跑判据再改档案；哈希要现场核对）；§76 模板自带表格普遍略超版心（越界量要算 tblInd 与所在节版心，基线件先存底，fixed 与 autofit 分开列）；§77 墨占比判据要按页型分级，LibreOffice 会静默转不出某些 docx（拿不到 PDF 就失败退出并换通道）；§105~§114 空章判据、标题树收紧（所有文档无例外）、表格 grid 越界归一、模板原样表只比 rows/cols/borders、「目录」进导航、AI 标签污染封面居中测量） |
| `dod-checklist.md` | 交付质量清单（Definition of Done）；F 组为分页与标题树终检 7 条 |
| `tools/docx_ops.py` | 通用原语库（统一封装共用函数；分页/标题树闸门 `pagination_audit` 与同源修复 `pagination_repair`（共用判据 `chapter_pad_map` / `sect_breaks_page_el`）、渲染判据 `page_ink_coverage` / `grade_pages_by_ink`、样式链生效级别 `effective_outline`、表格版式体检与修复 `audit_table_geometry` / `normalize_table_geometry`、正文表格边框 `set_table_borders_six_way` / 边框审计 `audit_table_borders`、表格文字居中 `center_table_text`、封面留白统一 `set_cover_spacers`、标题字号族内统一 `heading_format_profile_from` / `normalize_heading_format` / 跨档闸门 `check_heading_tiers`、编号机制审计 `heading_numbering_mechanisms`、正文段原语 `new_body_paragraph` / `demote_paragraph_to_body` 与"文字正文·样式标题"闸门 `body_paragraphs_with_heading_style`、编号字形 `normalize_numbering_glyphs` / `numbering_glyph_audit`、表头底纹 `unify_table_header_shading`、标题间距 `normalize_heading_spacing`、眉脚残留 `header_footer_text_audit`） |
| `tools/para_ops.py` | 段落级原语：重复段判据（四形态）、生效版式比对与锚点对齐、承接顺序 |
| `tools/fig_tools.py` | 配图绘制原语（框图/流程图/拓扑图；1 单位=1 英寸、边界精确、箭头端点自动算） |
| `tools/build_docs.py` | 配置驱动的生成入口 |
| `tools/config.example.json` | 配置模板 |
| `tools/consistency_check.py` | 配置驱动的一致性检查 |
| `tools/check_personnel.py` | 人员清单门禁：内容性人员表必填、签署类按状态、跨文档姓名一致 |
| `tools/check_quant_items.py` | 052 量化项门禁：§2.1.5 人员数／§2.1.6 时间工作量／§2.1.7 代码行数，禁占位 |
| `tools/check_version_history.py` | 052 更新历史门禁：§4.3 必须含「首次发布」（日期取《注意事项》软件发布时间、描述只写「软件首次发布」），修订类型不得为空 |
| `tools/check_rd030_revision.py` | 030 修订记录门禁：表头+1 行首次发布、固定布局、列宽总宽 ≤ 版心，防 V1/日期折行 |
| `tools/check_052_verification_table.py` | 052 §2.5.6 验证报告表门禁：与 069 逐条同源（行数/类别/名称/结果/是），序号列可选 |
| `tools/table_category_rules.py` | 表分类合并门禁：026 测试类别按大类合并、032/068/069 用例表无类别列、052 四列无序号且仅类别列合并（表头 tblHeader、keepNext） |
| `tools/check_required_inputs.py` | 必供材料门禁：型号须 `YJT-` + 5 位（如 YJT-12204）、软件 MD5 须 32 位并写入 052，缺失/占位即失败 |
| `tools/check_conclusion_results.py` | 结论↔结果联动门禁：032／069 有结论必须有结果且不矛盾 |
| `tools/check_refs.py` | 编号引用门禁：正文禁 QR/RD 模板编号，052 追溯矩阵验证报告→069、确认报告→032 |
| `tools/check_table_header_shading.py` | 表格底纹门禁：表头 D9D9D9、数据行无 `w:shd`、文字黑色；封面表与 RD-029/030 例外表除外 |
| `tools/baseline_fingerprint.py` | 生成模板结构基线指纹（tables/rows/VML 形状/内联图/标题/非空段/表内字数/节数），供产物做"缺失型"判据 |
| `tools/check_structure_baseline.py` | 结构基线门禁：产物各项不得少于基线、相邻表必须为 0、表内字数 ≥ 基线 60%；豁免走 `work/structure-allow.json` |
| `tools/check_template_tables_intact.py` | 模板原样表正校验：封面表、RD-029 第九章两张表单、RD-030 开发计划表须逐项等于模板 |
| `tools/check_cover_center.py` | 封面居中与 AI 标签门禁：第 1 页上下留白差 ≤14pt（页高 9%~91% 去眉脚带）、`AILabel` 图形 0 且无 AI 生成标记 |
| `tools/check_outline_tree.py` | 标题树门禁（2026-11-23 定为所有文档必须）：正文 ≥1 个 0 级且总数 ≥2、层级与编号一致、同名不重复、层级不断层、**「目录」标题与目录条目必须直接写 9 级（缺省即失败），目录区不得进导航**；表格单元格不得有 0~8 级 |
| `tools/check_table_overflow.py` | 表格越界门禁：渲染层文字不得越过左右版心，结构层 fixed 表宽＋缩进 ≤ 版心、禁止负缩进 |
| `tools/release_ops.py` | 全 XML 文本扫描、页眉页脚/文本框受控替换、哈希与发布清单原语 |

## 一句话总纲

**先定基线 → 以模板就地替换生成 → 脚本对账 + 渲染对拍 → 人工核对图与签署 → 版本快照归档。**

## 换项目三步

0. **先读 `authoring-workflow-and-experience-index.md`**，按它的 S0~S10 走；下面三步只是最短路径，不含阶段判据与停手条件。
1. 复制本目录（方法论与 `tools/` 无需改动）。
2. 建立项目主事实文件（YAML、JSON 或受控配置文件三选一）：填项目元数据、型号/配置、指标、版本、编号、术语和证据索引；调用本库脚本时生成适配的配置 JSON。
3. 指定参考模板（只读），依次跑 `build_docs.py`（核对 `manifest.json`）→ `consistency_check.py`（按 `scope` 对账）→ 渲染对拍 → 人工核图与签署。

## 质量与格式补充

- generality-boundaries-and-precedence.md：通用规则边界、参考资料优先级（补充注意事项 > 技术要求 > 程序源码 > 产品说明书）、声明证据边界和案例隔离要求。

- `one-pass-quality-gate.md`：事实基线、自动质量闸门、证据/签署状态与发布归档。
- `reference-format-profile-template.md`：项目模板格式档案的空白文字模板。
- `reference-document-format-and-diagram-requirements.md`：格式要求唯一写入口，含参考文档格式深度、必备框图、第六节分类索引，以及按「分类规则 -- X」一级标题分类管理的各类格式要求（详细要求为二级标题）。**新增或修改格式一律回本文件对应分类节**，不在其他文件就地改写。

## 工具使用边界

- `build_docs.py` 只接受主事实文件和项目配置提供的内容；模板只读，输出目录必须是新版本目录。已有输出默认会被拒绝，只有经过确认的重建才使用 `--force`。
- `manifest.json` 是本轮交付的可追溯快照：保留项目配置、主事实文件、模板和产物的 SHA-256 哈希；不要手工修改它。
- `global_subs` 会在正文、表格、页眉页脚和可见 Word XML 中复核替换；对于浮动文本框等非标准槽位，应把替换项登记在 `xml_subs`，再由残留词检查确认。
- `consistency_check.py` 的 `scope` 是比较边界。只有属于同一事实范围的文档才互相比较型号、版本或术语集合。
