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

## 重做（2026-11-06 14:00，用户令）

用户要求“重新建立 Tabview 0/1/2/3，使用 EEZ 拖动新建创建法”，并只改 `eez-widget-templates`：

- 在 EEZ UI 里删掉 `Tabview0/1/2/3` 四页，再 Add Page 重建；每页把 `Tabview` 从 Palette
  拖到画布，`Tab` 拖到 Widgets Structure 的 `Tabview` 行内（行下半区）落定，0/1/2/3 次；
- 期间误删了 `Lottie` 页（批量删页时行位置漂移），已用同样方式重新拖出并保存；
- 保存后重新 `extract_templates.py`：37 模板 + 4 变体**与重做前逐字节相同**，
  `validate_templates.py` PASS；EEZ 构建 39 页 0 错 0 警（14:03:53）；
- 工程 UUID 全换新，页面顺序变为变体在前、`Lottie` 在末，`screens.h` 的 `SCREEN_ID_*`
  随之重排（35~39）；这是重建的副作用，不影响模板语法；
- README 新增「硬规则：不得手搓，只能用 UI 拖拽保存语法」。

## 遗留

- 变体只入库到 3 个 Tab；4 个起可由“只差 `children` 数量”推断（已用 4-Tab 的真实工程佐证），
  若要把第 4 个也入库，仍须在 UI 拖一页再提取，不允许手拼。

## 关联

- P-0260（模板扩到 36 项）；P-0033（Tab 位置校验）；skills.md §11.20 四；PR-0572；CHANGELOG v0.9.160。
