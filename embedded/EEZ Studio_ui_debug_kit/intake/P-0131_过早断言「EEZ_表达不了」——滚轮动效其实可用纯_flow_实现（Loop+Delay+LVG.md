# P-0131 · 过早断言「EEZ 表达不了」——滚轮动效其实可用纯 flow 实现（Loop+Delay+LVGL 动作组整数表达式链）

- **工程**：watch (Design Watch)
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：eez-flow,loop,delay,objStyleSetProperty,objGetDisplayY,转换样式,整数表达式
- **关联提示词**：PR-0217,PR-0218

## 现象（看到什么）

AppList 滚轮动效（滑动时中心行放大）被判定为『flow 读不到滚动位置』→ 落成 native C 模块（watch/src/native/applist_wheel.c）；用户两次质疑『不是要求从 eez 里面来改吗』

## 复现（怎么稳定重现）

在 EEZ 里给行做『按与屏幕中心距离连续缩放』：需要每帧读每行屏幕 y。此前只查了可绑定事件清单（12 种，无 SCROLL）就下结论

## 根因（真正的原因）

排查面太窄：只看了『事件』，没看 ①A43 LVGL 动作组里有 objGetDisplayY（读屏幕坐标）与 objStyleSetProperty（写任意样式属性，property=LV_STYLE_* 数字码 110/111=transform_scale_x/y）；②A42 Loop（start/next→seqout/done，To 给大数=常驻循环）+ Delay（毫秒重排队，不忙等，tick() 跨帧切片）；③运行时 eez-flow.cpp 已内建 executeLVGLApiComponent 顺序执行动作列表。合起来 = 常驻轮询链无需任何滚动事件

## 修复（做了什么）

生成器 design/build_watch_ui.py 新增 wheel_flow_applist()：AppList 页加 Start+Loop(wlc 0..2147483646)+Delay(30ms)+LVGLAction(110 个动作：每行 objGetDisplayY→wly，再 4×objStyleSetProperty 双轴双态)；native 调用从仿真 main 移除（模块留档）

## 证据（数字 / 命令输出）

① eeZ_build 零错误零警告（此前 110 条 Widget index not found → 改用规范化标识符 row_sport_mode 后清零）；② 仿真静止态 5 行缩放实测 192/212/243/219/195 vs 公式 192/213/244/220/196（±1）；③ scroll_y=880 后 57/48/72/65/54 vs 理论 57.0/48.4/72.6/65.5/53.7；④ EEZ Run（F5）实测：进入 AppList 即见滚轮、拖动后放大行随滚动迁移；⑤ dragtest 点击导航 ✓ 滚动 Δ427/453 ✓

## 沉淀（新增断言 / 案例 / 文档）

kit CHANGELOG v0.9.6（A8 links_event_outputs 事件源过滤）；G2 check_nav 改只计 CLICKED；reference/07 补『动作 object 参数须写规范化标识符』；报告 §18
