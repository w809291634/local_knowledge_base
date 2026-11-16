# AGENTS.md — 模板化文档生成规则（本目录适用）

> **工具无关**的规则入口：Trae / Claude Code / Cursor / Codex 等均可读取。
> Claude Code 可在 `CLAUDE.md` 写 `@AGENTS.md`；Cursor 在 `.cursor/rules/*.mdc` 引用本文件。
> 本目录方法**不针对某一项目**，适用于任何版式固定、内容按项目替换的文档族。
> **要按流程执行任务（含交给其他 AI 执行）：读 `authoring-workflow-and-experience-index.md`**，
> 它把 S0~S10 每阶段的动作、完成判据、该读的经验条目和停手条件串好，并有「症状 → 先读哪一条」反查表。

## 适用场景

按公司既定版式批量生成 / 迭代 Word 文档族，例如：医疗器械软件研究资料（PEMS：软件确认计划、
软件体系构架、软件需求说明书、软件详细设计说明、软件确认报告、软件描述文档、软件验证计划、
软件验证报告）、产品技术要求、说明书、验证/确认记录、设计文档等。

## PEMS 开工资料要求（2026-11-10 用户确认）

- **三项必填**：项目编号、项目名称、可读取的产品说明书。项目编号须由用户提供或从明确项目资料核实，不得用型号、软件版本或目录数字自动代替。
- **三项可选**：技术要求、程序源码、补充注意事项。未提供时标“未提供”，不因此阻断编写，也不逐项追问；说明书中已有的警示仍须读取。
- 新建、改版或接续编写时，开工回复先展示六项及其必填性、当前值／资料位置和状态；已有会话信息及已核实资料直接复用，不重复索取，不要求再次批准清单。
- 必填项缺失、不可读取或冲突时，一次询问缺失的必填项；期间继续资料盘点和模板检查。三项必填齐全后按可得证据开始编写，不用常识补造可选资料。
- 可选资料缺失不等于对应核查已完成；实测结果、通过结论、人员、日期和签署仍须对应的有效原始记录支持，无证据时相应记录栏留空，缺口记入项目工作目录。
- 六项清单模板、缺失资料的处理及提示词见 `yjt/PEMS/authoring-workflow-and-experience-index.md` §6；编写开工条件与受控发布条件分别判断。

## PEMS 参考资料优先级（2026-11-10 用户确认）

**补充注意事项 > 技术要求 > 程序源码 > 产品说明书**。

对同一项目、型号、版本和字段的明确说明发生冲突时，按此顺序采用高优先级内容，并在主事实文件／证据索引及生成记录中保留各来源原值、采用值和依据；已有优先级能解决的差异直接处理，不反复要求用户裁决。高优先级来源未提供或未说明该字段时，按顺序使用下一项，不补造内容，也不改变三项必填、三项可选的开工要求。

该顺序决定编写采用的口径，不将注意事项或技术要求当作源码已实现、实物已符合或试验已通过的证明。差异涉及实际实现或测试结果时，分别登记要求值、实现值和实测值，保留未闭环项。详细适用范围见 `yjt/PEMS/generality-boundaries-and-precedence.md` §一.1。

## 格式要求入口（2026-11-16 收口）

**所有格式要求（新增／修改／废止）一律在 `yjt/PEMS/reference-document-format-and-diagram-requirements.md` 对应「分类规则 -- X」节内进行**（2026-11-12 登记；2026-11-14 起按分类管理；2026-11-16 用户明确「新增和修改一律在此」）。该文件第六节为分类索引，每个分类用一个一级标题「分类规则 -- X」管理，其下详细要求为二级标题；引用库内既有条款处即真值来源，不重新定规则、不重复登记数值。**其他文件（判据集合、坑库、流程编排、模板基线件、工具脚本）只承担引用、判据、坑例与执行原语，不得就地新增或改写格式条文**；调整既有规则时先改该文件、再同步他处引用，发现冲突以该文件为准。

