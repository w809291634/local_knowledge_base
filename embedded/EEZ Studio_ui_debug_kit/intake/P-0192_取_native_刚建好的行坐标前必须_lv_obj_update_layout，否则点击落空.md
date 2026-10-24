# P-0192 · 取 native 刚建好的行坐标前必须 lv_obj_update_layout，否则点击落空

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：无头验证,布局,坐标,偶发失败
- **关联提示词**：PR-0361

## 现象（看到什么）

[NAV] 断言约 1/5~1/8 概率在「点第一条带锁行」处假失败，且效果总在下一次点击才出现（日志里 sheet open 打在断言之后）。

## 复现（怎么稳定重现）

去掉 row_center() 里的 lv_obj_update_layout(list) 后连跑 8 次即可复现。

## 根因（真正的原因）

行由 wifi_list 刚 clean+add 出来，布局未刷新时 lv_obj_get_coords 返回旧值，算出的中心落在标题区——那一笔点在无处理器的对象上，整笔丢失；排查时被误当成「EVENT 模式不喂读」或「首笔注入被吞」，先后用重推 DOWN、补点、强制 lv_indev_read 三种绕法，通过率反而从 3/3 掉到 2/6。

## 修复（做了什么）

row_center() 先 lv_obj_update_layout(objects.list_box)，再取坐标，并自证「行的 y 区间必须与列表可视区相交」，不相交直接返回 0 让用例报错而不是假失败。

## 证据（数字 / 命令输出）

修复后连跑 10 次 [NAV] 17 PASS/0 FAIL、补点触发次数 0；此前同代码去掉该行时 8 次里 2 次全绿。

## 沉淀（新增断言 / 案例 / 文档）

本工程 EEZ_WORKFLOW §5.4 夹具坑清单（第 4 条）
