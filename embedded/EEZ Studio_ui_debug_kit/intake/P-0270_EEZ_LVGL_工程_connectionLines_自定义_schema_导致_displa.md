# P-0270 · EEZ LVGL 工程 connectionLines 自定义 schema 导致 displayName 异常、Pages 树空白

- **工程**：（待补）
- **日期**：2026-11-08
- **工具**：未知工具
- **状态**：open
- **标签**：（无）
- **关联提示词**：（无）

## 现象（看到什么）

生成器给 userPage 写自定义 source/target/control 的 connectionLines；EEZ 打开后 Pages 面板空白、Components Palette 报 Error rendering component，控制台 Cannot read properties of undefined (reading displayName)。

## 复现（怎么稳定重现）

（待补）

## 根因（真正的原因）

EEZ 把 connectionLines 当 flow 连线解析，期望 output 引用；no-flow 工程不该写自定义连线。

## 修复（做了什么）

LVGL/no-flow 工程 connectionLines 置空，跳转只用控件 eventHandlers；A 对账改为 design goto == eventHandlers == 生成 lv_obj_add_event_cb。

## 证据（数字 / 命令输出）

多参数监护仪 14 页/44 跳转：置空后 Pages 树显示 14 页，A 差异 0，44/44 回调。

## 沉淀（新增断言 / 案例 / 文档）

（待补）
