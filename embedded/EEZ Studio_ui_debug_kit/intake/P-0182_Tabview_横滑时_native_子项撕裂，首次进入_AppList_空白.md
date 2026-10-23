# P-0182 · Tabview 横滑时 native 子项撕裂，首次进入 AppList 空白

- **工程**：watch（EEZ no-flow + LVGL 9.4）
- **日期**：2026-10-23
- **工具**：Codex
- **状态**：fixed
- **标签**：tabview,横滑,native子项,绝对坐标,撕裂,首次空白,rxroller
- **关联提示词**：PR-0349

## 现象（看到什么）

从主屏横滑进入 AppList 时图标撕裂；冻结滚轮更新后撕裂消失，但首次横滑过程整页空白，到位后图标才出现。

## 复现（怎么稳定重现）

启动后从表盘向左滑入 AppList；第一次进入时观察横滑过程与到位后的图标显示。

## 根因（真正的原因）

滚轮 center_axis() 取显示器绝对坐标，但原目标固定为屏幕宽高的百分比。AppList 页初始位于 tabview 右侧时，校准把子项提前推到页外；原先 60 ms 定时器在父级横滚中不断反向改 padding，因父子不同步导致撕裂。LVGL tabview 的 VALUE_CHANGED 会在最终吸附动画结束前发出，不能据此立即校准。

## 修复（做了什么）

watch/src/native/watch_list_native.c：目标改为 host_area.x1/y1 加宿主内百分比；祖先正在 lv_obj_is_scrolling() 时冻结子项更新；VALUE_CHANGED 只置 s_realign_pending，待横滚停止后由 cull 定时器一次性校准。

## 证据（数字 / 命令输出）

用户截图显示横滑过程全黑、仅有鼠标与性能叠层；用户确认最终修复后无闪烁且方向正确。GCC -fsyntax-only 通过，git diff --check 通过；LVGL 9.4 源码证实 tabview 以 content 容器 scroll_x 实现横滑，VALUE_CHANGED 由 scroll-end 回调在 set_active 后派发。

## 沉淀（新增断言 / 案例 / 文档）

已写 P-0182；可推广为 cases：原生子树放入可横滚 tabview 时，内部绝对坐标校准必须换为宿主相对坐标，横滚期间冻结子项几何更新。
