# P-0174 · EEZ 画布里是圆的，仿真器里是方的

- **工程**：watch-app-list-rxroller / watch-app-list-no-flow
- **日期**：2026-10-22
- **工具**：Qoder
- **状态**：fixed
- **标签**：EEZ,circularDisplay,displayBorderRadius,clip_corner,radius,编辑器装饰,胶囊,LV_RADIUS_CIRCLE
- **关联提示词**：PR-0289

## 现象（看到什么）

工程 settings 里 `circularDisplay=true`、`displayBorderRadius=232`，EEZ Studio 预览呈圆角；
同一工程在 PC_SIM 里四角笔直。用户据此怀疑 EEZ 建的控件没被用上。

## 复现（怎么稳定重现）

`grep circularDisplay watch-app-list-rxroller.eez-project` 有值 →
看 `src/ui/screens.c`：主屏是 `lv_obj_set_style_radius(obj, 0, …)`，且全文件搜不到 `clip_corner`。

## 根因（真正的原因）

在 EEZ Studio 的 `app.asar` 里 `circularDisplay` 的 8 处命中**全部在 React 预览渲染层**
（给预览 DOM 加 CSS `border-radius`），代码生成器 0 处 ⇒ 这个总开关纯属编辑器装饰，
一帧 LVGL 绘制都不知道它存在。
另外 `displayBorderRadius=232` 是从 368x448 的姊妹工程抄来的，两个工程数值一样，
都不是各自短边的一半。

★ 我自己也下错过一次结论：只 grep 驼峰 `clipCorner`（0 命中）就断言「EEZ 属性面出不了裁剪」。
实际属性名是 snake_case `clip_corner`，在 MISCELLANEOUS 样式组，
生成器 144 个 `lv_obj_set_style_*` setter 里有它。用户一句「你确定吗，查一下手册」把它推翻。

## 修复（做了什么）

圆角全部走 EEZ 控件级属性（`build_example.py` 里主屏 style
`radius=LV_RADIUS_CIRCLE(32767)` + `clip_corner=True`），生成产物自带两行 setter，
**native 一行不加**，仿真器照旧只调 `ui_init()/ui_tick()`。
加圆角后贴直角上的标题 / 状态行会被整个裁掉，
外壳落点按 `d = R - sqrt(R^2 - h^2)` 算（h=140 ⇒ d≈56）。

## 证据（数字 / 命令输出）

`src/ui/screens.c`：
```c
lv_obj_set_style_radius(obj, 32767, LV_PART_MAIN | LV_STATE_DEFAULT);
lv_obj_set_style_clip_corner(obj, true, LV_PART_MAIN | LV_STATE_DEFAULT);
```
标签落在 (65,56) / (65,428)；截图四角已裁圆、标题与状态行完整。
用 canvas 采样验证 410x502 上 `LV_RADIUS_CIRCLE` 出的是**胶囊**
（半径钳到 205，左右半圆 + 上下各 92px 直边），不是正圆。

## 沉淀（新增断言 / 案例 / 文档）

preflight 第 1 组新增 5 条：radius / clip_corner 由 EEZ 生成、native 侧不许偷偷补、
两个标签必须落在胶囊安全区内（几何判据，反向测试 `(60,56)` 会被拦）。
经验库新增 [[reference-eez-circulardisplay-is-editor-only]]。
