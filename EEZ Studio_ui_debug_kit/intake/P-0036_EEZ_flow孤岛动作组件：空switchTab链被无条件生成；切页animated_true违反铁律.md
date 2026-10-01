# P-0036 EEZ flow 孤岛动作组件：空 switchTab 链被无条件生成；切页 animated:true 违反铁律

- **状态**：fixed
- **发现日期**：2026-09-30
- **提示词**：PR-0062
- **标签**：EEZ-flow, 孤岛组件, connectionLines, switchTab, animated, LV_ANIM_OFF, 铁律

---

## 一、现象（用户原话：「我发现 eez 里面的 actions 有很多没有使用的，没有箭头互连的」）

EEZ Studio GUI 打开工程，Main 页 flow 里能看到没有箭头互连的 LVGLActionComponent。
实测工程 JSON（Main 页）：39 组件 = 1 ScreenWidget + 38 LVGLActionComponent，
38 条 connectionLines——其中 **1 个空 `actions` 的组件没有任何连线**（真孤岛），
其余「看起来没连」是动作组件排布在画布右侧（left=820）一列、事件连线是
widget→面板的长线，视觉上易误读。

## 二、根因

1. **空链也生成组件**：`json2eez.py::build_page` 的 tabsw 循环对每条 switchTab
   无条件 `components.append` + `connection_lines.append`。P-0034 之后 pop 行
   （网络与连接）的 switchTab 已无 clear/add/tab —— 生成了**零动作组件**，
   在 GUI/写盘环节表现为无箭头孤岛。
2. **连带抓出铁律违规**：17 个 `tabviewSetActiveTab` 全部 `"animated": true`
   —— 违反用户铁律「程序切 tab 必须 LV_ANIM_OFF」（P-0029：在途动画会被陈旧
   SCROLL_END 按旧目标位拉回）。当时只在 native/滑动路径上修了竞态，
   **EEZ 声明层的 animated 字段漏了**。

## 三、修复

`design/json2eez.py::build_page`（tabsw 循环）：

```python
if st.get("tab") is not None:
    actions.append({..., "animated": False, ...})   # ★ 铁律
if not actions:
    continue          # 空链不建组件、不连线
```

## 四、证据

- 重建后：组件 38（screen + 37 action）、连线 37、**非 screen 孤岛 0**、
  `animated` 分布 `{False: 17}`。
- `all.py --shots` EXIT=0：6 条 swipe 断言全过（ANIM_OFF 下点击切页瞬切，
  无在途动画，竞态路径物理消失）、11 屏对照 8.63% 无缺屏。

## 五、沉淀

- **铁律要落到每一层**：LV_ANIM_OFF 不只在 native 调用点遵守，
  EEZ 工程字段（`animated`）也是它的载体 —— 声明式实现里「字段就是代码」。
- 生成器不变量：**没有动作就不生成组件/连线**，空壳组件对 GUI 是垃圾、
  对审计是噪音（本次正是用户从 GUI 孤岛顺手揪出 animated 违规）。
