# P-0166 · LVGL 滚动列表三坑 + PC 仿真无头拖拽测试法

> 2026-10-21 · app-wifi-connect2 实测（EEZ Studio 0.29 + LVGL 9.4 + mingw SDL 仿真）
> 现象：EEZ 里做的"可滚动容器 + 自建行"列表，仿真器里**滑不动**。

## 坑 1：`lv_obj_hit_test()` 第一行就要求 CLICKABLE —— 自建行/容器全线不可命中

`lv_obj_pos.c:961`：

```c
bool lv_obj_hit_test(lv_obj_t * obj, const lv_point_t * point)
{
    if(!lv_obj_has_flag(obj, LV_OBJ_FLAG_CLICKABLE)) return false;   // ← 第一行
    ...
}
```

indev 的 press 流程：`lv_indev_search_obj()`（lv_indev.c:590）递归找**最深的命中对象**，
命中判定就是 `lv_obj_hit_test`。**没有 CLICKABLE 的对象对 indev 完全不存在**：

- EEZ 的 `LVGLContainerWidget`（`widgetFlags=""` 或仅 `SCROLL_CHAIN_VER`）→ 不可命中；
- 自建的 `lv_obj_create` 行如果 `remove_flag(CLICKABLE)` → 不可命中；
- 后果：`indev->pointer.act_obj` 恒为 NULL → `lv_indev_find_scroll_obj()`
  （lv_indev_scroll.c:267）从 act_obj 起跳的父链搜索**根本没起点** → 滚不动。
  此时 `SCROLL_CHAIN_VER` 加了也白加（坑 16 的老结论在这条面前不成立）。

**正解**：要么给行加 `CLICKABLE`（并准备处理点击），要么**用 LVGL 原生控件**
（lv_list/lv_table 的子项天生 CLICKABLE）。

## 坑 2：`lv_list_add_text` 建的不是 button —— 要用 `add_button`

`lv_list.c` 两个行类：

```c
const lv_obj_class_t lv_list_text_class = { .base_class = &lv_label_class, ... };
const lv_obj_class_t lv_list_button_class = { .base_class = &lv_button_class, ... };
```

- `lv_list_add_text()` → `lv_list_text`（**label 子类，无 CLICKABLE**）→ 同坑 1；
- `lv_list_add_button()` → `lv_list_button`（**button 子类，CLICKABLE**）→ 命中、
  滚动链（SCROLL_CHAIN）、将来的点选（CLICKED）全部天然成立。

**结论：EEZ List (LVGL) 控件 + C 侧 `lv_list_add_button(list, NULL, ssid)` 是
ESP32/LVGL 上"动态列表 + 可滚动"的可靠正解。** 行内自绘子对象时注意：
add_button 默认 `flex_flow=ROW`，要 `lv_obj_set_layout(btn, LV_LAYOUT_NONE)`
才能用绝对坐标（LVGL 9.4 没有 `LV_FLEX_FLOW_NONE`）。

## 坑 3：PC 仿真两个时间/状态假象（无头测试才会踩）

1. **`lv_tick_inc()` 被架空**：`lv_sdl_window_create()` 里
   `lv_tick_set_cb(SDL_GetTicks)` 把 LVGL 时间挂到**系统时钟**——手动
   `lv_tick_inc(40)` 对 `lv_timer_handler()` 的到期判定**完全无效**。
   SDL 事件由 `sdl_event_handler`（5ms timer）经 `SDL_PollEvent` 消费，
   时间不真实推进 → 事件不被消费 → indev 永远读不到新坐标。
   **推进时间只能 `SDL_Delay()`。**
2. **indev 残留 PRESSED**：注入的 `BUTTONUP` 若未被消费，`left_button_down`
   保持 true → 下次 DOWN 时 LVGL 认为"仍在按"→ **不重走 press 分支** →
   `act_obj` 不更新（表现为"有时能滚有时不能"的竞态）。
   无头测试必须：**先 UP 再 DOWN，且每步轮询等状态就绪**。

## 无头拖拽测试（main.c 钩子，可复用）

```c
static uint32_t sdl_window_id(void) { return 0; }  /* 0=不存在 → handler 走
    disp==NULL fallback（用第一个 read_cb==sdl_mouse_read 的 indev）*/
static void push_mouse(uint32_t type, int x, int y) { /* SDL_PushEvent，注意
    button 与 motion 的 x/y 在同一 union 偏移，写一处即可 */ }

static int drag_scroll_test(int px, int py, int dy, int frames)
{
    /* 1) 先 UP 并等 RELEASED  2) DOWN 并等 PRESSED + act_obj
     * 3) 每帧 push motion + SDL_PollEvent→lv_sdl_mouse_handler + SDL_Delay(8)
     * 4) 读 lv_obj_get_scroll_y(list) 判定 */
}
```

判据：`scroll_y` 从 0 变正 = 滚动链路通。实测 3/3 稳定。

## 机器检查

- 生成码 grep：`lv_list_create` 存在且 `list_box` 的 remove_flag **不含** CLICKABLE；
- C 侧 grep：`lv_list_add_button`（**不是** add_text）；
- 无头：`WIFI_SCROLLTEST=1` 三次全 PASS；
- 反例库：EEZ 容器控件做滚动列表 = 必然失败（本条目坑 1）。

## 关联

- P-0164 坑 16（坐标空间）仍有效，但"SCROLL_CHAIN_VER 能让容器滚起来"的推论
  在本条目坑 1 面前不成立——CLICKABLE 是更硬的前置条件；
- P-0152（List 是 wip，只能生成空容器）补充：**空容器 + C 侧 add_button 正是用法**。
