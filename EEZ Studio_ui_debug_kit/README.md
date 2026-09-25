# ui_debug_kit —— UI 调试与验收工具箱

> **把这个文件夹整个拷进任意 UI 工程，填一份配置文件，就立刻具备一套完整的
> "出效果图 → 对照定位 → 修复验收" 能力。** 方法论与工具都与具体框架解耦，支持持续迭代。
>
> **内核可移植、记录可累积。** 工具箱分两块：
> ① **内核**（`PLAYBOOK.md` / `CONFIG.md` / `tools/` / `cases/` / `config.template.json`）——
> 与具体工程解耦，拷到哪都一样；
> ② **记录区**（`skills.md` / `intake/` / `prompts/`）—— 会**随项目不断累积**（手册 / 新问题 / 提示词），
> 换工程时保留，靠每条记录里的 `工程` 字段区分。
> 你的工程差异（路径、字体、屏名…）只写在工程侧的配置文件里。

适用栈：任何"用组件树描述界面 + 由它生成代码"的 UI 方案，以及 Web/桌面/移动/嵌入式各类前端。

---

## 30 秒上手

```bash
# 1) 把 ui_debug_kit/ 拷进你的工程（放哪都行，工具会自动向上找配置）

# 2) 在工程里建配置：从模板复制一份，按 CONFIG.md 填写
cp ui_debug_kit/config.template.json ./ui_debug_kit.config.json

# 3) 自检：确认路径解析与关键路径存在性
python ui_debug_kit/tools/kit.py

# 4) 一键门禁（回归断言 A1~A10 + 静态体检 + 你挂的工程侧检查）
python ui_debug_kit/tools/run_gate.py

# 5) 手上有两张图要对照？（期望图 vs 实际渲染图）
python ui_debug_kit/tools/diff_report.py a.png b.png --overlay diff.png

# 6) 量一个元素到底有没有被裁（**墨迹**，不是控件框）
python ui_debug_kit/tools/ink_check.py b.png --box X Y W H --against <声明框的 L T W H>

# 7) 留痕：把用户提示词 / 新问题追加进记录区（任何 AI 工具都该做，见 INTAKE.md）
python ui_debug_kit/tools/log_entry.py prompt "用户的原始提示词" --tool <AI名>
python ui_debug_kit/tools/log_entry.py problem --title "<标题>" --symptom "<现象>" --root "<根因>" --fix "<修复>"
```

> 配置也可以放到别处，或用环境变量 `UI_DEBUG_KIT_CONFIG` 指定路径。

---

## 目录结构

```
ui_debug_kit/
├── README.md               ← 你在这里
├── PLAYBOOK.md             ← ★ 核心：通用方法论（三层图策略 / 差异量化四步法 / 基准标定法 /
│                              六类体检 / 组件树 8 个通用坑 / SOP / 十条红线 / 迁移清单）
├── skills.md               ← ★ 操作手册：A 自动设计 → B 对照查验 → C 仿真器真点击
│                              （含一份实战工程的路径示例 + UI 测试条例 D/G/R）
├── INTAKE.md               ← ★ 记录规约：新问题怎么登记、提示词怎么留痕（给任何 AI 工具看）
├── config.template.json    ← 配置模板（**纯占位符**）
├── CONFIG.md               ← 配置字段说明 + 迁移清单 + 常见配置错误
├── CHANGELOG.md            ← 工具箱自身的迭代记录
├── cases/                  ← ★ 案例库：把踩过的坑按七段式模板沉淀进来，越用越快
│   ├── README.md               案例写法模板 + 索引
│   ├── B1_字体源分配错误.md
│   ├── B2_保存时重算坐标.md
│   ├── B3_默认主题padding偏移.md
│   └── B4_异步渲染拿到旧帧.md
├── intake/                 ← ★ 记录区：开发中遇到的**新问题**（P-####），只追加
│   ├── README.md / TEMPLATE.md / index.md
│   └── P-0001_*.md …
├── prompts/                ← ★ 记录区：用户与 AI 的**提示词日志**（PR-####），只追加
│   ├── README.md
│   └── PROMPT_LOG.md
└── tools/
    ├── kit.py              公共库（配置解析 / 图像工具 / 文本度量 / 组件树遍历）+ 配置自检
    ├── log_entry.py        ★ 记录写入器（把新问题/提示词一致地追加进 intake/ 与 prompts/）
    ├── run_gate.py         ★ 一键门禁（回归断言 + 静态体检 + 工程侧扩展闸门，CI/pre-commit 用）
    ├── audit_ui.py         回归断言集 A1~A10：把踩过的坑固化成可执行断言
    ├── gen_clicks.py       从设计源自动生成 L2 真点击用例（含两类底栏回归）
    ├── tree_check.py       组件树静态体检（几何 / 换行 / 字体名 / 引用完整性 / 入口页）
    ├── diff_report.py      图像差异量化（直方图 + 热点聚类 + 差异标红图 + 目录批量）
    ├── ink_check.py        墨迹检测（包围盒 / 触边 / 与声明框对比算偏移）
    ├── text_measure.py     文本真实宽度与字形度量
    ├── README.md           工具索引（每个工具一句话 + 参数速查）
    └── cdp/                抓"原生渲染图"（Chromium / Electron 系通用）
        ├── launch.sh           按配置启动并等 CDP 端口就绪
        └── grab.js             通用抓图器（canvas / 整窗 / 界面文本）
```

