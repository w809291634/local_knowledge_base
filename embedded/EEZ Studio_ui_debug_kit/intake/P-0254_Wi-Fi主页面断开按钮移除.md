# P-0254 Wi-Fi 主页面“断开”移除：只保留长按对话框

> **检索别名**：Wi-Fi 多一个断开 / 主页面断开 / 对话框断开 / 设计源 vs 成熟示例 /
> 控件 815→813。

- **时间**：2026-11-05
- **工程**：`w78-tabview-smart-home`
- **触发**：用户问“Wi-Fi 页面怎么多出来一个断开按钮”，确认后令“可以”。

## 原因

不是 EEZ 生成错误，是设计源在主页面多加了一颗：

- 主页面 `btn_disconnect` (528,96,104,30)：设计源 `wifi_frame()` + `pages.py` 控件行；
- 对话框 `btn_dlg_disconnect` (132,148,96,36)：设计源 `wifi_dialog_frame()`，父 `dlg_root`
  `hiddenFlag=true`，长按时才显示；
- 成熟示例 `app-wifi-scan-conn-no-flow` 只在长按对话框里放“断开”。

D5 只比较“EEZ 工程 vs 设计源”，设计源本身有主页面按钮，所以 D5 不会判多余。

## 修改

- `simple_control.wifi_frame()`：删除主页面“断开”，只留“扫描”；`WIFI_BOXES` 删 `disconnect`。
- `pages.py`：删除“断开”控件行，更新 Wi-Fi 页出口说明。
- `eez_gen.build_wifi_page()`：不再生成 `btn_disconnect`。
- `wifi_bind.cpp`：删除 `btn_disconnect` 回调；对话框 `btn_dlg_disconnect` 保留。
- `eez_check.py` / `behavior_audit.py` / `control_table.py`：同步移除必需对象/已接项，
  并修正 Wi-Fi 弹层行不计入基础页控件表的计数断言。

## 结果

- 控件 815 → **813**，A14 字段集 **813/813**。
- D5 重跑：24/24，平均 **98.03%**，最低 **95.89%**；Wi-Fi **99.56%**。
- NAV 72/72、UI 行为、flowtest/uitest/quittest 全 PASS；D1–D9 PASS。
- 设计产物已更新：H5、控件清单（Wi-Fi 只剩 3 行）、prototype、page map。

## 关联

- P-0253（全流程/测试夹具）；PR-0561。
