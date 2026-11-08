# P-0270 · EEZ LVGL 工程 connectionLines 自定义 schema 导致 displayName 异常、Pages 树空白

- **工程**：多参数监护仪 UI（multipara_monitor_ui）
- **日期**：2026-11-08
- **工具**：Trae
- **状态**：fixed
- **标签**：connectionLines,EEZ工程,跳转,no-flow
- **关联提示词**：PR-0622

## 现象（看到什么）

生成器给 userPage 写自定义 source/target/control 的 connectionLines；EEZ 打开后 Pages 面板空白、Components Palette 报 Error rendering component，控制台 Cannot read properties of undefined (reading displayName)。

## 复现（怎么稳定重现）

生成的 .eez-project 里任一 userPage 的 connectionLines 非空，数组元素带 source/target/control 而非 EEZ flow 的 output 引用；用 EEZ Studio 打开该工程即复现。

## 根因（真正的原因）

EEZ 把 connectionLines 当 flow 连线解析，期望 output 引用；no-flow 工程不该写自定义连线。

## 修复（做了什么）

LVGL/no-flow 工程 connectionLines 置空，跳转只用控件 eventHandlers；A 对账改为 design goto == eventHandlers == 生成 lv_obj_add_event_cb。

## 证据（数字 / 命令输出）

多参数监护仪 14 页/44 跳转：置空后 Pages 树显示 14 页，A 差异 0，44/44 回调。

## 沉淀（新增断言 / 案例 / 文档）

- `tools/eez_gen_template.py` 固定 `connectionLines=[]`，跳转只写控件 `eventHandlers`。
- A 声明层对账判据改为：design goto == 工程 eventHandlers == 生成回调，三者必须同为 44。
- 文档：NO_FLOW §2.2 生成器规则、`reference/eez_gen_template/README.md`、CHANGELOG v0.9.187。
