# EEZ 控件语法库（UI 拖拽创建模板）

真值来源：`C:\Users\yjt54\Desktop\EEz_stidio_examples\eez-widget-templates`。
该工程是在 EEZ Studio UI 里新建的 18 个画布，每页一个控件，**从 Components Palette 拖到画布、
松开稳定后保存**；`templates/` 是从保存后的工程只读提取的语法。
**新建控件只从这里克隆**，不要临时去别的工程抓样板，也不要手写字段。

## 文件

- `templates/<Type>.json`：拖拽后保存的控件语法（objID 已占位）。
- `defaults.json`：每类的页面、`defaultFlags` 与保存后的默认值（不含对象 ID/位置）。
- `manifest.json`：类型 → 页面/模板文件。

## 关键语法（与拖动中的 payload、classInfo 片段区分）

- `clickableFlag: true` 表示可点击，`widgetFlags` **不含 `CLICKABLE`**；
- 有 `flagScrollbarMode`、`flagScrollDirection`、`scrollSnapX/Y`、`group`；
- **没有 `hiddenFlag`、`checkedState`**（只有对应的 `*Type`）；
- `localStyles` 默认只有 `{objID}`；Keyboard 与 Button 子 Label 保留实际 `definition`（align），不要删；
- 身份角色独立占位：`__OBJID__` / `__STYLE_OBJID__` / `__LOCAL_STYLE_OBJID__`；
  Button 子 Label 用 `__CHILD0_OBJID__` / `__CHILD0_STYLE_OBJID__` / `__CHILD0_LOCAL_STYLE_OBJID__`；
- 模板**不带 `identifier`**（放置/克隆时赋值）；
- Keyboard 没有 `textarea`；Button 子 Label 是完整 Label 字段集。

## 使用

1. `copy.deepcopy(templates[type])`。
2. 按角色给占位符换新 UUID，并赋新的 `identifier`。
3. 所有 `*Type` 保持 `literal`；不要新增 `hiddenFlag/checkedState/textarea` 等字段。
4. 只改 `left/top/width/height`、`text`、`localStyles` 的值。
5. 跑 A10（字段集）与 A13（Switch CHECKABLE）；按钮跑 A4（恰一子 Label）。
6. 改 UI 工程后，在工程目录运行 `python extract_templates.py` 重提取、
   `python validate_templates.py` 逐字段校验（含占位符角色、覆盖完整性、defaults/manifest）；
   本经验库目录是它的镜像。

## 类型

Label / Button / Container / Panel / Switch / Slider / Bar / Arc / Chart / Scale / Led /
Checkbox / Dropdown / Roller / Textarea / Keyboard / List / Spinner（+ Screen）。

## 硬约束

- **模板只来自 EEZ UI 拖拽后保存的工程**；不要用脚本生成/修改 `.eez-project`。
- **Switch `widgetFlags` 必须含 `CHECKABLE`**；LVGL 在 RELEASED 靠它切换。
- Button 恰一个子 Label，文字在子 Label；按钮自身无 text。
- 模板里的 objID 是占位符，严禁原样拷进工程（会撞 ID）。
- 克隆后仍要检查表达式字段，防止带入 `get_var_*`。
