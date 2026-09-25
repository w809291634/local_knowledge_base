# P-0006 · EEZ Studio CLI build 结束后进程不退出

- **工程**：（待补）
- **日期**：2026-09-23
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：eez,cli
- **关联提示词**：（无）

## 现象（看到什么）

subprocess.run 等 --build-project 返回，脚本挂到超时

## 复现（怎么稳定重现）

（待补）

## 根因（真正的原因）

build 完成后 home 窗口仍开着，只有收到 on-build-project-message(undefined) 才 quit

## 修复（做了什么）

改 Popen + 轮询日志出现 'Build successfully finished' → terminate + taskkill

## 证据（数字 / 命令输出）

构建本身 1.3s，进程 3 分钟不退出

## 沉淀（新增断言 / 案例 / 文档）

（待补）
