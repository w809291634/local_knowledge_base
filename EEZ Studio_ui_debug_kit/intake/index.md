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
| P-0014 | 2026-09-24 | 圆形按钮里的图标没落在父对象正中（居中是算出来的，不是声明的） | 居中,布局,dsl,像素偏差 | fixed |
| P-0015 | 2026-09-24 | 纯图标胶囊偏中心 3px（布局助手给最后一项也加了间隔） | 布局,gap,间隔语义,pill | fixed |
| P-0016 | 2026-09-24 | 噪音过滤正则与真实时间戳不符（P-0010 的修复未真正生效，复发） | eez,ci,regex,false-positive,复发 | fixed |
| P-0017 | 2026-09-27 | compare.py 在本机无 PIL 导致 G5 无法运行（受管 venv 未装 Pillow） | G5,依赖,PIL,venv | fixed |
| P-0018 | 2026-09-27 | tree_check 未配墨迹偏移时把下边界系统性低估，越界长期漏判 | tree_check,越界,假通过,墨迹,精度 | fixed |
| P-0019 | 2026-09-27 | 运行时对象框与设计框不一致，按严格坐标查表会把正确命中误判成未命中 | LVGL,坐标,命中,查表,框偏差 | fixed |
