# B19 表盘自环 Tabview（单滚动带循环 + 磁吸自愈 + 边缘过界手势）

> 场景：EEZ no-flow 腕表圆屏（466×466）。要求主屏（表盘）与若干快捷功能页 +
> 「+」页像手机 tabview 一样横滑切换，首尾相接成环；主屏右滑弹出左侧快捷窗。
> 本文把这轮反复被否（4 轮）+ 后续 4 个衍生 bug 的结论一次写清。

## 现象

1. 表盘与功能页之间横滑时"像切画面"、不是跟手滑动；表盘不算 tabview 成员。
2. 快滑（短促甩动）后页面停在两页之间，不磁吸；有时永久卡半页（截图：心率页整体右偏 ≈70px，指示点仍高亮原页）。
3. 「+」页（430×430 按钮铺满屏）滑不动，一碰就跳进选择页。
4. 表盘右滑不弹快捷窗；快捷窗只能瞬间显隐，没有渐入渐出，也没有"左滑收起"。

## 证据

- EEZ 生成物 `src/ui/screens.c` 给**每个子控件**都加了
  `lv_obj_remove_flag(obj, ...LV_OBJ_FLAG_SCROLL_CHAIN_HOR...)`（实测加号按钮那行）。
- LVGL `src/indev/lv_indev_scroll.c:327-333`：对象"不可滚且无 `SCROLL_CHAIN_HOR`"时**直接 break**，
  滚动目标搜索在控件处断链 → 拖动既不滚、松手还判成 CLICKED。
- LVGL `src/indev/lv_indev.c:1719`：`if(indev->pointer.scroll_obj) return;` —— 只要滚动器接管了，
  `LV_EVENT_GESTURE` 就**永不派发**。给 host / tab0 / screen 三处都绑手势回调，插桩一次都没进。
- 边界 elastic 实测：140px 拖动 → scroll_x 过界 46px（≈拖动量 1/3）；120px → 27px。
- 卡半页复现：`lv_async_call` 排队的归位被下一次拖动的 `SCROLL_BEGIN` 清空待办 → 目标丢失。
- 指示点不同步复现：`strip_scroll_only()` 提前把 `s_tab_slot` 设成目标槽，归位动画完成时
  `slot == s_tab_slot`，重建指示点的分支被跳过（逻辑槽位对、点没动）。

## 曾经的误判

1. **两个 LVGL screen + 瞬时换屏 + `LV_SCR_LOAD_ANIM_MOVE_LEFT`**
   → 用户："不是 tabview、是一个正方形在移动"。整屏动画会连底色方块一起搬，永远不像跟手滑动。
2. **表盘作为条带槽 0，但仍换屏**（独立 `quick_strip` 屏）
   → 用户："主界面不属于 tabview"。只要还在换屏，第一帧就没有跟手。
3. **归位走 `lv_async_call` 闸门**——以为异步更安全，实际快速连滑必丢待办 → 卡半页。
4. **归位时提前写 `s_tab_slot`**——以为无害，实际让"点重建"条件永不成立。
5. **以为边界右滑能收到手势**——按 LVGL 文档直觉，实际边界仍会被当成 elastic 候选（见真因）。

## 真因

- **跟手只能来自"同一个滚动器"**：表盘必须和功能页处在同一个滚动容器的相邻槽位里，
  才可能在同一条带上被手指拖走；任何换屏/整屏动画都做不到。
- **EEZ 剥链 + LVGL 边界仍把宿主当候选**：控件没有 `SCROLL_CHAIN_HOR` → 搜索断链（滑不动）；
  同时宿主在"边界方向"仍会被记为 elastic 候选 → `scroll_obj` 非空 → 手势被吞（右滑开不了窗）。
  两个症状同一个机制。
- **一次性闸门不可靠**：滚动事件是高频且可被新触摸打断的，任何"排队一次待办"的状态机都会丢事件。
  落点必须每次 END 重算（自愈）。

## 修法

### 1) 表盘常驻滚动容器（结构）

设计源把 `strip_host` 放成 **watchface 页的第一个控件**（EEZ 按声明顺序创建，宿主先出生）；
native 在 init 时把表盘其余子件**整体搬进槽 0 并永久留在那里**：

```c
/* strip_host_init：宿主=表盘屏子件，槽 0 装表盘内容 */
lv_obj_t *tab = strip_new_tab(host, 0);
while (i < lv_obj_get_child_count(objects.watchface)) {
    lv_obj_t *c = lv_obj_get_child(objects.watchface, i);
    if (c == host) { i++; continue; }          /* 宿主自己留在屏上 */
    lv_obj_set_parent(c, tab);
}
```

