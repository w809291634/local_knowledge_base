# EEZ_Studio_examples/ — EEZ Studio 示例工程库（说明）

> 这里收 **EEZ Studio 示例工程**：一个工程一个独立子目录，每个工程演示一类用法、提供一份可拷走复用的实例。
> 通用方法论与调试工具**不在这里**，在 `embedded/EEZ Studio_ui_debug_kit/`（先读它的 `README.md`，再读 `PLAYBOOK.md`）。
> 本文件回答两个问题：**怎么获取 EEZ Studio 的使用经验**、**怎么建子目录保存工程文件夹**。最后更新：2026-10-19。

---

## 1. 怎么获取 EEZ Studio 的使用经验

按优先级四条途径：

### 1) 先查本库已有的积累（最快）

- `embedded/EEZ Studio_ui_debug_kit/PLAYBOOK.md` —— 通用方法论：三层图策略 / 差异量化四步法 / 组件树 8 个通用坑 / 十条红线
- `embedded/EEZ Studio_ui_debug_kit/skills.md` —— 操作手册：自动设计 → 对照查验 → 仿真器真点击（含实战路径示例与 UI 测试条例 D/G/R）
- `embedded/EEZ Studio_ui_debug_kit/EEZ_FIRST_WORKFLOW.md` —— EEZ 为主、仿真为辅的栈专属流程：验证优先级金字塔 / 框架分层 / 七步主链
- `embedded/EEZ Studio_ui_debug_kit/cases/`、`intake/`、`prompts/` —— 历史案例、问题登记、提示词留痕（按每条记录的「工程」字段区分）

### 2) 官方渠道

- **官方 Reference Guide 本机存档（2026-10-19 起，查原文先翻这里，不必上网）**：
  `embedded/EEZ Studio_ui_debug_kit/EEZ-Studio-reference-guide.pdf`（784 页；
  全量文字版同目录 `reference_guide_raw.txt`，结构化提炼在其 `reference/01~07`）
- 源码与文档：<https://github.com/eez-open/studio>（`docs/` 目录有使用文档）
- **新建工程向导里的 Templates / Examples**：官方自带模板工程，是最直接的写法参照
- 仓库 issues 区搜报错关键字（很多坑别人已踩过）

### 3) 做示例工程积累（本目录的用途）

每学会一类用法（某个控件、某种动作/事件流、某种 LVGL 集成方式），就做一个最小示例工程落库，
见第 2 节的目录规范。踩的坑随工程写进该工程的 `README.md`，下次直接查。

### 4) AI 协作留痕

每次让 AI 改 EEZ 工程，把原始提示词与新问题追加进 ui_debug_kit 记录区：

```bash
python ui_debug_kit/tools/log_entry.py prompt "用户的原始提示词" --tool <AI名>
python ui_debug_kit/tools/log_entry.py problem --title "<标题>" --symptom "<现象>" --root "<根因>" --fix "<修复>"
```

规约见 `embedded/EEZ Studio_ui_debug_kit/INTAKE.md`。

---

## 2. 怎么建本地子目录保存工程文件夹

**一个示例工程 = 一个独立子目录**，目录名即示例主题（kebab-case，见名知意）：

```
embedded/EEZ_Studio_examples/
├── README.md              ← 本文件
├── <示例主题>/             ← 每个工程一个独立文件夹
│   ├── README.md          ← ★ 必备（写什么见下）
│   ├── <工程名>.eez-project
│   └── ...
└── ...
```

### 新建一个示例工程的固定动作

1. 在本目录下新建 `<示例主题>/` 子目录；
2. 拷入 EEZ 工程文件（`.eez-project`、`.ei`、`vars/` 等），
   **剔除可再生产物**：`build/`、`generated/`、SDK 拷贝、大体积缓存 —— Studio 与构建链能重新生成的不入库；
3. 为该工程写 `README.md`，最少写清四件事：
   - **演示点**：这个示例演示什么用法；
   - **工程结构**：关键文件各自是什么；
   - **依赖版本**：EEZ Studio 版本、LVGL 版本、目标平台；
   - **踩过的坑**：症状 / 根因 / 修法（沿用本库「文件名即结论关键词」风格，严重坑标题加 ★）;
4. 在本文件第 3 节索引表加一行，并同步仓库根 `README.md` 的 `### UI Debug Kit` 章节。

---

## 3. 示例工程索引

| 目录 | 演示什么 | 一句话 / 关键坑 |
|---|---|---|
| （暂无；新增示例后在此加行） | | |

---

## 4. 落库分流（与 `embedded/README.md` 第 4 节一致）

- **只在这个示例工程成立**（某屏布局、某工程的具体配置）→ 写进该工程子目录的 `README.md`；
- **换一个 EEZ 工程还成立**（组件树通用坑、对照查验方法、工具用法）→ 进
  `embedded/EEZ Studio_ui_debug_kit/` 记录区（`intake/` / `skills.md`），按 `INTAKE.md` 登记规约；
- **机器相关路径**：每台电脑不同的 B 类路径（工程根、仿真器根等）不得当事实写死，
  一律按 `{占位符}` 处理，判据见 `embedded/README.md` 第 6 节。
- 引用本库其他文件一律写仓库根相对路径（如 `embedded/EEZ_Studio_examples/<主题>/README.md`）。