> 栈专属的工具与脚本请放在**你的工程里**（例如 `design/` 或 `tools/`），不要放进本目录 ——
> 这样工具箱的**内核**才能保持"拷到哪都一样"。

---

## 记录区：让技能越用越强

> 结构规约见 **`INTAKE.md`**。**任何 AI 工具**（WorkBuddy / Cursor / ChatGPT / 人）都应遵守：
> 每轮对话把用户提示词追加进 `prompts/PROMPT_LOG.md`；遇到新问题登记进 `intake/`。

```bash
python ui_debug_kit/tools/log_entry.py prompt "用户的原始提示词" --tool <AI名> --link P-0001
python ui_debug_kit/tools/log_entry.py problem --title "<标题>" \
    --symptom "<现象>" --root "<根因>" --fix "<修复>" --evidence "<数字证据>"
python ui_debug_kit/tools/log_entry.py list          # 看已经记录了什么
```

- `intake/P-####_*.md`：**问题流水**（现象 → 复现 → 根因 → 修复 → 证据 → 沉淀）
- `prompts/PROMPT_LOG.md`：**提示词日志**（逐字抄用户原话，编号 `PR-####`）
- 两者用编号互引 → 可还原「**用户原话 → AI 定位 → 修复 → 沉淀断言**」的完整链条
- 一个坑彻底搞懂且能推广后，再按 `cases/README.md` 提炼进 `cases/`

---

## 四步工作法（详见 `PLAYBOOK.md`）

```
① 出图 ── 三层图，一张证明一件事
   设计预览图（设计源渲染） → 交叉验证图（编译产物渲染） → 原生渲染图（引擎本尊渲染）

② 量化 ── 不靠肉眼
   diff_report.py：big==0 → 一致；<0.05% 且形状一致 → 抗锯齿；否则看热点定位元素

③ 定位 ── 量墨迹，不量控件框
   ink_check.py --against：墨迹 − 声明框 = 实际偏移
   （非 0 就去查默认主题 padding —— 见 cases/B3）

④ 回归 ── 给数值证据
   tree_check.py + diff_report.py 全绿，才算修好
```

---

## 为什么要有这个文件夹

1. **知识可移植**：方法论写在 `PLAYBOOK.md`，与框架解耦；工程差异隔离在工程侧的配置文件。
2. **能力可执行**：工具是真能跑的脚本（标准库为主，Pillow 只有图像类工具才需要），不是伪代码。
3. **经验可累积**：`cases/` 是七段式的结构化沉淀，每解决一个问题就追加一条；
   下次同类问题**直接对号入座**。
4. **不被项目绑架**：工具箱与工程代码完全分离 —— 升级工具箱不动工程；
   工程换框架也不用重写工具箱（改 `tree_schema` 映射即可）。

---

## 迭代方式

- 新增一个坑 → 按 `cases/README.md` 的模板加一个 `cases/Bx_*.md`
- 新增一个检查 → 在 `tools/` 加脚本，并在 `tools/README.md` 登记
- 调整方法论 → 直接改 `PLAYBOOK.md`，在 `CHANGELOG.md` 记一笔
- 换了工程 → 只改工程侧的 `ui_debug_kit.config.json`（见 `CONFIG.md` 的迁移清单）

> 约定：**只往前迭代，不删历史。** 旧的判断被推翻时，在案例里写清"为什么当初误判"，
> 这比只留正确答案更有价值。