槽位约定：`0=表盘 → 1..N=勾选页 → 末槽=「+」页`。
功能页/「+」页只在**表盘屏激活时**搬进槽（否则从 applist 等入口打开会是空页）：

```c
go_screen(scr):  scr==watchface ? strip_home()   /* 滚回槽 0 + attach */
                                : strip_release(); /* 内容搬回各自 screen */
```

### 2) 滚动口径：关 momentum/snap，自己做定量磁吸（自愈）

```c
lv_obj_set_scroll_dir(host, LV_DIR_HOR);
lv_obj_remove_flag(host, LV_OBJ_FLAG_SCROLL_MOMENTUM);  /* 不要 LVGL 甩动（会跨多槽） */
/* 不用 LV_SCROLL_SNAP_*：其 momentum+snap 在快速甩动时落点不可控 */
```

`LV_EVENT_SCROLL_END` 里**每次都重算**，不设一次性闸门：

```c
x = lv_obj_get_scroll_x(host);
if (s_strip_drag_from >= 0) {                 /* 用户拖动：拉过页宽 1/8 就翻页，最多一页 */
    int start = s_strip_drag_from * W, turn = W / 8;
    if (x >= start + turn) slot = s_strip_drag_from + 1;
    else if (x <= start - turn) slot = s_strip_drag_from - 1;
    else slot = s_strip_drag_from;
} else slot = (x + W / 2) / W;                /* 程序化滚动：最近槽 */
if (slot < 0) slot = 0; if (slot >= n) slot = n - 1;

if (LV_ABS(x - slot * W) > 2) {               /* 没对齐：立刻起归位动画（只启动 anim，不重入） */
    s_tab_slot = slot; quick_tabs_show(slot); /* 点先跟上目标页 */
    strip_scroll_only(slot, LV_ANIM_ON);
    return;
}
```

四个状态位分工（缺一个就会出前面那些 bug）：

| 状态位 | 作用 |
|---|---|
| `s_strip_suppress_end` | 程序化**瞬时**滚动（ANIM_OFF）会同步发 SCROLL_END，必须屏蔽 |
| `s_strip_anim_program` | 下一次 `SCROLL_BEGIN` 是本层起的动画滚动 → `drag_from=-1`，绝不当"用户拖动" |
| `s_strip_drag_from` | 用户拖动起始槽；`-1` = 程序化。用于 ±1 页钳制与过界判定 |
| `s_strip_over_min/max` | 本次滑动的 elastic 过界极值（向左/向右），用完立即清零 |

`strip_scroll_only()` **只滚不改状态**；要同步状态/指示点必须显式写
（否则归位完成时 `slot == s_tab_slot`，指示点永不重建 —— 就是这个坑）。

### 3) 补齐滚动链与手势冒泡（控件上起手也能滑）

```c
/* EEZ 去掉了子控件的 SCROLL_CHAIN_HOR；条带子树必须补回来，否则断链 */
static void enable_scroll_chain_tree(lv_obj_t *node) {
    lv_obj_add_flag(node, LV_OBJ_FLAG_SCROLL_CHAIN_HOR);
    for (uint32_t i = 0; i < lv_obj_get_child_count(node); i++)
        enable_scroll_chain_tree(lv_obj_get_child(node, i));
}
/* 手势接收点=宿主：子树给 GESTURE_BUBBLE，宿主自己去掉 GESTURE_BUBBLE */
```

### 4) 边缘过界 = 唯一的"边界手势"信号

滚动与手势互斥，边界方向没有滚动量，只剩 elastic 过界量可用：

```c
/* 槽 0 继续右拉 → 打开左侧快捷窗 */
if (s_strip_drag_from == 0 && s_strip_over_min <= -(W / 16)) → quick_drawer_open();
/* 末槽继续左拉 → 循环切回 main */
if (s_strip_drag_from == n - 1 && s_strip_over_max >= (n - 1) * W + W / 16) → strip_loop_home();
```

**循环切 main 的做法（像普通换页，不是回卷）**：把槽 0 临时排到末槽右边，滚过去——
「+」页左滑出、表盘从右滑入，位移正好一页；到位那一帧画面与"槽 0 在原位、scroll=0"完全相同，
所以同帧瞬时归位看不出跳变：

