# 问题登记索引

> 每遇到一个新问题，追加一行 + 一个 `P-####_*.md`。写入方式见 `../INTAKE.md`。

| 编号 | 日期 | 标题 | 标签 | 状态 |
|---|---|---|---|---|
| P-0001 | 2026-09-23 | 缺 Pillow 时脚本裸崩（与文档承诺不符） | 工具缺陷,Pillow,降级 | fixed |
| P-0002 | 2026-09-23 | tab_bar 模板默认值导致 A5 误报/静默失效 | 工具缺陷,配置陷阱,可移植性 | fixed |
| P-0003 | 2026-09-23 | json2eez 备份文件未被忽略，累积 308MB 污染 git | 工件卫生,git,备份 | fixed |
| P-0004 | 2026-09-23 | 界面开关是装饰容器，点了没反应 | 交互,开关,控件类型 | fixed |
| P-0005 | 2026-09-23 | EEZ CLI build 报成功但零产出（settings.build.files 被删） | eez,codegen | fixed |
| P-0006 | 2026-09-23 | EEZ Studio CLI build 结束后进程不退出 | eez,cli | fixed |
| P-0007 | 2026-09-23 | 保留嵌套容器导致控件二次偏移（文字全部跑到卡片外） | lvgl,d2 | fixed |
| P-0008 | 2026-09-23 | LVGL 快照 ARGB8888 内存序是 B,G,R,A | lvgl,snapshot | fixed |
| P-0009 | 2026-09-23 | EEZ 打开工程报 invalid color（0x2a3044 忘了加引号） | eez,color,gate | fixed |
| P-0010 | 2026-09-23 | 构建日志里的 Chromium 噪音被误判成构建错误 | eez,ci | fixed |
| P-0011 | 2026-09-23 | A6 断言假阳性：被 #if 守护的字体引用被当成「引用但未开启」 | audit,false-positive | fixed |
| P-0012 | 2026-09-23 | A7 不适用时打印 OK，把「没检查」伪装成「通过」 | audit,false-positive | fixed |
| P-0013 | 2026-09-23 | gcc 在 PATH 缺失时静默失败（rc=1 且零输出） | toolchain,path | fixed |
