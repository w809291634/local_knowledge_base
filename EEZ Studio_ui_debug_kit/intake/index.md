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
| P-0021 | 2026-09-28 | EEZ tabview 吃默认亮色主题：整屏发白+tab文字豆腐块（终版修复=P-0025 原生路线，初版补丁已废） | EEZ,主题,tabview,字体,深色 | fixed |
| P-0022 | 2026-09-28 | tabName 不进字形收集：tab 标签中文字形缺失（设了字体仍豆腐） | json2eez,字体,字形收集,tabview,tabName | fixed |
| P-0023 | 2026-09-28 | DSL 容器创建后未挂载：歌词块整块消失 | build_ui,DSL,容器,挂载,children | fixed |
| P-0024 | 2026-09-28 | RAIL_TAB_IDS 用 build_ui 原始 id，被 prefix_ids 加前缀后永不命中，rail FA 图标全部烘焙缺失 | json2eez,字体,FA图标,prefix_ids,id前缀 | fixed |
| P-0025 | 2026-09-28 | tabview 主题/字体需运行时补丁？实测 EEZ 原生三件套即可：darkTheme 字段 + LV_FONT_CUSTOM_DECLARE + tabName 图标字符 | EEZ原生,主题,字体,tabview,fix_tabview废除 | fixed |
| P-0026 | 2026-09-28 | EEZ tab 栏原生定制：首子容器样式发射到 lv_tabview_get_tab_bar（rail 两行标签 / 设置左栏紧凑行） | EEZ原生,tabview,样式,tab栏,字体继承 | fixed |
| P-0027 | 2026-09-28 | 动作 object 写了重写前 id：EEZ identifiers 只收录被引用 widget，assign_ids 加页面前缀 → 16 个 Widget index not found | json2eez,动作,identifier,tabviewSetActiveTab,tabSize | fixed |
| P-0028 | 2026-09-28 | 设置左栏随页滑动：tab pager 导航必须外置固定 + CHECKED 两态/初始 checkedState/多动作链跟随（副本案废除） | EEZ原生,tabview,动作,objAddState,checkedState,样式状态,导航固定 | fixed |
