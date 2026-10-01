# P-0037 动作画布分区布局 + tab pager 编辑态查看结论

- **状态**：fixed
- **发现日期**：2026-10-01
- **提示词**：PR-0063
- **标签**：EEZ-flow, 画布布局, 分区, tabview, Active tab, 编辑态, identifier

---

## 一、现象（用户原话）

「tab pager 中多个页，所有的 actions 都显示出来，但是所有页没有显示出来，
导致有的 actions 指向空白的地方……能够编辑状态显示所有的 pager 吗」、
「eez 里面的 actions 排列很乱……看不到哪些是一个页面里面的」。

## 二、两个结论

### 结论 1：tab pager 编辑态**不能同时显示所有页**（LVGL 结构决定），但有官方秒切手段

- tabview 的多页是**叠放在同一矩形**里的（LVGL 结构如此），编辑器只渲染
  Active tab 那一页 → 未激活页的 widget 不渲染 → flow 连线指向「空白」。
- **官方途径（手册 W78.2.3 `Active tab`）**：Widgets 树选中 tabview →
  属性面板改 **Active tab**（零基索引）→ 画布立刻切到那一页。逐页查看编辑。
  ⚠ Active tab 同时是「初始页」——看完建议改回原值（main_nav=0、set_nav=0），
  以免改变上电初始语义（运行时被 switchTab 接管，影响小但语义干净）。
- 本工程全部 tabview `tabSize=0`（隐藏原生 tab 栏），画布上没有 tab 栏可点，
  **只能走属性面板/Widgets 树**，这是刻意设计（§11.9 tab pager 规则）。

### 结论 2：动作画布「乱」是生成端布局问题 —— 已按导航分区分列重排

原布局所有动作组件堆在 `left=820` 一列纵向排开，与页面归属无关。

**修复**（`json2eez.py::build_page`）：

```python
def _bucket(path):        # 从动作 path 的祖先链判分区（★顺序敏感：先判内层子导航）
    设置(m_set_nav/m_cats_/wifi_pop/net_/set_/disp_/wake_) → 列4
    AI(m_ai_nav/ai_) → 列0   音乐(m_mus_nav/np_/lib_) → 列1
    通知(notif) → 列2        其余(主导航/状态栏/全局) → 列3
_slot(path): 列 x = W+20+列号*620，行 y = 40+行号*90（列内计数）
```

- gotos / tabsw / setvars / flagacts 四类竖排组件全部走 `_slot(path)`；
- tabsync（onTabChange 高亮同步链）是**水平流水线**（getter→Compare→Add），
  保持横向，整链右移到分区列之后的专用区（`X0 = W+20+6*620+k*980`）。
- 分区列现状：AI 8 / 主导航 4 / 设置 9 / 音乐、通知空（无动作链）/ tabsync 区 16。

## 三、验证

- `all.py --shots` EXIT=0：6 条 swipe 断言全过、11 屏对照 8.63% 无缺屏；
- 组件/连线数量与重排前一致（38/37），仅坐标变化（objID 确定性，动作语义零变化）；
- **顺带修正了工程审计脚本的基准错误**：EEZ widget 名字段是 **`identifier`**
  （不是 `name`，也不是 identifiers 表——EEZ 动态收录被引用 widget）。以
  `identifier` 为基准复核：128 个动作引用 0 缺失、animated 全 False、
  tab 索引无越界（4 个 tabview 页数 4/4/2/3）。

## 四、沉淀

- 「查看别的 pager 页」 = 属性面板 `Active tab` 秒切（§11.9 tabSize=0 的代价
  与对策）。
- 审计脚本基准：EEZ 工程里控件名字段是 **`identifier`**；`identifiers` 表
  动态生成、不落盘。
- 画布布局是生成端职责：**布局即文档** —— 分区列让「动作属于哪个页面」
  不言自明，用户审 EEZ 工程的效率直接受益。

## 五、追加（PR-0064，用户追问「能够生成组名吗」）

- **组框本身不渲染文字**（ComponentGroupRenderer 只画 1px 边框；description 仅用于
  左侧树列表 label）。画布上要看得见组名 → 用 EEZ 官方 **CommentActionComponent**
  （黄色标题条 #fff5c2、`isFlowExecutableComponent:false` 不参与执行、collapsed
  态只显示标题条、`label: description`）。
- 实现：每组顶部 y=40 放一个 Comment（text/description=「分区名（组件数）」，
  collapsed:true；tabsync 每条链一个「换页高亮同步：主导航/设置」）。
  ⚠ json2eez 的 `check_identifiers` 要求所有组件带 identifier —— Comment 也要
  （`m_title_col%d` / `m_title_tabsync%d`），否则生成期即 FAIL。
- 最终：4 组全部带黄色标题条，42/42 组件入组（37 动作 + 5 标题）。
