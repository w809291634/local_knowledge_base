# P-0272 · 按钮子标签与按钮等大导致 align=CENTER 失效、文字不居中

- **工程**：多参数监护仪 UI（multipara_monitor_ui）
- **日期**：2026-11-08
- **工具**：Trae
- **状态**：fixed
- **标签**：EEZ,Button,对齐,生成器,门禁
- **关联提示词**：PR-0624 / PR-0625

## 现象（看到什么）

EEZ 按钮文字看起来贴顶/偏左；项目里子标签 widthUnit/heightUnit 被设成 px 且宽高等于按钮盒。

## 复现（怎么稳定重现）

生成器克隆 Button 模板后把子 Label 的 `widthUnit/heightUnit` 改成 `px`，且宽高写成与按钮盒相等；
打开工程看画布，文字贴顶/偏左，`align=CENTER` 无可移动空间。

## 根因（真正的原因）

子标签与按钮容器等大时，align=CENTER 没有可移动空间；垂直方向也因标签满高而贴顶。

## 修复（做了什么）

按钮子标签统一改 content 尺寸：居中用 align=CENTER/text_align=CENTER；左/右例外用
LEFT_MID/RIGHT_MID + 父级 pad_left/pad_right，不再把子标签设成与按钮盒等大的 px 盒。

## 证据（数字 / 命令输出）

多参数监护仪 76 按钮/15 隐藏覆盖，可见非居中 0；B1 平均相似度 96.55%→97.26%。

## 沉淀（新增断言 / 案例 / 文档）

- 生成器内置 `BTN_CHILD` 断言：按钮子标签必须 `widthUnit/heightUnit=content`，
  且几何不得等于按钮盒；违规直接 `SystemExit`，不写出工程。
- 独立门禁 `design/check_button_child.py <project>`：对任意 .eez-project 复检，
  违规退出码 1。
- 负向测试：把 `main_go50` 子标签改成 px + 与按钮同尺寸 → 门禁报 2 条违规并 FAIL。
- 文档：NO_FLOW §2.2 规则 ⑬、`reference/16` §3 规则 6、CHANGELOG v0.9.189。
