# P-0260 模板库补齐到 Palette 全部 36 项

> **检索别名**：模板覆盖 18/36 / 面板 36 项 / 缺 18 类 / Tab 嵌套 /
> Widgets Structure 行内拖放 / LVGLSpanWidget / MessageBox localStyles。

- **时间**：2026-11-06
- **工程**：`eez-widget-templates`；镜像 kit `reference/eez_widget_syntax`
- **触发**：用户指出“新建工程只建了模板库已有的 18 类，上一轮对比自然是 0 差异；
  面板里另外 18 类根本没有模板可对”。

## 补齐

在同一个 EEZ UI 工程里追加，未用脚本改 `.eez-project`：

- 新增 17 个画布（ButtonMatrix、Image、Menu、MessageBox、QRCode、Spangroup、Table、
  Tabview、TileView、Window、Calendar、Imgbutton、Spinbox、AnimationImage、Canvas、Line、Lottie）；
- `Tab` 不独立成页：在 Tabview 页内，把 Palette 的 Tab 拖进 Widgets Structure 的
  Tabview 行内（行下半区）落定后保存；
- 最终 35 画布、36 个 Palette 控件、37 个模板（含 Screen）。

## UI 拖放口径（实测）

- **画布拖放一律落到页面这一层**：EEZ 画布 `onDrop` 固定 `addObject(page.components, obj)`，
  在 Tabview/容器上松手也不会嵌套；
- **嵌套只能走 Widgets Structure**：拖到目标行，且落点必须在行的**下半区**
  （`clientY > 行中心`）且 `clientX > 文本左边界 + 25`，才会判为 INSIDE；
  落在上半区会变成 BEFORE，仍是页面级兄弟；
- Tab 放到画布会变成 Screen 子对象，Checks 报
  `Invalid position of Tab widget inside Widgets Structure`。

## 新增类型的语法事实

- `Spangroup` 的控件类型是 `LVGLSpanWidget`，内容在 `spans[]`，每个 span 也有 `objID`；
- `MessageBox` 的 `localStyles` 保存为 `{objID, definition}`；
- `Image`、`AnimationImage`、`Canvas`、`Line` 保存后没有 `clickableFlag`；
  `Label`、`Spinner` 同样没有；
- `Tabview` 有 `selectedTab/selectedTabType`；`Tab` 有 `tabName/tabNameType`；
- 其余字段仍符合“拖拽保存语法”：无 `hiddenFlag/checkedState`、flags 不含 CLICKABLE。

## 脚本

- `extract_templates.py`：35 页 + Tabview 内嵌 Tab；`spans[].objID` 也换占位符；
  `manifest.palette` 记录面板名（`Spangroup`→`LVGLSpanWidget`、`Tab`→`LVGLTabWidget`）。
- `validate_templates.py`：35 页 / 37 模板；只把页面根控件与 Tabview 内的 Tab 当模板，
  Button 子 Label 不算；`localStyles` 允许 `objID` + 实际 `definition`；
  非可点击类型集合加入 Image/AnimationImage/Canvas/Line。

## 结果

- `python validate_templates.py`：**PASS（37 个模板）**；
- 面板 36 项与 `manifest.palette` 集合完全一致，无缺无多；
- EEZ Build 生成源码包含 tabview/table/qrcode/menu/msgbox 等新创建调用；
- kit 镜像 37 个模板 + defaults/manifest/README 与工程逐字节一致。

## 遗留

- 复核时 w78 工作树已回到迁移前的 HEAD（`git status` 干净），A14 为 **0/813**；
  不是本次模板扩充造成的。已按 P-0259 重放迁移收尾：A14 813/813、D1–D9 全 PASS。
