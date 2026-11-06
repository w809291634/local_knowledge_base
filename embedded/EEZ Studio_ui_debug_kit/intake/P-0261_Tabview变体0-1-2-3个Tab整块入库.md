# P-0261 Tabview 0/1/2/3 个 Tab 整块入库

> **检索别名**：Tabview 变体 / tabs0 tabs1 tabs2 tabs3 / 多 Tab 语法 /
> children 手拼 / 动态添加 Tab / variants 目录

- **时间**：2026-11-06
- **工程**：`eez-widget-templates`；镜像 kit `reference/eez_widget_syntax`
- **触发**：用户要求「Tabview 不需要 tab、有 1 个、2 个、3 个 tab 分别创建示例，
  防止动态添加导致语法不同」。

## 实测结论

在模板源工程用 EEZ UI 真实拖出 `Tabview0/1/2/3` 四页（Tabview 拖画布，Tab 拖
Widgets Structure 的 Tabview 行下半区），保存后逐字段比对：

- **只差 `children` 数量**；其余 34 个字段、`tabviewSize=32`、`selectedTab=0` 完全相同；
- 每个 `LVGLTabWidget` 的字段集与值也完全相同（180×68、`tabName:"Tab"`）；
- 所以“动态添加让语法不同”在 EEZ 侧不成立，但**整块入库**仍更稳，避免生成器手拼。

## 落地

- 新增 `templates/variants/LVGLTabviewWidget.tabs{0,1,2,3}.json`；
- `extract_templates.py`：`VARIANT_PAGES` + `extract_variants()`，变体页不参与
  “一页一控件类型”的重复检查；`manifest._variants` 记录页/文件/Tab 数；
  `defaults._meta.variants` 记数；
- `validate_templates.py`：`EXPECTED_PAGES=39`、`EXPECTED_VARIANTS=4`，逐变体核对
  ①等于变体页（字段/值/键序）②`children` 数等于变体号 ③除 `children` 外等于基础
  Tabview 模板 ④每个 Tab 归一后等于 Tab 模板 ⑤占位符唯一、无 `identifier`、无真实 UUID；
- kit 镜像同步：37 模板 + 4 变体 + defaults/manifest/README 逐字节一致。

## 自证

- `python validate_templates.py` → `[TPL_CHECK] PASS（37 个模板 + 4 个变体）`；
- 反向夹具三条全部 FAIL：改 `tabviewSize`、删一个 Tab、塞 `identifier`；
- EEZ CLI 构建 39 页工程：`No error and no warning detected`，
  `Build successfully finished at 2026/11/6 13:03:31`，`screens.c` 生成 39 个
  `create_screen_*`（含 tabview0~3）。

## 遗留

- 变体只覆盖到 3 个 Tab；要更多 Tab 需在源工程再拖一页并扩 `VARIANT_PAGES`，
  不允许凭推断生成。

## 关联

- P-0260（模板扩到 36 项）；P-0033（Tab 位置校验）；skills.md §11.20 四；PR-0572；CHANGELOG v0.9.160。
