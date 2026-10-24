# P-0198 · lv_obj_remove_style_all() 会连 local 尺寸一起清掉，遮罩变 0×0、点击全穿透

- **工程**：app-wifi-scan-conn-no-flow
- **日期**：2026-10-24
- **工具**：Qoder
- **状态**：fixed
- **标签**：LVGL,样式,尺寸,遮罩,无头断言
- **关联提示词**：PR-0368

## 现象（看到什么）

按用户口径加了"连接中全屏遮罩 + 转圈，期间不可操作"。遮罩确实显示出来了（截图里能看到半透明底和圈），
但无头断言 `转圈期间点带锁行不生效（输入被锁住）` FAIL——遮罩盖着的时候点列表，半页照样弹出来。

## 复现（怎么稳定重现）

`wifi_busy.cpp:ensure_root()` 里把顺序退回
`lv_obj_set_size(...)` → `lv_obj_remove_style_all(...)`，重编重跑 `WIFI_NAVTEST=1`：
`[NAV] RESULT: PASS 36 / FAIL 8`、rc=1（第一条 FAIL 就是那条锁操作断言，其余是连锁反应）。

## 根因（真正的原因）

LVGL 9 里 **width/height 是 local style 属性**（`lv_obj_set_size` 写进对象自己的样式存储），
而 `lv_obj_remove_style_all()` 会把所有样式（含 local）一并清掉。
所以"先定尺寸再清样式"等于把尺寸也清了，对象塌成 0×0：
渲染上看不出问题（子对象 spinner/label 仍然画出来，父对象 0 尺寸不影响子对象绘制），
但 `lv_obj_hit_test()` 判定该点不在对象范围内 → 事件穿透到下面的列表行。
**"看得见"和"挡得住"是两件事**，只截图验证会漏掉这一整类缺陷。

## 修复（做了什么）

`src/native/widgets/wifi_busy/wifi_busy.cpp`：把 `lv_obj_remove_style_all()` 提到
`lv_obj_set_size/set_pos` **之前**，并在代码里写明这条顺序约束。

## 证据（数字 / 命令输出）

修复后 `[NAV] RESULT: PASS 44 / FAIL 0`、rc=0；`preflight --skip-cli --with-sim` 全绿；
六屏既有截图 SHA1 与改动前逐字节一致。反向测试（退回旧顺序）rc=1 且点名该断言。

## 沉淀（新增断言 / 案例 / 文档）

**任何"遮罩/模态要挡住下层"的需求，必须有一条"遮罩期间点下层不生效"的行为断言**，
不能只截一张"遮罩看起来在"的图。落档：工程 `EEZ_WORKFLOW.md` §5.10。
