# P-0258 模板工程按 EEZ UI 拖拽重建（18 画布）

> **检索别名**：模板工程重建 / UI 拖拽 / 18 画布 / 松开稳定保存 /
> clickableFlag / 不要脚本生成 .eez-project。

- **时间**：2026-11-06
- **工程**：`eez-widget-templates`
- **触发**：旧模板不一致；用户令“新建一个 EEZ 工程，在 UI 中从控件面板拖到画布，松开稳定后保存；
  每个画布一个控件；不要用 Python 脚本创建 EEZ 工程”。

## 重建方式

1. EEZ Studio Home → CREATE → LVGL 9.4.0，创建新工程；
2. Pages 加 18 个画布，每个画布从 Components Palette 拖入一个控件，**松开稳定后保存**；
3. 删除默认 Main 页；最终 18 页，每页一个控件（Button 含子 Label）；
4. 只读 `extract_templates.py` 从保存后的工程提取 `templates/`、`defaults.json`、`manifest.json`；
5. 没有脚本生成/修改 `.eez-project`。

## 结果

- 18 页：Label/Button/Switch/Arc/Bar/Chart/Checkbox/Container/Dropdown/Keyboard/
  Led/List/Panel/Roller/Scale/Slider/Spinner/Textarea。
- 19 个模板（含 Screen）；`validate_templates.py` 逐字段对比 UI 工程：PASS。
- EEZ 构建：`Build successfully finished`。

## 与旧模板的差异

旧模板是“已有工程保存形态 + classInfo 片段 + hiddenFlag 手工补”，不是拖拽保存语法。
新模板以 UI 保存对象为准：

- 有 `clickableFlag`、`flagScrollDirection`、`scrollSnapX/Y`、`group`；
- 没有 `hiddenFlag`、`checkedState`；Keyboard 没有 `textarea`；
- `localStyles` 只有 `{objID}`；`flagScrollbarMode` 为空；
- `widgetFlags` 不含 `CLICKABLE`（点击由 `clickableFlag` 表达）。

## 影响

w78 旧工程仍是旧语法，A14 会报 0/813；需要另做一次 w78 字段集迁移。

## 关联

- PR-0568；旧问题 P-0249/P-0250/P-0252。
