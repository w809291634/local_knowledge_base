# P-0150 · EEZ Tabview 页拖不动：Tab 页被裁 SNAPPABLE，吸附滚动零吸附点

- **工程**：EEz_stidio_examples/tabview-swipe-switch
- **日期**：2026-10-19
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：tabview,SNAPPABLE,吸附滚动,widgetFlags,remove_flag,SCROLL_CHAIN,PC_SIM,滑动切页
- **关联提示词**：PR-0254

## 现象（看到什么）

PC_SIM 里按住页面拖动无法切页：事件探针实测 PRESSING 连发而 0 次 SCROLL；同环境的纯 LVGL tabview 对照版拖动正常。gesture 版同环境却表现为'要快速滑动才触发 GESTURE'（同一根源的另一种表相）

## 复现（怎么稳定重现）

EEZ Tabview(tabviewSize=0 隐藏 tab 栏) + 2 个 Tab 直挂（手册配置1），Tab 页 flags 照 watch 工程裁掉 SCROLLABLE/SCROLL_ELASTIC/SCROLL_MOMENTUM/SCROLL_WITH_ARROW/SNAPPABLE；PC_SIM 鼠标按住拖动

## 根因（真正的原因）

①主因：内容区被 lv_tabview 置为 SNAP_CENTER 吸附滚动，内核 find_scroll_obj 在 snap 模式下不算普通溢出，改调 has_more_snap_points()（lv_indev_scroll.c:353-360）只数带 LV_OBJ_FLAG_SNAPPABLE 的子对象当吸附点；Tab 页被裁 SNAPPABLE → 零吸附点 → 内容区被判该方向不可滚 → 拖动全废。EEZ widgetFlags 是'最终态白名单'而非增量，按类默认差集发射 lv_obj_remove_flag，漏写即被反向移除。②次因：不可滚动对象若无 SCROLL_CHAIN_*，滚动链在该对象 break（lv_indev_scroll.c:327-334），label 不留链时从 label 起拖的链路断；本例 label 不可点击、落点是 PAGE，故非主因但属同类陷阱

## 修复（做了什么）

Tabview 与 Tab 页都只裁 SCROLLABLE（eez-test 实测可滑同款）：flags=CLICKABLE|CLICK_FOCUSABLE|GESTURE_BUBBLE|PRESS_LOCK|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER|SCROLL_ELASTIC|SCROLL_MOMENTUM|SCROLL_WITH_ARROW|SNAPPABLE，产物仅一条 lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE)；label 加 GESTURE_BUBBLE|SCROLL_CHAIN_HOR|SCROLL_CHAIN_VER

## 证据（数字 / 命令输出）

修复前 SendInput 注入真实拖动：97 PRESSING/0 SCROLL（P-0150/PR-0254）；结构探针（修复后）content scroll_right=480、snap_x=SNAP_CENTER、页 SNAPPABLE 保留、产物 flags 终检=仅 remove SCROLLABLE；对照实验：同 build 同 main 循环的纯 LVGL tabview（页带默认 flags）拖动正常滚。另注意：离屏页 lv_obj_get_width()=0 是惰性布局假象，须先 lv_obj_update_layout(tv) 再读，勿误诊'第二页 0x0'

## 沉淀（新增断言 / 案例 / 文档）

tabview-swipe-switch/README.md 坑1-2-3-8 与 build_example.py 注释、根 README 索引行、workspace memory 2026-10-19