格式要求按类别查阅主文件：封面／目录／标题树／正文／字体颜色／表格／单元格对齐／页眉页脚／分页／页面设置／图示图题／字体与版式（跨分类专题），各自对应「分类规则 -- X」。本文件不再逐条登记格式条文。

PEMS 必须严格按当前明确的格式要求、已确认模板版号及受控修正编写，并在全过程落实检查；字体统一、脚本成功或 PDF 可导出均不足以证明格式合格。流程的必做动作与证据见 `yjt/PEMS/authoring-workflow-and-experience-index.md` §1.3、S2～S10，验收逐项对应 `yjt/PEMS/dod-checklist.md` B/F/G/H 组。开工冻结各文档格式基线；结构修复前保存副本；渲染失败不等于模板结构不可用，不得为使导出成功删分节、合并所有节或重建眉脚；所有交付文档必须对最终状态逐页渲染检查，抽检不能代替全页复核，旧 PDF 不能代替修改后的重渲染；未执行或失败的格式项不得勾为通过。豁免限于明确不适用或已有确认依据的具体位置，逐项登记理由与证据，不能批量填写「模板原样／按注册人口径」绕过真实格式缺陷。

## 硬约束（违反即返工）

1. **数据唯一**：项目事实仅写入当前项目指定的主事实文件（`facts.yaml`、`facts.json` 或受控 `config.json` 三选一）；禁止在脚本、经验库或文档中另写一套。
2. **格式靠继承**：以参考文档 `.docx` 为模板「就地替换」，**禁止从零拼 Word**
   （会丢封面大标题、浮动封面表、目录域、页眉页脚、分节）。
3. **封面独立成页**；封面后不得出现空白页。
4. **输出到新版本目录**（`<族名>_V{n}/`），永不覆盖源文档与历史版本。目录名只放族名与轮次，模板版号与交付主体另立一轴；默认轮次由扫描既有目录推导，不写死在代码里（细则见 `iteration-and-versioning.md` §8~§9，坑见 `pitfalls.md` §88）。
5. **相同代码只写一份**：公共处理封装在 `tools/docx_ops.py`，项目只提供配置。
6. **三方收口**：每轮输出文档后，必须核对 **说明书 / 代码 / 注意事项** 三者一致性，
   冲突未清零不得发布（规则见 `consistency-gate.md` 第 5 节）。未提供的可选来源登记为“未提供／未核查”，不虚称三方一致，也不因缺少该来源阻断可得证据支持的编写。
7. **模板版号是独立的一条轴**：模板改版时旧版基线件与判据原样保留，新版单独建档；生成前先定 `template_version`，
   只取该版判据，两版判据与产物目录都不得互用。见 `iteration-and-versioning.md` §7。

## 每次交付前必做（6 步）

```
1) 使用当前项目主事实文件生成；调用本库脚本时执行 `python tools/build_docs.py --config <project-config.json>`，确认输出目录中的 `manifest.json` 已记录配置、事实文件、模板和产物的哈希。
2) 运行一致性检查；调用本库脚本时执行 `python tools/consistency_check.py --config <project-config.json>`。跨文档对比必须按 `scope` 分组，禁止把本来不应包含同一型号或术语的文档强行判为不一致。
3) soffice --headless --convert-to pdf --outdir out "某份.docx"   # 一次只转一份
   → 逐页 page_ink_coverage + grade_pages_by_ink：封面独立页 + 无空白页 + 页眉编号正确
     （不要用抽文字字数判空白页：中文 PDF 缺 ToUnicode 会双向误判，见 pitfalls.md §41）
3b) pagination_audit(doc, cover_texts=[封面文档名]) 按流程 S7 **分三类处置**：缺陷键清零，toc_field 只记录，redundant_breaks/numbered_not_in_tree/body_page_break 逐项结合结构与渲染分诊，修复或登记有证据的保留依据；不得要求全部返回键为空或写死键数；
    需修复时只用同源的 pagination_repair(..., apply=[本轮已确认的动作])，改完复跑 audit 并重渲染核账页数
    （流程见 `reference-document-format-and-diagram-requirements.md` 「分类规则 -- 分页」，终检项见 `dod-checklist.md` F 组，阶段编排见 `authoring-workflow-and-experience-index.md` S7）
4) 人工核对：图（图文一致）、签署栏、交叉引用文件名、他项目残留
5) **用 Word 只读打开每一份产物并记录页数**（LibreOffice 与 python-docx 都不报的损坏，Word 会报；
   典型诱因见 `pitfalls.md` 第 6/7 节）
6) 三方收口：说明书 / 代码 / 注意事项 逐参数核对 → 冲突清零（consistency-gate.md 第 5 节）
```

