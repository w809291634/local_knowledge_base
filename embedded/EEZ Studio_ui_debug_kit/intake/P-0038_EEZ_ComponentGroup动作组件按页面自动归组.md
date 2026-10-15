# P-0038 动作组件按页面分组（ComponentGroup）：json2eez 自动生成组

- **状态**：fixed
- **发现日期**：2026-10-01
- **提示词**：PR-0064
- **标签**：EEZ-flow, ComponentGroup, 组件分组, 分区布局, 白名单, asar取证
- **归档备注**：本文件曾因 2026-10-01 早晨系统自动重启（NTFS 尾部未刷盘）丢失，
  由会话记录重建；同批 index.md / PROMPT_LOG.md / 2026-10-01.md 尾部 NUL 已截断修复。

---

## 一、现象（用户原话：「我看到有一个组功能，可以将同一个页面的 actions 放在一个组里面，这样就好看一些」）

P-0037 分列布局后，用户发现 EEZ 的 **ComponentGroup（组件组）**功能——
把同一页面的 actions 框进一个组，归属一目了然。

## 二、取证（asar `flow/component-group.js`）

```js
class ComponentGroup extends EezObject {
    description;   // 组名（树列表 label = description || "Group"）
    components;    // 成员组件 objID 数组
    // boundingRect 是 computed —— 由组内组件位置自动计算，无需存坐标！
    // classInfo 只有 description/components 两个字段，group 自身无 objID
}
```

## 三、修复（json2eez.py::build_page 末尾）

按 P-0037 的分区列（left 反推列号）自动归组：

```python
by_col.setdefault((left - (W0 + 20)) // 380, []).append(comp["objID"])
page_groups.append({"description": GROUP_NAMES[col], "components": by_col[col]})
```

- **白名单类型**：LVGLActionComponent + SetVariableActionComponent +
  **CompareActionComponent**（首版漏了 Compare，tabsync 组只收到 9/16，
  按全页类型分布 Counter 核对后补上）；
- **tabsync 水平链单独一组**（换页高亮同步链）；
- screen 等非动作组件不进组。

## 四、证据

- 4 组全建成、引用全有效、入组 37/37 动作组件全覆盖；
- `all.py --shots` EXIT=0（对照 8.62%、6 条 swipe 断言全过）。

## 五、沉淀

- ComponentGroup 零成本增补：只要组件坐标已分区，分组只是元数据一行；
- **白名单按「全页类型分布 Counter」核对**，不要凭想象列类型。
