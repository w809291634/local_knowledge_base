# P-0029 · 程序切页 animated:true 时高亮/页面 off-by-one：陈旧 SCROLL_END 拉回旧 tab

- **工程**：eez-test（EEZ Studio 1.22.10 / LVGL 9.4.0 / 800×480）
- **日期**：2026-09-30
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：tabview,VALUE_CHANGED,高亮跟随,竞态,动画,冒烟断言
- **关联提示词**：PR-0056

## 现象（看到什么）

为「滑动切 tab 时左侧 rail 高亮跟随」新增 native 动作 `sync_rail_main`
（tabview VALUE_CHANGED → 按 `lv_tabview_get_tab_active` 重排 CHECKED）后，
sim 冒烟断言反常：

```
[smoke] after tile_bell: main_nav tab=2        ← 点击链正常
[smoke] rail after tiles: chat=0 music=0 bell=1 tune=0   ← 正常
（set_tv_layer 切到 tab1 后）
[smoke] rail@tab1: chat=0 music=0 bell=1 tune=0 (expect 0100)   ← 高亮停在旧页
（切到 tab2 后）
[smoke] rail@tab2: chat=0 music=1 bell=0 tune=0 (expect 0010)   ← 高亮又是上一次的
```

同时插桩打印 `[sync] main idx=2` 出现在「刚切到 1」之后、`idx=1` 出现在
「刚切到 2」之后——**sync 收到的 tab 序号永远慢一拍**。

## 复现（怎么稳定重现）

`python design/sim.py`（click_smoke_test 内 rail@tab1/rail@tab2 断言）。
EEZ 链 `tabviewSetActiveTab(animated:true)` + 快速连续切页（间隔 < 180ms 滚动动画）
即触发；偶发与否取决于上一次动画是否已落定。

## 根因（真正的原因）

LVGL 9.4 tabview 的 `cont_scroll_end_event_cb`（lv_tabview.c:344-380）在
SCROLL_END 用 **`lv_obj_get_scroll_end(cont)`（滚动动画目标位）** 反算 tab 序号 t，
若 t ≠ 当前 tab 则 `lv_tabview_set_active(tv, t)` 并发
`VALUE_CHANGED`。程序切页用 `animated:true` 时滚动动画 180ms 未落定，下一次
切页把 tab_cur 改掉后，**旧动画的 SCROLL_END** 仍按旧目标位算出旧 t →
`set_active(旧t)` 把页面拉回去 → 发 `VALUE_CHANGED(旧t)` → sync 把高亮排到旧页。
为什么以前没发现：此竞态一直存在，但旧链路里没人监听 VALUE_CHANGED，
G5 截图（400ms 时间片、逐屏等待）又掩盖了慢一拍；只有运行时断言能抓到。

## 修复（做了什么）

- `design/json2eez.py`：tabsw 动作链 `tabviewSetActiveTab` 的 `animated` 由硬编码
  `True` 改为 **`False`**（注释写明竞态机理）。程序切页即时完成 → SCROLL_END
  恒有 t==tab_cur → 不再产生陈旧事件；**手势滑动的跟手动画不受影响**（那是
  LVGL 滚动自身行为，松手 SCROLL_END 拿新鲜 t）。
- `design/build_ui.py`（上一轮）+ `src/native/native_actions.cpp`：VALUE_CHANGED →
  `action_sync_rail_main/cats`（onTabChange DSL 字段，json2eez 编译为
  handlerType:"action" 直调）。

## 证据（数字 / 命令输出）

修复前（build3）：

```
[smoke] rail@tab1: chat=0 music=0 bell=1 tune=0 (expect 0100)
[smoke] rail@tab2: chat=0 music=1 bell=0 tune=0 (expect 0010)
```

修复后（build4，`python design/sim.py`）：

```
[smoke] rail@tab1: chat=0 music=1 bell=0 tune=0 (expect 0100) ✓
[smoke] rail@tab2: chat=0 music=0 bell=1 tune=0 (expect 0010) ✓
[smoke] wifi pop after row: pop=0 bg=0 (expect 0/0)           ✓
[smoke] wifi pop after close: pop=1 (expect 1)                ✓
[smoke] wifi pop after bg: pop=1 (expect 1)                   ✓
```

EEZ build 0 error；native C（sync 两动作 + screens.h 引用）随 sim 编译链接 0 error。

## 沉淀（新增断言 / 案例 / 文档）

- sim.py `click_smoke_test` 新增 rail 四项 CHECKED 恰一为真断言 +
  wifi 浮层 has_flag(HIDDEN) 翻转断言（运行时断言，长期保留）。
- skills.md **§11.15**（滑动高亮跟随 / animated:false 铁律 / 下拉浮层 / 自查方法论）；
  CHANGELOG v0.8.8。
- 可被哪条断言提前拦住：任何给 tabview 加 VALUE_CHANGED 监听或改切页动画参数的
  改动，必须跑 rail 恰一为真断言（已固化进 sim.py）。
