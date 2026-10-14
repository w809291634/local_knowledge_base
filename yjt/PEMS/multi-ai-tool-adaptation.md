# 多 AI 工具适配：一套内容，多处引用（通用）

> 适用：希望同一套知识与规则在 Trae / Claude Code / Cursor / Codex / 其他 Agent 里都能被读到。

## 结论先行

**内容用纯 Markdown（工具无关），规则用「各工具约定的入口文件」引用同一份 `AGENTS.md`。**
不要为每个工具维护一套内容；脚本一律 **Python + 命令行**（跨工具、可复现），不依赖某个 IDE 插件。

## 1. 入口文件对照

| 工具 | 约定入口 | 放法 |
|---|---|---|
| 通用 / Codex / 多数 Agent | `AGENTS.md` | **真身**，放在项目根或被操作目录 |
| Claude Code | `CLAUDE.md` | 内容写 `@AGENTS.md`（引用）或直接复制 |
| Cursor | `.cursor/rules/*.mdc` | 引用 `AGENTS.md` 要点（可带 frontmatter） |
| Trae | `.trae/rules/*.md` | 同上 |
| 任意工具 | 纯 `.md` 知识片段 | 一主题一文件（TIL 式），本目录即此结构 |

> 本知识库根目录已有 `.trae/`、`claude-code/`、`cursor/` 等主题，做法一致。

## 2. 规则入口该写什么（模板化文档场景）

```markdown
# 文档生成规则（本目录）

## 硬约束
- 数据以 config.json 为唯一来源；禁止在脚本/文档里另写一套数值。
- 以参考文档 .docx 为模板「就地替换」；禁止从零拼 Word（会丢封面/目录/页眉）。
- 封面必须独立成页；正文不得出现空白页。
- 输出到新版本目录，永不覆盖源文档与旧版本。

## 每次交付前必做
1) python tools/build_docs.py --config config.json
2) python tools/consistency_check.py --config config.json
3) 渲染 PDF：一次一份，确认「封面独立页 + 无空白页 + 页眉编号正确」
4) 人工核对：图、签署栏、交叉引用文件名

## 详细规范
- ./template-doc-methodology.md（总纲）
- ./template-inheritance-in-place-replace.md、./cover-pagination-and-sections.md
- ./consistency-gate.md、./pitfalls.md、./dod-checklist.md
```

## 3. 让知识「工具无关」的三条

1. **单一事实来源**：数据只写在 `config.json`；文档、规则、脚本都引用它。
2. **纯文本资产**：知识片段 Markdown、脚本 Python；避免 `.docm` 宏与私有格式。
3. **可复现命令**：把「怎么跑」写成可直接复制的命令行（`python ...`、`soffice --headless ...`）。

## 4. 升级为 Skill（可选）

当「生成 + 校验 + 渲染对拍」被反复调用，可封装为一个 Skill，入口描述写清触发条件
（如「生成/更新该文档族时」），规则正文仍引用 `AGENTS.md` 与本文档，**避免双份维护**。

## 5. 跨工具协作注意点

- **不要假设工具会自动读上级目录规则**：在被操作的**具体目录**放一份 `AGENTS.md`，或让其引用的
  文件就近可达。
- **路径可配置**：脚本里避免写死绝对路径；基线、模板、输出路径做成配置项。
- **产物二进制不入库，数据与脚本入库**：仓库只放 `.py`/`.md`/`.json`，docx 产物按需另存。