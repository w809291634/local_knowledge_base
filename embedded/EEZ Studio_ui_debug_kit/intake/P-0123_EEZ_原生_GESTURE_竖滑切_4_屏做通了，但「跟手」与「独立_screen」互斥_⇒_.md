# P-0123 · EEZ 原生 GESTURE 竖滑切 4 屏做通了，但「跟手」与「独立 screen」互斥 ⇒ 外层还原 LEFT tabview

- **工程**：lvgl_demo_ai/eez-test
- **日期**：2026-10-15
- **工具**：Qoder
- **状态**：open
- **标签**：EEZ,手势,tabview,screen结构,仿真输入
- **关联提示词**：（无）

## 现象（看到什么）

竖滑切屏在仿真里「要滑得很快」才生效，且观感和原 tabview 不一样（不跟手）；用户在 EEZ RUN 里还看到左侧栏/状态栏跟着屏一起滑（我们自己的仿真与真机不会）。

## 复现（怎么稳定重现）

仿真窗口内用鼠标慢速竖拖：不切屏。走路脚本 design/sim.py --walk=swipe：6 步×16px 十次只成一次手势；改成 2 步×64px 后稳定触发。

## 根因（真正的原因）

两条独立根因。① 判据不同：手势通道要 gesture_limit=50px 累计，且「这一拍 x/y 位移都 <3px 就把累计清零」（lv_indev.c:46,49,1731-1742）；而 tabview 翻页走容器滚动，scroll_limit=10px 起判、无速度门槛（lv_indev.c:32）。仿真的 SDL 鼠标还是 LV_INDEV_MODE_EVENT（lv_sdl_mouse.c:64），事件模式下 LVGL 又会 resume 读定时器（lv_indev.c:1363）⇒ 两次 motion 之间夹进零位移读，累计被反复清零，人手慢拖必然失败。② 结构互斥：切屏唯一入口是 replacePageHook() 里的 lv_scr_load_anim(screen, animType, speed, delay, false)（eez-flow.cpp:6732-6741），一次性定时动画、没有任何「停在手指位置」的公开接口（动画回调是 lv_obj.c 内部静态函数）；跟手要求两页同时渲染并随指定位移 ⇒ 只有同属一个可滚容器才可能。

## 修复（做了什么）

外层还原成「单屏 + tab bar 在 LEFT 的 tabview」：lv_tabview_set_tab_bar_position(LEFT/RIGHT) 会把内容容器设成 flex COLUMN + scroll_snap_y=CENTER（lv_tabview.c:196-203），竖向跟手+吸附就是原手感来源（HEAD 版 build_ui.py:2493）。随之退役：4 份状态栏、native rail_top_sync()、屏根 GESTURE flow、screen_swipe_spec()；恢复 switchTab+onTabChange（真值源 main_page_idx）；语音切屏回 lv_tabview_set_active。若日后仍要保留 4 屏，最多只能对齐灵敏度（indev->gesture_limit=10 / gesture_min_velocity=1，字段在 lv_indev_private.h:68,71，赋值不改库文件），跟手那半无解。

## 证据（数字 / 命令输出）

EEZ 侧能力实证：屏根 eventHandlers 写 {eventName:GESTURE, handlerType:flow} -> 生成 lv_obj_add_event_cb(..., LV_EVENT_ALL) + if (event == LV_EVENT_GESTURE)（screens.c:24-33/1073，四屏各一份）；表达式必须写 Event.getGestureDir(evt)（对象.方法形式，否则编译抛 Invalid call expression），evt 是 Compare 的 customInputs 输入引脚、由同一只 GESTURE 引脚以数据线连入；只连执行线报 「identifier 不是 input/local/global」。CLI 构建 No error and no warning detected。行为验证：Ai->Music->Notify->Settings 三连 up 全对、横滑与边界不切屏、设置内容列竖滑被 scroll_obj 接管（LVGL 自带让路，indev_gesture 首行 if(scroll_obj) return）。门禁 10.83% 不变、设备 build rc=0（bin 0x4ea5e0，39% free）。另：9.4 无 lv_obj_get_abs_x/y、无 lv_obj_class_get_name（都链接不过）=> 取真实渲染矩形用 lv_obj_get_coords；lv_indev_get_active_obj() 只在 indev 处理期间有值；shoot() 拍的是屏对象快照，看不见双屏推入的合成帧。

## 沉淀（新增断言 / 案例 / 文档）

skills.md 新增「EEZ 手势事件三件套 + 跟手/独立screen 互斥」通则；P-0122 追加更正段（4 屏方案的观感代价与作废原因）；工程侧 .workbuddy/memory/MEMORY.md 加「屏结构与输入手感」节，2026-10-06.md 补录第十一/十二轮（原文被删过）。
