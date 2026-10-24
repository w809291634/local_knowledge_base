# P-0187 · 无头 SDL 鼠标注入的三个时序坑：早期事件被吞、EVENT 模式不喂读、长按要按帧数算

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-23
- **工具**：Qoder
- **状态**：fixed
- **标签**：LVGL,输入注入,无头夹具,事件语义
- **关联提示词**：（无）

## 现象（看到什么）

注入点击完全无效（indev state 恒 0、point 恒 0,0）；或「效果总晚一次点击」——断言 FAIL 之后 [UI] 才打印 open。

## 复现（怎么稳定重现）

app-wifi-scan-conn-no-flow：WIFI_NAVTEST=1 跑 main.exe，对比不同等待帧数的表现。

## 根因（真正的原因）

① 启动后约 300 帧（≈600ms LVGL 时间）之前压进 SDL 队列的鼠标事件不会被消费；② lv_sdl_mouse 用 LV_INDEV_MODE_EVENT，只有新事件到达才 lv_indev_read，待派发的 CLICKED 会一直挂到下一次点击；③ 夹具 pump() 每帧只把 lv_tick 推 2ms，长按 400ms 需要 260 帧，按真实毫秒估会短一截。

## 修复（做了什么）

①注入前先跑够 300 帧再点；②抬起之后补一次同坐标 MOUSEMOTION 喂读（★只能在抬起后喂，按住时喂会被判成拖动、CLICKED 被吃掉）；③长按帧数按 lv_tick 增量换算，并加注释；④断言一律改成轮询等待（wait_until(pred, max_frames)），不写死帧数。

## 证据（数字 / 命令输出）

[NAV] 从 8/13 PASS 逐轮收敛到 17 PASS / 0 FAIL、rc=0；掐掉长按通路反向测试 rc=1；WIFI_SCROLLTEST 回归 scroll_y 0→169 仍 PASS。

## 沉淀（新增断言 / 案例 / 文档）

本工程 EEZ_WORKFLOW §5.6 + kit PLAYBOOK 输入注入条目
