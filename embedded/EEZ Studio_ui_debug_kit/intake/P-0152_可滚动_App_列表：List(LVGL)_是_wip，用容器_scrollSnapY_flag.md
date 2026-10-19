# P-0152 · 可滚动 App 列表：List(LVGL) 是 wip，用容器 scrollSnapY/flagScrollDirection 自建（watch applist 同款）

- **工程**：EEz_stidio_examples/app-list-scroll
- **日期**：2026-10-19
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：applist,滚动列表,scrollSnapY,flagScrollDirection,SNAPPABLE,CHECKABLE,PRESSED,List wip,渐变,bg_grad_dir
- **关联提示词**：PR-0258

## 现象（看到什么）

想要 watch applist 同款的可滚动列表示例；官方手册 List(LVGL) EXAMPLES [EMPTY]（wip），Container 亦无示例；eez-open/studio 仓库无 examples 目录（已核实）

## 复现（怎么稳定重现）

EEZ v3 工程：Container 作滚动容器（flags 留全滚动族，去 GESTURE_BUBBLE/PRESS_LOCK/SCROLL_WITH_ARROW）+ flagScrollDirection=ver + scrollSnapY=center + 6 行 Container（CHECKABLE+SNAPPABLE+渐变图标块）

## 根因（真正的原因）

①List (LVGL) 官方 wip，只有创建代码无属性 → 列表用普通容器自建（watch applist 即此形态：list_scroll 容器 set_scroll_dir(VER)+set_scroll_snap_y(CENTER)+行绝对坐标）；②吸附滚动下行是吸附点，必须保留 SNAPPABLE（P-0150）；③EEZ 样式枚举属性须传名字符串（bg_grad_dir 传 1 会发射 LV_GRAD_DIR_1 编译错，须传 "VER"）；④CLI 构建偶发首跑不落 eez-flow.h/cpp（g_currentScreen undefined），重跑一次即现

## 修复（做了什么）

按 watch list_scroll 形态生成：容器 flags=全滚动族去三漏、flagScrollDirection=ver、scrollSnapY=center、flagScrollbarMode=AUTO；行=CHECKABLE+SNAPPABLE+PRESSED 样式态高亮（零 flow）；产出 app-list-scroll 示例，CLI 0 错 0 警 + PC_SIM 7/7 链接 0 错

## 证据（数字 / 命令输出）

screens.c 产物：set_scroll_dir(LV_DIR_VER)/set_scroll_snap_y(LV_SCROLL_SNAP_CENTER)/add_flag(CHECKABLE)/PRESSED 样式各就位；grad_dir 修正前后编译错误与通过对比；eez-flow 缺失重跑即现

## 沉淀（新增断言 / 案例 / 文档）

app-list-scroll/README.md、根 README 索引第 9 行、workspace memory 2026-10-19

## ★ 坑 4 更正（2026-10-19 晚，slider-arc-bar 工程复现并定位）

"CLI 首跑常不落 eez-flow.h/cpp，重跑一次即现"是**误诊**。真因：自写的 cli_build.py
轮询到 **"No error and no warning detected"**（该行出现在生成文件列表**之前**）就
terminate 进程，恰好掐死其后的 **"EEZ Flow engine built"**（eez-flow.h/cpp）发射阶段——
重跑"碰巧"成功只是因为第二次进程没被提前杀。
**修法**：脚本成功判据必须用 **"Build successfully finished"**（EEZ Flow engine 行
在其之前出现）。本库所有 cli_build.py 副本（w1/tabview/app-list-scroll/slider-arc-bar）
已统一修正；对外判断 eez-flow 缺失时直接看 `ls src/ui` 有无 eez-flow.h/cpp。
