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
| P-0029 | 2026-09-30 | 程序切页 animated:true 时高亮/页面 off-by-one：陈旧 SCROLL_END 按旧动画目标位拉回旧 tab | tabview,VALUE_CHANGED,高亮跟随,竞态,动画,冒烟断言 | fixed |
| P-0030 | 2026-09-30 | 滑动同步 native user action 退役改纯 EEZ flow（asar 序列化四要点 + 选型铁律） | EEZ-flow,tabview,VALUE_CHANGED,user-action,asar取证,Compare,localVariables,铁律 | fixed |
| P-0031 | 2026-09-30 | 状态机 UI 用 hiddenExpr 声明式显隐：表达式禁嵌套括号（互斥控件叠字）+ pill 宽度必须 x=0 锚点（文字骑 pill）+ 行容器与行内按钮禁绑同一动作（冒泡双命令） | hiddenExpr,hiddenFlag,声明式显隐,状态机,互斥显隐,pill宽度,事件冒泡,表达式嵌套 | fixed |
| P-0032 | 2026-09-30 | 设置页内容压左栏：撤子页时把 pane 起点 RAIL_W+206 改成 RAIL_W（外置左栏让位铁律）；对照门禁只看 11 屏平均，单屏错位不报警 → 出图必分区放大目检 | 布局,外置左栏,place起点,RAIL_W,tab pager,对照门禁,均值盲区,目检 | fixed |
| P-0033 | 2026-09-30 | Screen 直下挂 tab：EEZ GUI 报 Invalid position of Tab widget（headless build 不查结构）；钉态页零引用死代码已删，再要干净背景页须包进隐藏 tabview | EEZ结构校验,tab,tabview,headless,GUI校验,钉态页,死代码,结构不变量 | fixed |
| P-0034 | 2026-09-30 | 滑动点亮组空缺：无子页的入口行（pop）不归组，滑回通用页左栏全灭；pop 行点击不动高亮；swipe 断言把 bug 写成规格（expect 0/000） | 高亮跟随,rail_cats,onTabChange,点亮组,tab=None,pop行,断言写成规格 | fixed |
| P-0035 | 2026-09-30 | 字体 Opts 行路径形式：EEZ 用工程里 filePath 原文拼 opts_string（无相对化），工程必须存相对路径；内核读文件基准改工程目录 + ensure_engine 的 bake.js 缓存缺陷修复 | 字体烘焙,Opts,filePath,相对路径,KERNEL_HASH,bake.js缓存,黄金样本 | fixed |
| P-0036 | 2026-09-30 | EEZ flow 孤岛动作组件：空 switchTab 链被无条件生成（pop 行 P-0034 后为空）；连带修复 17 处 tabviewSetActiveTab animated:true 违反 LV_ANIM_OFF 铁律 | EEZ-flow,孤岛组件,connectionLines,switchTab,animated,LV_ANIM_OFF,铁律 | fixed |
| P-0037 | 2026-10-01 | 动作画布按导航分区分列重排（json2eez _bucket/_slot）；tab pager 编辑态结论：多页叠放无法全显，属性面板 Active tab 秒切；审计基准修正（widget 名字段=identifier） | EEZ-flow,画布布局,分区,tabview,Active-tab,编辑态,identifier,审计基准 | fixed |
| P-0038 | 2026-10-01 | 动作组件按页面分组（ComponentGroup）：json2eez 自动生成 {description, components[]}（boundingRect computed 免存坐标）；白名单含 CompareActionComponent（首版漏） | EEZ-flow,ComponentGroup,组件分组,分区布局,白名单,asar取证 | fixed |
| P-0039 | 2026-10-01 | 动作画布组间距/堆叠：EEZ 组件渲染高度随 actions 数增高（行距须动态）；列距收紧 420；分区改名字制（数字桶+重映射曾致组名错位） | EEZ-flow,画布布局,渲染高度,堆叠,组间距,名字制分区,分区键 | fixed |
| P-0040 | 2026-10-01 | 变量死活审计：三态合并判据（JSON 结构化绑定/表达式裸引用/native 读写），唯一死变量 battery_pct 已删（33→32）；GUI 里 hiddenExpr/native 引用不可见易误判 | 变量审计,hiddenExpr,Label绑定,native读写,死变量,battery_pct | fixed |
| P-0041 | 2026-10-01 | native 变量死活审计：四点闭环判据（UI表达式/EEZ消费/io写入/io读回），删 wifi_rssi/wifi_icon/wifi_bars_visible/battery_charging（io写UI不读）；brightness 保留（滑块接口暂留）；六文件同步删除 | native变量,APP_IN,io写入,死变量,三向审计,变量删除,双向绑定 | fixed |
| P-0042 | 2026-10-01 | 画布组件重叠：渲染高度公式低估（EEZ 组件渲染高 ≈ 40+n*30，行距须按渲染高+间距）+ 律动链区起点相撞（新链区起点=前一链区右缘之外，单行排布） | 画布布局,渲染高度,行距,堆叠,律动链,tabsync,防重叠 | fixed |
| P-0043 | 2026-10-01 | EEZ 动画能力边界与纯 flow 律动模式：PLAY_ANIMATION 一次性无循环；Loop+Delay+SET_PROPERTY 循环链（Run 预览真实执行）；三坑=Loop 输入 start/next、`/` `%` 返回 double、停止检查须帧级 | EEZ-flow,动画,Loop,Delay,SET_PROPERTY,预览,Run模式,double陷阱 | fixed |
 | P-0044 | 2026-10-01 | 设置 tab 页数/顺序变更的三处同步点：CATS 表、onTabChange 分组、sim nav_btn_for+VIEWS —— 漏一处就内容串位；断言只查序号抓不住，必须目检子页截图 | tabview,页序,nav_btn_for,VIEWS,串位,目检 | fixed |
 | P-0045 | 2026-10-01 | 设备侧专属文件（io_esp.cpp）是 PC 构建盲区：TODO 注释漏 */ 吞掉下游函数签名，潜伏到真机 idf.py build 才爆且报错点远离病灶；改后必须配平检查/跑一次真机构建 | io_esp,注释,潜伏,Werror=comment,真机构建,盲区 | fixed |
 | P-0046 | 2026-10-01 | LVGL 9.4 CHECKABLE 翻转发生在 LV_EVENT_RELEASED（lv_obj.c:829-835）而非 CLICKED：CHECKED 绑变量后命令走 VALUE_CHANGED，冒烟脚本模拟点击必须发 RELEASED（CLICKED 只过用户 handler 不翻状态） | LVGL9,CHECKABLE,RELEASED,VALUE_CHANGED,冒烟脚本,checkedState,真状态 | fixed |
 | P-0047 | 2026-10-01 | EEZ LVGL 滑杆/开关真状态绑定语法（asar 实证）：slider value 表达式=双向（tick 推送+VALUE_CHANGED 回写 assign*Property）；checkedState 表达式挂 Base.js（任意控件可绑 CHECKED）；slider KNOB 负 pad 放大；v9 slider flags 无 SCROLL_CHAIN_HOR（拖动不换页） | slider,checkedState,双向绑定,KNOB,asar取证,flags,真状态 | fixed |
 | P-0048 | 2026-10-01 | 复查三错：hiddenExpr 是「隐藏条件」不是显示条件（写反=默认全灭，暗色卡 compare 均值盲区不报警）；var 绑定 label 右锚定不能走 label_right（tw(None)=0 → 内容溢出屏幕外，固定宽+textAlign RIGHT 解）；settings_publish 类批量发布会覆盖纯 UI 状态（notif_filter 被刷回 0） | hiddenExpr,语义反向,均值盲区,label右锚定,textAlign,批量发布,状态覆盖 | fixed |
 | P-0049 | 2026-10-02 | knob 几何实测（修正 P-0047 的错误说法）：slider/switch 的 KNOB 直径 = **控件高度**，pad 只**向外扩**（正 pad 撑出轨道）→ 细轨道必须用 MAIN 的 transform_height 负值收缩（lv_bar draw_indic 的 lv_area_increase），switch 内嵌圆点用**负 pad**(-3)；h=5 的滑杆圆点只有 5px≈不可见 | slider,switch,KNOB,transform_height,pad方向,几何,目检 | fixed |
 | P-0050 | 2026-10-02 | 设备侧文件（io_esp.cpp）重复定义只在真机构建暴露（PC 仿真不编译它）：整块「音乐/电量假数据」被复制两份 → redefinition。自检手法：用工程 build/compile_commands.json 取该文件的编译命令，去掉 -c/-o 加 **-fsyntax-only** 用真机工具链在 PC 上过一遍（补上 P-0045 盲区的可执行检查） | io_esp,重复定义,真机构建,compile_commands,-fsyntax-only,自检 | fixed |
 | P-0051 | 2026-10-02 | 运行时字符串字形必须补**完整字符集**：clock_date 只种了「星期」漏「一二三四五六」→ 状态栏/待机页显示 "10月2日 星期 · 早上好"（星期名后半段空白）。新增 `design/_glyph_lint.py`：io 侧中文字面量 vs DSL 已种字形差集检查（负向测试已验证能抓到） | 字形,glyphs_seed,运行时字符串,星期,漏字,lint | fixed |
 | P-0052 | 2026-10-02 | ★ 修正 P-0050 的自检手段：`-fsyntax-only` **不跑优化器**，抓不到 `-Wstringop-truncation` 这类 tree-optimization 警告（真机连吃两次：重复定义 → strncpy）。自检必须是**真实编译（保留 -O2 的 -c）**；脚本 design/_device_syntax_check.py（负向测试已验证）。另：GCC14 把 `strncpy(dst,src,sizeof-1)` 判为可能截断（IDF -Werror 升级），改用 snprintf 版 safe_copy | 自检,fsyntax-only局限,stringop-truncation,strncpy,真机工具链,-Werror | fixed |
 | P-0053 | 2026-10-02 | ★ 修正 PR-0095 的 keyboard 写法：LVGLKeyboardWidget 的 `textarea` 属性值是 **identifier 名**（asar: enumItems 用 identifier、check() 用 getIdentifierByName），不是 objID。写 objID 的双重后果：①GUI 报 `"Textarea": "<objID>" not found`；②**CLI 静默略过绑定**，screens.c 无 lv_keyboard_set_textarea → 键盘与输入框实际没连上（真机才暴露）。已加 sim.py [kbd] 运行期绑定断言 | keyboard,textarea,identifier,objID,静默失败,真机,GUI报错 | fixed |
 | P-0054 | 2026-10-02 | 真机扫描到 AP 却一行不显示：`s_scan_in_progress` 扫完/失败路径都没清 → io_sample_inputs 的 `state = s_scan_in_progress ? 1 : snap.state` 恒为 1 → UI 列表 hiddenExpr="wifi_state == 1" 永久隐藏，只剩"正在搜索网络…"。修：do{}while(0)+break 单一出口清标志 + 15s 看门狗强制回列表态（C++ 里 goto 跨变量初始化会编译失败，别用 goto） | wifi扫描,状态标志,退出路径,hiddenExpr,看门狗,goto陷阱,真机 | fixed |
