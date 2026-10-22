# P-0175 · 真手滑到最上面不弹回，但 11 条无头断言全绿

- **工程**：watch-app-list-rxroller（移植 rxwind7/Rxroller 到 LVGL 9.4 / PC_SIM）
- **日期**：2026-10-22
- **工具**：Qoder
- **状态**：fixed
- **标签**：手势,HIDDEN,事件搜索,静默失效,indev,SDL注入,lv_sdl_mouse,夹具
- **关联提示词**：PR-0291

## 现象（看到什么）

用户上手反馈「我发先滑到最上面不返回了」；同一时刻 `WATCH_AUTOTEST` 的 11 条断言全部 PASS。

## 复现（怎么稳定重现）

`set WATCH_DRAGTEST=1 && main.exe`（合成 SDL 拖动：按下 → 10 次移动 → 抬起，全程走真 indev）。
修复前：中心停在 0，且日志里没有任何行级回调的痕迹。

## 根因（真正的原因）

手势回调只挂在**列表行**上。本工程的屏外回收把中心两侧 4 行以外的行置了 `HIDDEN`，
而 LVGL 的事件搜索会跳过隐藏对象 ⇒ 手指按在「隐藏行 / 空白」上时，按下目标是**滚轮根对象**，
行上的 PRESSED / PRESSING / RELEASED 一次都不触发，快滑与松手弹回全部**静默失效**。

无头断言全部直接调行级 API，**绕过了整条 indev 链路**，所以一条都测不到。

附带翻案：此前我判定「SDL 事件注入到不了 LVGL 的 indev」并删掉了脚手架，那是错的。
真因是上游 `lv_sdl_mouse.c:166-168` 的 `SDL_MOUSEBUTTONDOWN` 分支读的是
`event->motion.x / motion.y`（不是 `button.x / button.y`），
按下事件不填 motion 字段会让按下点落在 (0,0)，命不中任何控件。

## 修复（做了什么）

1. 同一组手势回调（PRESSED / PRESSING / RELEASED / PRESS_LOST）**也挂到滚轮根对象**；
   两条路径最终都归到同一个 `snap_edge_async`，行为一致。
2. 新增走真 indev 的 SDL 合成拖动夹具 `WATCH_DRAGTEST`（顶、底两个方向各一条断言），
   并让 `hal_init()` 在该模式下**保留**鼠标 indev（普通自证模式仍默认摘除）。

## 证据（数字 / 命令输出）

```
[ASSERT] 真拖动到顶：松手弹回顶部第 n 个    PASS  中心=1（第 2 个）
[ASSERT] 真拖动到底：松手弹回底部倒数第 n 个 PASS  中心=20（第 21 个）
```
标准 11 条无回归（合计 13/13）；取证图 `shots/shot_drag_top.png`、`shots/shot_drag_bottom.png`。

## 沉淀（新增断言 / 案例 / 文档）

preflight 第 6 组新增 2 条：手势回调必须同时挂行与根对象；必须存在走真 indev 的拖动夹具。
反向测试：摘掉根对象上的 RELEASED 注册即 FAIL。
经验库 [[feedback-ui-acceptance-is-behavior]] 补「直接调 API 的夹具会绕过整条输入链路」。