```c
lv_obj_set_pos(s_strip_tabs[0], n * W, 0);      /* 临时排到末尾 */
lv_obj_update_layout(host);                     /* 让可滚范围算到 n*W */
s_strip_loop_pending = true;
strip_scroll_only(n, LV_ANIM_ON);
/* END 里 x >= n*W-2 → 槽 0 移回 0 + scroll 归零（同一帧，画面一致） */
```

注意：`SCROLL_BEGIN` 里**先判断"本层程序化滚动"并 return**，再判断"循环被用户拖动打断"，
否则循环动画会把自己收尾（实测停在起始槽）。

### 5) 快捷窗（屏子件，不进滚动带）

- 父对象是表盘 screen（不是宿主），所以不走滚动器：屏上绑 `LV_EVENT_GESTURE` 做"任意手势收起"。
- 渐入/渐出用 `LV_STYLE_OPA` 动画，收起完成回调里再置 `HIDDEN`；换屏前用"瞬时隐藏"，
  避免淡出拖住状态。
- 右缘小拉条 6×96、半透明白，提示可拖（几何走设计源宏）。
- 打开判定只认"槽 0 + 左向过界"，不依赖手势（见 §4）。

### 6) 大按钮的"点击 vs 滑动"分离

铺满屏的按钮会让每次滑动都被判点击。用按下→松手位移判据（`lv_event_get_param(e)` 拿 indev）：

```c
pressed: lv_indev_get_point(indev, &s_qa_press);
clicked: 位移 > 24px → return（是滑动，不当点击）
```

## 验证

- **物理量断言**（关键）：`watch_nav_strip_aligned()` = `scroll_x % 页宽 == 0`（±2px）。
  只断言"逻辑槽位"是不够的 —— 内容偏 70px 时逻辑槽位依然正确。
- **点的实际高亮**：`watch_nav_quick_tab_dot()` 记录 `quick_tabs_show()` 真正画出的下标，
  断言 `dot == slot`；槽 0 断言 `-1`（表盘不画点）。
- 真实输入链路：独立 POINTER indev 逐拍喂位移（每拍必须有位移，否则 LVGL 会因
  `gesture_min_velocity` 清零 `gesture_sum`），跑完断言落点 + 对齐。
- 用例覆盖：连续三次快滑 / 短滑 55px（过 50px 滚动阈值但不足翻页阈值）/
  末槽循环切页 / 「+」按钮上起手右滑 / 末槽左滑不误触 / 开窗+左滑收窗。
  结果 `131 PASS / 0 FAIL`。
- 中间帧截图取证：表盘与下一页同处一条滚动带；循环切页时「+」页左滑出、表盘右滑入。

## 通用化

| 问题 | 跨栈对照 |
|---|---|
| 换了容器就不跟手 | 任何 UI 栈（Android ViewPager / iOS UIScrollView / Flutter PageView / LVGL）都要求"被拖的内容与目标页在同一滚动容器内"；`replacePageHook` 式的换屏只能做跳转，不能做跟手 |
| 边界手势 | 先确认"该方向是否还有滚动余量"；没有余量时框架通常既不滚也不派发手势，必须读**弹性过界量**（或自己做按压位移采样） |
| 一次性待办闸门 | 触摸/滚动是高频可打断的事件流，落点必须**每次 END 重算**；异步转发一层只会丢事件 |
| 逻辑状态 vs 物理状态 | 测试断言要打"像素/偏移倍数/对齐"，只打标志位会掩盖"内容偏半页"这类问题 |
| 生成器剥旗标 | 代码生成器常按"属性面没勾"**显式去掉**默认 flag（如 SCROLL_CHAIN_HOR）；native 侧要么补回，要么别依赖框架的链式搜索 |

### 参数调节手册（本形态实测值）

| 参数 | 值 | 位置/说明 |
|---|---|---|
| 翻页磁吸阈值 | 页宽 1/8（≈58px） | 短促快滑也能落到相邻页 |
| 边缘过界阈值 | 页宽 1/16（≈29px） | elastic 约拖动量 1/3，140px 拖出 46px |
| 点击判定位移 | 24px | 大按钮上区分点击/滑动 |
| 快捷窗淡入 / 淡出 | 180ms / 160ms | `LV_STYLE_OPA` 0↔255 |
| 归位动画时长 | LVGL 默认 `anim_duration` | 无头回归需 pump ≥ 250ms 再断言 |
