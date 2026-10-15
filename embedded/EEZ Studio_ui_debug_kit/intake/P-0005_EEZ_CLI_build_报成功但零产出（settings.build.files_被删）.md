# P-0005 · EEZ CLI build 报成功但零产出（settings.build.files 被删）

- **工程**：（待补）
- **日期**：2026-09-23
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：eez,codegen
- **关联提示词**：PR-0024

## 现象（看到什么）

python design/eez_build.py 输出 'No error and no warning detected / Build successfully finished'，但 src/ui 下只有 eez-flow.cpp/.h，没有 screens.c/ui.c

## 复现（怎么稳定重现）

把 settings.build.files 删掉后跑 --build-project

## 根因（真正的原因）

settings.build.files 是 12 个产出文件（screens.c/ui.c/fonts.h...）的模板表，build 靠它决定产出哪些文件；我误以为 0.29 不再使用而 pop 掉了

## 修复（做了什么）

不移除该字段；缺失时从 design/build_files.json 恢复

## 证据（数字 / 命令输出）

删掉后日志少了 'Configuration: Default' 与 12 行 'File ... built'；恢复后 screens.c 正常生成

## 沉淀（新增断言 / 案例 / 文档）

（待补）
