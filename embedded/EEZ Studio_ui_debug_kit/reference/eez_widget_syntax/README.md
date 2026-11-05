# EEZ 控件语法库（初始控件模板）

真值来源：`C:\Users\yjt54\Desktop\EEz_stidio_examples\eez-widget-templates`（真实拖拽工程提供字段集 +
EEZ `classInfo.defaultValue/defaultFlags` 复位标准值 + EEZ 构建验证）。
**新建控件只从这里克隆**，不要临时去别的工程抓样板，也不要手写字段。

## 文件

- `templates/<Type>.json`：控件初始字段集（含默认样式/子结构/标志），值已复位为标准默认值。
- `defaults.json`：标准默认值真值表（几何、单位、标志、文本、选项、值域、localStyles）。
- `manifest.json`：每类模板的源工程与源 identifier（仅字段集来源）。

## 使用

1. `copy.deepcopy(templates[type])`。
2. 给 `objID` / `style.objID` / `localStyles.objID` 及所有子对象换新 UUID。
3. 复位表达式：所有 `*Type` 为 `literal`；`hiddenFlag/checkedState/disabledState` 用 literal。
4. 只改 `identifier`、`left/top/width/height`、`text`、`localStyles` 的值。
5. 跑 A10（字段集）与 A13（Switch CHECKABLE）；按钮跑 A4（恰一子 Label）。
6. 模板变更后先跑 `python validate_templates.py`：逐项对照 `defaults.json`，任何非标准
   几何/标志/文本/选项/值域/localStyles 都判 FAIL。

## 类型

Label / Button / Container / Panel / Switch / Slider / Bar / Arc / Chart / Scale / Led /
Checkbox / Dropdown / Roller / Textarea / Keyboard / List / Spinner（+ Screen）。

## 硬约束

- **模板必须是标准新建值**：字段集来自真实拖拽，属性值来自 EEZ classInfo；不得保留源工程的
  自定义颜色/圆角/字体/文案/尺寸（如 Switch 的 iOS 配色、Button 的 `cn14`）。
- **Switch `widgetFlags` 必须含 `CHECKABLE`**；LVGL 在 RELEASED 靠它切换。
  验证发 `PRESSED → RELEASED`，只发 CLICKED 不会切换。
- Button 恰一个子 Label，文字在子 Label；按钮自身无 text。
- 模板里的 objID 是占位符，严禁原样拷进工程（会撞 ID）。
- 模板已把表达式字段改成 literal；克隆后仍要再检查，防止带入 `get_var_*`。
