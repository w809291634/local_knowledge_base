# VSCode / Trae 问题两则（Python 折叠 / 登录缓慢）

> 适用：VSCode、Trae（基于 VSCode 的国产 IDE）
> 来源：《问题解决和汇总 v1.2》"vscode软件问题汇总"章节

## 1. Python 代码无法折叠

折叠功能（folding）已打开但仍无法折叠 Python 代码：**更新 Python 插件/解释器版本后恢复**——旧版插件与语言服务不兼容导致折叠区域计算失败。

## 2. VSCode / Trae 登录一直很慢、无法登录

登录流量走了代理导致超时：**关闭所有代理**——
- 系统设置里的代理服务器；
- VPN 客户端；
- 环境变量里的代理（`HTTP_PROXY` / `HTTPS_PROXY` 等，终端 `env | grep -i proxy` 检查）。

全部关掉后再点登录。
