# P-0248 开关无法切换：采样样板缺 CHECKABLE（用户判断正确）

> **检索别名**：开关点不动 / Switch 不切换 / CHECKABLE / EEZ 默认开关 /
> 拖拽样板不完整 / A13。

- **时间**：2026-11-05
- **工程**：`w78-tabview-smart-home`
- **触发**：仿真器里房间格开关无法切换；用户指出“EEZ 默认开关本来会切换，是不是样板没按拖拽生成”。

## 根因

- `eez_defaults.json` 的 `LVGLSwitchWidget` 采样自 watch 工程，`widgetFlags` 不含 `CHECKABLE`；
- EEZ 生成器按样板输出 `lv_obj_remove_flag(obj, LV_OBJ_FLAG_CHECKABLE|...)`；
- LVGL 的开关切换发生在 `LV_EVENT_RELEASED`，条件是对象有 `LV_OBJ_FLAG_CHECKABLE`
  （`lv_obj.c`）；标志被移除后，点击只会发事件，不切换状态。
- 对照：`two-state-styles` 工程里真实的开关样板带 `CHECKABLE`，生成代码是
  `lv_obj_add_flag(obj, LV_OBJ_FLAG_CHECKABLE)`。

## 修复

1. 从 `two-state-styles.eez-project` 取真实拖拽 Switch 样板，替换 `design/eez_defaults.json`
   的 `LVGLSwitchWidget`；`checkedState=false`、`states=""`，开/关由 `make_switch` 控制。
2. 重新生成 EEZ：`screens.c` 不再移除 `CHECKABLE`。
3. `eez_check` 新增 **A13**：所有 `LVGLSwitchWidget` 的 `widgetFlags` 必须含 `CHECKABLE`。
4. 去掉临时 native `switch_fix` 补丁（生成器修好后不需要）。

## 自证

无头发送真实状态序列 `PRESSED → RELEASED`：

```
[SWITCH] on:1->0  off:0->1
```

原来的 `CLICKED` 单发不会切换，不能拿来验证开关。

## 结果

- A1–A13 PASS；PC 仿真构建通过；D5 确认哈希仍有效（视觉未变）。
- 重新打开仿真器后，开关可正常切换。
