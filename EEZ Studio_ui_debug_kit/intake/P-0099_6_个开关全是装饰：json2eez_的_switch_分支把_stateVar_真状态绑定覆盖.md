# P-0099 · 6 个开关全是装饰：json2eez 的 switch 分支把 stateVar 真状态绑定覆盖成 literal

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：open
- **标签**：switch,json2eez,checkedStateType,stateVar,假反馈,审计
- **关联提示词**：PR-0136

## 现象（看到什么）

用户报 UI 中好多按钮和功能没有实现。审计产物发现：拨开关外观会翻（LVGL 给 switch 加了 LV_OBJ_FLAG_CHECKABLE，lv_switch.c:124），但真值/NVS/硬件全没动，也不由变量回显 —— 给了假反馈。

## 复现（怎么稳定重现）

对照 test.eez-project：6 个 LVGLSwitchWidget 全是 checkedStateType=literal 且无 eventHandlers；screens.c 的 tick 段一次都没引用这些对象。命令通道其实早就建好（native_vars.cpp 里 set_var_mic_en 等到 app_set_output 都有）。

## 根因（真正的原因）

json2eez.py 同一函数体内前后两段互相覆盖：375-383 通用路径在 node 带 stateVar 时正确写 checkedStateType=expression + checkedState，但 494-496 的 switch 专属分支随后无条件把 checkedState 写成字面量、checkedStateType 改回 literal。所以 build_ui.py 里 switch(..., stateVar=wake_en) 从 P2④ 起就没生效过；此前目检只看外观，截图是对的，没人真去拨它。

## 修复（做了什么）

待改：switch 分支尊重 stateVar（有绑定时不覆盖成 literal），并给 6 个 switch 补齐 stateVar（mic_en / dnd_en / auto_brightness / wake_en / wake_dnd_en / wifi_on）。验收用走路器 toggle（发 RELEASED）看 io_pc 是否打出对应命令 + 钉态回显一致。

## 证据（数字 / 命令输出）

统计口径：checkedStateType=expression 全工程仅 3 个且都是容器胶囊（np_shuffle/np_repeat/np_mute）；滑杆 9 个都绑了变量，所以只有开关坏。审计脚本 build/_ui_action_audit.py 一条命令复跑。

## 沉淀（新增断言 / 案例 / 文档）

新增可复用审计：可交互控件对象集 减 有事件回调集 = 死控件名单；MEMORY.md 加一条改完控件要拨一遍不只截图
