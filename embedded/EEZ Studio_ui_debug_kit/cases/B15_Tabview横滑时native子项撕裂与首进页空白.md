# B15 Tabview 横滑时 native 子项撕裂、首次进入页面空白

> **检索别名**：tabview 撕裂 / 首次进页空白 / native 子树 / AppList 空白 /
> 子项不跟父页走 / 绝对坐标校准 / 横滑时图标消失。

## 现象

466×466 腕表 UI 使用隐藏 tab 栏的 LVGL `lv_tabview`：主屏左滑进入 AppList，
AppList 内容是挂在 EEZ 生成宿主下的 native Rxroller 子树。

- 初态：横滑过程中图标撕裂，像子对象没有随父页移动；
- 只冻结 native 更新后：撕裂消失，但**第一次**横滑过程整页黑，抵达 AppList 后图标才出现；
- 修复后：图标从右侧跟随 AppList 页面连续滑入，落位后位置不跳变。

## 证据

1. LVGL 9.4 的 `lv_tabview` 把所有 tab 页放进 content 容器，以
   `lv_obj_scroll_to_x(content, ...)` 做横向切页（`lv_tabview.c:110-143`）。因此
   AppList 页在初态位于主屏右侧，宿主的绝对 `x` 约为一屏宽 **466 px**。
2. 滚轮的 `center_axis()` 返回显示器绝对坐标；旧逻辑却把目标写为
   `host_width * 38% = 177 px`。隐藏页的正确目标应为 `host_x + 177 = 643 px`，
   两者正好相差一个页宽 **466 px**。旧标定会提前把滚轮子项反向推到页外，
   所以首次滑入时只见黑底。
3. `LV_EVENT_VALUE_CHANGED` 不能当作“滚动已经结束”的信号：tabview 的
   `SCROLL_END` 回调会先调用 `lv_tabview_set_active(..., LV_ANIM_ON)`，随后就派发
   `VALUE_CHANGED`（`lv_tabview.c:344-376`）。此时最终吸附动画仍可能在跑。
4. 用户提供的仿真截图只含黑底、鼠标和性能叠层（86 FPS / 22% CPU），无 AppList 图标；
   最终修复后用户确认“修复对了”。

## 曾经的误判

1. **只怀疑屏外 `HIDDEN` 回收**：移动期反复切 `HIDDEN` 的确会让纵向快滑中的行延迟出现，
   需要在滚轮移动时停止回收；但它解释不了“首次横滑整页空白”。
2. **横滑期间冻结全部子项就够了**：冻结消除了父子不同步导致的撕裂，却把已经按错误绝对
   坐标摆到页外的子项原样带入页面，因此空白更稳定地暴露出来。
3. **收到 `VALUE_CHANGED` 立即重标定**：该事件可能发生在最终吸附动画刚启动时；此时改子项
   padding/position，仍会和父 content 的滚动叠加，导致撕裂或到位跳变。

## 真因

同一份几何计算混用了两个坐标系：子项测量值是**显示器绝对坐标**，设计目标却是
**宿主局部坐标**。在可滚动父容器中，局部目标必须先加上父容器当前绝对原点。
同时，父页横滚期间修改子项局部几何，会让两套动画相互抵消或叠加。

## 修法

把校准目标统一到显示器绝对坐标：

```c
lv_area_t host_area;
lv_obj_get_coords(host, &host_area);
target_x = host_area.x1 + lv_obj_get_width(host) * CENTER_X_PCT / 100;
target_y = host_area.y1 + lv_obj_get_height(host) * CENTER_Y_PCT / 100;
```

再把更新分为两阶段：

1. 沿 `s_wheel` 的父链调用 `lv_obj_is_scrolling()`；任一祖先正在滚动时，
   不改 native 子项的 `HIDDEN`、padding、position 或 transform；
2. `VALUE_CHANGED` 只置 `realign_pending`。祖先完全静止后，再执行一次校准和屏外回收。

这样坐标在隐藏 tab 中就已正确，横滑过程只由父 content 的滚动统一搬运；到位后的
一次校准只是幂等确认，不会制造视觉跳变。

## 验证

1. 冷启动后，从主屏向左首次滑入 AppList：过程应连续显示图标，无黑屏、无撕裂；
2. 反向滑回主屏、再进入 AppList：结果一致；
3. AppList 内纵向拖动与惯性动画时，屏外行不应延迟出现；
4. `gcc -fsyntax-only watch_list_native.c` 通过，`git diff --check` 无空白错误；
5. 用户实测确认最终修复正确。

## 通用化

- **坐标公式**：若量测值是 screen/global 坐标，局部设计目标必须换成
  `parent_global_origin + local_design_target` 后再比较；不能直接比较全局量与局部量。
- **动画所有权**：父级负责分页/滚动时，子级在该时间窗只能被动继承位移；不要在帧定时器、
  `VALUE_CHANGED` 或异步回调中重新写子级几何。
- **跨栈对照**：Web 中等价于 carousel `translateX` 期间又以 viewport 坐标修改子卡片的
  `left/transform`；Flutter/React Native 中等价于 `PageView` 动画中对子节点做全局坐标回写。
  原则一致：统一坐标系，等待父动画稳定后再做测量—校正闭环。

> 对应原始流水：`intake/P-0182_Tabview_横滑时_native_子项撕裂与首次进入_AppList_空白.md`。
