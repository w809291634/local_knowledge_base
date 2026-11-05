# P-0237 H5 批注模式实现：控件删/改 + 页面落点 + 导出 JSON

> **检索别名**：H5 批注 / 点控件删除 / 页面提示标签 / annotations.json /
> 返回 EEZ ④ / localStorage 批注。

- **时间**：2026-11-05
- **工程**：`w78-tabview-smart-home`（overview_pro.html）
- **依据**：NO_FLOW §2.1「H5 批注回路」、reference/14 §8

## 实现

- 顶栏新增 `批注：开/关`、`导出批注`；底部出现 `N 条批注 · 导出并返回 ④` 条。
- 批注开启后：
  - 点控件组 `g[data-rn]` → 面板显示 `页 · #n 名称`，可写修改说明、勾「标记删除」；
  - 点页面空白 → 按 SVG viewBox 坐标落 pin（带序号，点 pin 可再次编辑）；
  - 保存写 `localStorage["w78_annotations_v1"]`，页面重绘显示红框/红 pin。
- 删除预览：该控件组加 `opacity=.18`，并画红色虚线框 +「删」标；不改工程文件。
- 导出 `w78_annotations.json`（Blob 下载），结构见 NO_FLOW §2.1。
- `导出并返回 ④`：导出后提示把 JSON 交给 AI，改设计源后重新生成 H5/EEZ。

## 行为自证（Edge headless + CDP）

| 操作 | 结果 |
|---|---|
| 开启批注 → 点主控 #1 | 面板打开，标题 `主控 · #1 回家按钮` |
| 写说明并保存 | localStorage 出现 control/modify 记录，底部条 `on` |
| 点页面 (400,192) | 面板标题 `主控 · (400,192)`，保存后出现 pin 记录 |
| 点 #2 → 勾删除 → 保存 | 面板关闭，控件组 `opacity=".18"`，出现红色批注标记 |

## 约束

- 批注只存浏览器本地；换浏览器/清缓存会丢，需及时导出 JSON。
- 坐标用 viewBox（0–800/0–480），卡片缩放不影响；弹层态用各自展开帧坐标。
- 真正删除/修改由 AI 改 `pages.py` / `values.py` / `eez_gen.py` 后重生成。
