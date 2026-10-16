# P-0129 · 图标改动后 design/icons_out 看似未变——陈旧预览目录误导（真源=构建直出 watch/assets/）

- **工程**：Design Watch（watch UI 工程）
- **日期**：2026-10-16
- **工具**：Qoder
- **状态**：fixed
- **标签**：图标,icons_out,assets,误导,陈旧目录
- **关联提示词**：PR-0215

## 现象（看到什么）

改 icons.py 后 design/icons_out/*.png 时间戳与内容都不变 → 误判『图标没重新生成』（实际 watch/assets/*.png 已更新）。

## 复现（怎么稳定重现）

编辑 icons.py 任一 icon → 跑 design/build_watch_ui.py → 对比两个目录 mtime

## 根因（真正的原因）

build_watch_ui.py 显式调用 IC.build_all(watch/assets)；design/icons_out 只是 build_all 的默认参数遗留（无任何代码引用），是 11:54 一次手工运行留下的陈旧产物。

## 修复（做了什么）

以 watch/assets/ 为唯一真源；删除 design/icons_out（不可由当前代码再生，纯误导）。

## 证据（数字 / 命令输出）

assets mtime=构建时刻；grep icons_out 仅命中函数默认参数。

## 沉淀（新增断言 / 案例 / 文档）

（待补）
