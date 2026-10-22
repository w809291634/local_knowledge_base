# P-0176 · 字体覆盖门禁比的是声明值，字体被换掉时它会因为错的理由通过

- **工程**：watch-app-list-rxroller
- **日期**：2026-10-22
- **工具**：Qoder
- **状态**：fixed
- **标签**：字体,门禁,假判据,Opts,lv_font_conv,EEZ-GUI烘字体,声明vs产物
- **关联提示词**：PR-0292

## 现象（看到什么）

用户用 EEZ Studio GUI 重新生成工程后，`src/ui/fonts/ui_font_cn14.c` 被 EEZ 自己烘的版本覆盖
（`--range 32-126,20013,…` 取代了 `gen_font.py` 的 `--symbols 中二亮…` 写法），
而 preflight 第 3 组依旧报 `OK native 上屏用字 54 个，全部在字体子集内`。

## 复现（怎么稳定重现）

把 `ui_font_cn14.c` 头部 `Opts:` 里的 `--range` 删掉 3 个码点，再跑 preflight：
旧断言仍然 OK —— 假门禁实锤。

## 根因（真正的原因）

该断言拿 native 实际用字去比 `build_example.FONT_CHARS`，那是**声明值**，
不是这份 `.c` 真正覆盖的码点集。EEZ GUI 构建会自己烘字体（CLI 不烘，见 P-0140），
两边是两份配方 ⇒ 字体被整个换掉时门禁毫无感知。

## 修复（做了什么）

新增 `font_covered_codepoints()`：解析 `ui_font_cn14.c` 头部 lv_font_conv 原样回显的 `Opts:` 行
（`--range` 与 `--symbols`），得到这份字体的**真实**覆盖集，
再分别与 native 上屏用字、与 `FONT_CHARS` 声明做双向差集比对。

## 证据（数字 / 命令输出）

正向：
```
OK   实际字体文件覆盖 native 用字 54 个（解析自 ui_font_cn14.c 的 Opts）
OK   字体实际覆盖码点数(155) == 声明字符集数(155)
```
反向（删 3 个码点）：
```
FAIL 实际字体文件覆盖 native 用字 54 个 …  -> 字体缺字 动天日
FAIL 字体实际覆盖码点数(152) == 声明字符集数(155) -> 只被声明有、字体里没有：动天日
```
本轮实测两份配方覆盖完全相同（155 码点，无缺字），所以这次重新生成在功能上是安全的。

## 沉淀（新增断言 / 案例 / 文档）

preflight 第 3 组从 1 条扩到 4 条；README 生成链注明「EEZ GUI 也会烘字体，
两份配方要靠产物反查而不是靠声明」。
