# P-0172 · 上游 .orig 与仓库文件 SHA256 对不上，看着像被人改过

- **工程**：watch-app-list-rxroller
- **日期**：2026-10-22
- **工具**：Qoder
- **状态**：fixed
- **标签**：移植,整仓对账,CRLF,行尾,SHA256,假失配,release,tag
- **关联提示词**：PR-0286

## 现象（看到什么）

`sha256sum` 上游克隆里的 `Rxroller.c` 得 `166b648076f6…`（41339 B），
入库 `Rxroller.c.orig` 是 `3a364084ef49…`（40135 B），差 1204 字节。
另外用户问上游有没有发布 release，需要给可核对的答案而不是印象。

## 复现（怎么稳定重现）

`git clone` 上游 → `sha256sum Rxroller.c` → 与工程内 `.orig` 直接比，必然不等。

## 根因（真正的原因）

入库时把行尾归一化成了 LF，上游仓库是 CRLF；差的 1204 字节正好等于行数。
也就是说「哈希不等」在这里完全不构成立论据。

release 问题：GitHub Releases 必须先有 tag，而 `git ls-remote --tags` 返回空 ⇒ 逻辑上就已排除；
再用 `releases.atom` / `tags.atom` 各 0 条 entry 二次确认（避开 API 限流）。

## 修复（做了什么）

1. 上游**整仓**（6 文件 + `.git` 全历史）克隆进工程内 `upstream_Rxroller/`，
   不入库（根 `.gitignore` 排除，嵌套仓库）。
2. 新增 `design/compare_upstream.py`：先做**整仓对账**（上游每个文件必须有归属，
   冒出没记账的文件就 FAIL），再**归一化行尾后逐字节**比 `.orig` vs 上游，最后复核补丁账单。
3. PORTLOG 新增 §2.1（整仓对照库）/ §2.2（行尾事实），§5 加为第四条复核命令。

## 证据（数字 / 命令输出）

```
上游仓库共 6 个文件（git ls-tree -r HEAD）
      未取用 README.md / CMakeLists.txt / .gitignore
OK    Rxroller.c   上游 3a364084ef49  vs  入库 Rxroller.c.orig  逐字节一致（归一化行尾后）
OK    Rxroller.h / LICENSE 同上
OK    账单 .orig -> Rxroller.c = 14 hunks / +49 / -16
```
`git ls-remote --tags` 空；`releases.atom` `<entry>`=0；`tags.atom` `<entry>`=0。
对照库不参与编译：`build.ninja` 里 `upstream_Rxroller` 出现 0 次。

## 沉淀（新增断言 / 案例 / 文档）

经验库 [[feedback-port-open-source-keep-portlog]] 补「CRLF 会让哈希假失配 + 整仓对账」；
[[feedback-web-research-timebox]] 印证「GitHub 元数据走 ls-remote/.atom 不吃配额」。