## 详细规范

| 文件 | 内容 |
|---|---|
| `authoring-workflow-and-experience-index.md` | **编写流程总编排**：S0~S10 每阶段的动作/完成判据/该读条目/停手条件、十条铁律、交付物最小集、续接纪律、开工六项资料清单与任务提示词、症状反查索引、机器环境占位符、一票否决清单 |
| `template-inheritance-in-place-replace.md` | 核心方法：就地替换 |
| `template-baselines.md` | 公司模板版式基线族入口：模板库**九份**的版号总表（交付族为**八份**、不含 RD-057，见 `authoring-workflow-and-experience-index.md` S2）、两档入库判定、跨程序页数口径、建档方法 |
| `template-format-audit-2026-10.md` | 模板自身的格式符合性审计（哪些是模板缺陷要在生成时修、哪些是原样保留、哪些要注册人裁决） |
| `templates/<版号>/<件名>_基线.md` | 与基线件同目录的变更清单：逐条列出删除/替换/改写/保留的原文、位置与复核判据；`template-baseline-deletions.md` 是这些清单的总表与指针 |
| `template-baseline-rdXXX-<版号>.md` + `templates/<版号>/*.docx` | 各文档各版号的独立基线档案与基线件；一份只描述一个版号，判据互不通用；不得按旧版骨架补回新版已删除的章节、目录或表格 |
| `reference-document-format-and-diagram-requirements.md` | **格式要求唯一写入口**：第六节分类索引；按「分类规则 -- X」分类管理，详细要求为二级标题；**新增／修改格式一律回此文件对应分类节** |
| `consistency-gate.md` | 多文档一致性对账 + 说明书/代码/注意事项**三方收口** |
| `iteration-and-versioning.md` | 迭代与版本管理 |
| `pitfalls.md` | 环境/格式坑 |
| `dod-checklist.md` | 交付质量清单（DoD） |
| `tools/docx_ops.py` | 通用原语库（统一封装，跨项目复用；标题文字一致性 `heading_text_sequence` / `check_heading_text_against_template`、字体统一判据 `non_baseline_font_runs`（含表格内段落，私用区 run 除外）） |
| `tools/fig_tools.py` | 配图绘制原语（框图/流程图；边界精确、箭头端点自动算） |
| `tools/build_docs.py` / `config.example.json` | 配置驱动的生成入口 |
| `tools/consistency_check.py` | 配置驱动的一致性检查 |
| `tools/release_ops.py` | 全 XML 文本扫描、页眉页脚/文本框受控替换、哈希与发布清单原语 |

## 环境

- Python 3 + `python-docx`；`.doc` 转换需 `pywin32`（Word 或 WPS）。
- 配图需 `matplotlib`（中文字体用 SimHei/Microsoft YaHei；**文档正文统一宋体时，图内也要改用 SimSun 重绘**，否则一眼看出不统一，见 `reference-document-format-and-diagram-requirements.md` 「分类规则 -- 字体与版式」）。
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
  见 `reference-document-format-and-diagram-requirements.md` 「分类规则 -- 字体与版式」§6/§7 与 `tools/docx_ops.py:unify_document_fonts`。
