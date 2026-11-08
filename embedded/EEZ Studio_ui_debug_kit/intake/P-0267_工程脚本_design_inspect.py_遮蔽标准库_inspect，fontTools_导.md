# P-0267 · 工程脚本 design/inspect.py 遮蔽标准库 inspect，fontTools 导入即 AttributeError

- **工程**：redblue_p4
- **日期**：2026-11-08
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：命名冲突,fontTools,工具链
- **关联提示词**：PR-0614

## 现象（看到什么）

build_ui.py 里 import fontTools.ttLib 触发 dataclasses 调用 inspect.signature，报 AttributeError: module 'inspect' has no attribute 'signature'。

## 复现（怎么稳定重现）

把工程内脚本命名为 inspect.py 且放在 sys.path[0]（design/），任何依赖标准库 inspect 的第三方包都会拿到该脚本。

## 根因（真正的原因）

Python 模块查找顺序：脚本所在目录优先于标准库；工程内文件名不得与标准库模块同名。

## 修复（做了什么）

改名 design/inspect.py → design/inspect_pages.py，删除 __pycache__/inspect.*.pyc，同步 README / 框架确认.md / design_view.py 注释里的全部引用。

## 证据（数字 / 命令输出）

改名后在 design/ 目录下 import inspect 返回 Python311/Lib/inspect.py 且 signature 可用；fontTools 正常加载。

## 沉淀（新增断言 / 案例 / 文档）

固化断言：工程脚本命名避开标准库模块名；新增工具前扫一遍同名冲突。
