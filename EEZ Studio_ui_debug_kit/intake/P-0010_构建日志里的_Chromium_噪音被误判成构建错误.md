# P-0010 · 构建日志里的 Chromium 噪音被误判成构建错误

- **工程**：（待补）
- **日期**：2026-09-23
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：eez,ci
- **关联提示词**：（无）

## 现象（看到什么）

eez_build.py 报「构建报错 9 条」，但项目实际是 'No error and no warning detected'

## 复现（怎么稳定重现）

（待补）

## 根因（真正的原因）

日志里混进 Chromium 自己的 GPU/磁盘缓存报错：'[27612:0923/185626.983:ERROR:net\disk_cache\...] Unable to move the cache'

## 修复（做了什么）

按前缀 ^\[pid:mmdd/hhmmss.mmm:(ERROR|WARNING|INFO): 过滤掉 Chromium 噪音再判定

## 证据（数字 / 命令输出）

过滤前 9 条 error，过滤后 0 条

## 沉淀（新增断言 / 案例 / 文档）

（待补）
