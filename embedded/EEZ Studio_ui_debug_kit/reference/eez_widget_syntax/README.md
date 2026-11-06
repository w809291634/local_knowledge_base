# EEZ 控件语法模板（UI 拖拽创建）

本工程覆盖 EEZ Studio LVGL 9.4 Components Palette 的全部 **36 项**控件。

- 39 个画布（Pages）：35 个“一页一控件”（`Tab` 不能独立成页，建在 `Tabview` 页内），
  外加 4 个 Tabview 变体页 `Tabview0/1/2/3`；
- 每个控件都是**从 Components Palette 拖到画布、松开稳定后保存**的；`Tab` 是拖到
  Widgets Structure 的 `Tabview` 行内（行下半区）落定后保存；
- 没有用脚本生成/修改 `.eez-project`；
- `templates/*.json` 是从这份保存后的工程只读提取的语法（36 控件 + Screen = 37 个模板），
  `templates/variants/` 另存 4 份 Tabview 整块形态（0/1/2/3 个 Tab）。

## 文件

- `eez-widget-templates.eez-project`：UI 创建并保存的源工程（39 画布）。
- `templates/<WidgetType>.json`：从各画布控件提取的语法模板（objID 已占位）。
- `templates/variants/LVGLTabviewWidget.tabs<N>.json`：Tabview 带 0/1/2/3 个 Tab 的整块形态。
- `defaults.json`：每类控件的页面、flags 与保存后的默认值（不含对象 ID/位置）。
- `manifest.json`：类型 → 页面/模板文件；`palette` 是面板显示名；`_variants` 列变体页与文件。
- `extract_templates.py`：**只读提取**，从保存后的工程重写 templates/variants/defaults/manifest。
- `validate_templates.py`：只读校验，逐字段对比模板与 UI 工程保存的控件，并校验占位符角色/覆盖完整性/defaults/manifest/变体。

## 关键语法口径

这是“拖拽后保存”的语法，不是拖动中的临时 payload，也不是 classInfo 片段：

- `clickableFlag: true` 表示可点击，`widgetFlags` **不含 `CLICKABLE`**；
- 有 `flagScrollbarMode`、`flagScrollDirection`、`scrollSnapX/Y`、`group`；
- **没有** `hiddenFlag`、`checkedState`；
- `localStyles` 常见只有 `{objID}`；Keyboard、MessageBox 与 Button 子 Label 保留实际
  `definition`（如 align），不要删；
- 三个身份角色用独立占位符：`__OBJID__` / `__STYLE_OBJID__` / `__LOCAL_STYLE_OBJID__`；
  Button 子 Label 用 `__CHILD0_*`，Spangroup 的 span 用 `__SPANS0_OBJID__`；
- 模板**不带 `identifier`**（放置/克隆时才赋值）；
- Keyboard **没有** `textarea`（绑定后才会出现）；
- Button 子 Label 是完整 Label 字段集。
- Tabview 的 0/1/2/3 个 Tab 实测**只差 `children` 数量**，其余字段与每个 Tab 对象完全相同；
  多 Tab 一律整块克隆 `templates/variants/`，不要拿基础模板手拼 `children`。

## 面板名与类型名

多数面板名等于控件类型；不同名的只有：

- `Spangroup` → `LVGLSpanWidget`
- `Tab` → `LVGLTabWidget`（挂在 `LVGLTabviewWidget` 内）

`Label`、`Spinner`、`Image`、`AnimationImage`、`Canvas`、`Line` 保存后没有
`clickableFlag`，其余控件有。

## 使用

1. 克隆 `templates/<WidgetType>.json`；
2. 按角色给占位符换新 UUID，并赋新的 `identifier`；
3. 只改几何/文本/样式值，不增删字段；
4. Switch 保留 `CHECKABLE`；Button 保留唯一子 Label；
5. `Tab` 只能复制到 `Tabview.children` 下；`Tab` 的 `tabName` 是页签标题；
   要 N 个 Tab 就整块克隆 `templates/variants/LVGLTabviewWidget.tabs<N>.json`（N=0~3）；
6. 改动 UI 工程后跑 `python extract_templates.py` 再提取，跑 `python validate_templates.py` 校验。

> Screen 是页面根节点，不是 Palette 拖拽控件；它的模板从页面根提取，`children` 清空。
> EEZ 画布拖放一律落在页面这一层；要把控件放进某个容器/Tabview，必须拖到
> Widgets Structure 对应行内（行下半区），不能只看画布位置。