- 承接旧稿做块对齐时：空段先剔除、封面区与目录域禁止插入、刷新后比对目录条目数，
  超阈值还原备份（`pitfalls.md` §11/§12）。
- **承接与槽位是两条写入轨道，必须互相查重**：写前用"本轮正文池"拦承接／插入，写后全量扫
  `dup_kind` 四形态（exact／near／same-lead／contained），优先级 本轮正文 > 模板原样 > 承接；
  两段都是模板原样时只报不删，去重前确认独有事实已并入保留段（`pitfalls.md` §16）。
- **段落版式按"生效版式"对齐**：本轮新写段以就近模板段为锚点，先双向对齐 `pStyle` 再抄其直接
  pPr；只读段落 pPr、用多数派或互相参照都会误伤模板（`pitfalls.md` §18、
  `reference-document-format-and-diagram-requirements.md` 「分类规则 -- 字体与版式」§8）。闸门两条：无重复正文段、本轮正文段版式与锚点一致。
- 同锚点多段插入必须按顺序 `append`；闸门校验承接段先后与来源版一致（`pitfalls.md` §17）。
- 渲染复用只在"PDF 不比 docx 旧"时成立；页码补丁必须在渲染之后跑（`pitfalls.md` §19）。
- 详细规则见 `one-pass-quality-gate.md`、`reference-format-profile-template.md` 与格式主文件 `reference-document-format-and-diagram-requirements.md`（图示要求见「分类规则 -- 图示图题」）。

## 通用性边界

- 通用经验库不得写入具体项目名称、项目号、型号、芯片、版本、阈值、人员、测试结果或结论。
- 案例、历史文档和格式档案仅用于方法与版式参考，不能作为新项目事实来源。
- 事实来源、证据边界和发布条件遵循 `generality-boundaries-and-precedence.md`；**必备图示与图示格式要求见格式主文件 `reference-document-format-and-diagram-requirements.md` 的「四、必备图示」与「分类规则 -- 图示图题」**。

## 格式执行与证据纪律索引（非格式条文）

以下为执行／判据纪律的**索引**，不是格式规格；格式要求一律见 `reference-document-format-and-diagram-requirements.md`，判据真值在 `pitfalls.md`／`dod-checklist.md`，流程编排在 `authoring-workflow-and-experience-index.md`。

- **原语**：分页审计 `tools/docx_ops.py:pagination_audit(doc, cover_texts=[...])`，修复 `pagination_repair(doc, cover_texts=[...], apply=[...])`，渲染侧 `page_ink_coverage(pdf)` + `grade_pages_by_ink(cov)`；项目里不再自写第二套。字体统一、段落基线、标题字号收口见「分类规则 -- 字体与版式」§1~§10。
- **判据形态与回归**（`pitfalls.md` 编号）：修复动作不得污染自己的判据 §45／§46、空段三种命运 §47、修完分页三项回归 §48、判据对象选错 §49、无头 Office 状态残留 §50／§44、新判据入库后回扫上一轮脚本 §57、判据跑不起来必须失败退出 §58、补空段排在删空段之后 §59、闸门全绿不等于文档没错 §68、改完别急着信自己 §69、留空改实值的一类风险 §70、结果列白名单不许整条关 §71、对账表每个 ✅ 可脚本反查 §72、插入正文段不克隆供体 §67。
- **第二轮改同一批文档**：槽位「已消费」按段落元素身份记录 §31、同一标签多处出现必须全部改 §32、生成器与闸门共用同一豁免函数 §34、版式收口排在 Word 刷新目录之后并重算交付清单哈希 §36、渲染判据分级 §37、断词不合并段落 §27、两个静默失效写法 §64。
- **闸门封装**：上述判据已封装为 `tools/docx_ops.py:pagination_audit` 返回键（`hard_page_breaks`／`stacked_breaks`／`body_page_break`／`keep_on_body`／`chapter_pad`／`outline_anomaly`／`numbered_not_in_tree`／`toc_field`）；交付时直接调用，不要另写。
