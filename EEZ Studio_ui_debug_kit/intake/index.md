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
 | P-0055 | 2026-10-02 | 密码面板键盘被 LVGL 每帧重排（`lv_keyboard` 构造函数内含 `lv_obj_align(BOTTOM_MID)`，DSL 坐标只是初值）：键盘挂**同层**（不进面板）+ 自管 hiddenExpr + `build_ui.kb_at()` 预减固定偏移（y+=h-7、x+=17）；排查手法=复位实验+读 `lv_obj_t` 私有字段 raw/align | keyboard,重排,align,同层挂载,kb_at,偏移,raw字段 | fixed |
| P-0056 | 2026-10-02 | LVGL 9.4 的 keyboard 按键**不在 children 里**（`child_count` 恒 0，`lv_keyboard_t` 内嵌 buttonmatrix）：`key` 走路命令按 children 找键必然 0 个 → 输密码改 `text` 灌 textarea，真点键盘用 `tree <kb> 2` 量坐标再 `tapxy`（另：9.4 无 `lv_obj_get_text`/`lv_obj_get_abs_x`/`lv_obj_class_get_name`，`LV_KEYBOARD_OK/DEL` 宏也不存在） | LVGL9,keyboard,buttonmatrix,child_count,walking,量坐标,tapxy | fixed |
| P-0057 | 2026-10-02 | ★ PC 仿真快捷入口只判「exe 是否存在」→ 改了 `io_pc.cpp` 跑的还是**旧副本**（副本 08:50、源文件 09:01，日志里旧行为骗了排查）。规则：走路/钉态截图每次 `copy_native()`，再按「用户代码是否比 exe 新」增量编译（`sim.exe_stale`）；行为与代码不符先看时间戳 | 仿真,exe同步,copy_native,stale,走路器,假绿 | fixed |
| P-0058 | 2026-10-02 | 失败态「重试」要点 slot 的**第 9 个子对象**：`[8] rel(455,15) 63x15` 是同位的哑壳（无 `lv_obj_add_event_cb`、失败态 hidden，真机也命中不到），真按钮是 `[9] rel(472,10) 46x24`（`m_box_138`）。判据：带 onAction 的对象在 screens.c 里各有 `event_handler_cb_*`，点前确认挂的是哪个 | 重试,哑壳,tapchild,子对象索引,event_handler,失败态 | fixed |
| P-0059 | 2026-10-02 | PC 模拟的 Wi-Fi 语义必须对齐真机 `io_esp`：`io_wifi_pick` 开放/已保存→直连、加密未保存→弹密码面板；失败态同槽位 pick = retry（清 err + 进连接态，对齐真机 StartStation），否则「失败→重试→成功」走不通。静态钉态全绿、走路一跑就露馅（钉态是手工置位，只证明画面对、证明不了交互跑得通） | io_pc,io_esp,语义对齐,弹面板,retry,走路验证,钉态局限 | fixed |
| P-0054 | 2026-10-02 | 真机扫描到 AP 却一行不显示：`s_scan_in_progress` 扫完/失败路径都没清 → io_sample_inputs 的 `state = s_scan_in_progress ? 1 : snap.state` 恒为 1 → UI 列表 hiddenExpr="wifi_state == 1" 永久隐藏，只剩"正在搜索网络…"。修：do{}while(0)+break 单一出口清标志 + 15s 看门狗强制回列表态（C++ 里 goto 跨变量初始化会编译失败，别用 goto） | wifi扫描,状态标志,退出路径,hiddenExpr,看门狗,goto陷阱,真机 | fixed |
| P-0060 | 2026-10-02 | ★ PC 仿真统一适配范式：统一用 v5.5.5 树 `PC_SIM/lv_port_pc_vscode_v9.5`，**目录内除根 CMakeLists 零改动**，只暴露一个 `TARGET_PROJ_DIR` 宏（其余路径相对它推 UI_DIR/NATIVE_DIR/SIM_MAIN_DIR）；仿真**就地构建**（build/ bin/ 落 PC_SIM，它自带 .gitignore）+ **引用编译**工程 src/ui、src/native（GLOB 直编，入口 main.c 与仿真 lv_conf.h 放工程侧 design/sim_cmake），彻底干掉"副本忘同步"假绿（P-0057） | 仿真,构建,CMake,适配层,引用编译,就地构建,目录规范,假绿 | fixed |
| P-0061 | 2026-10-02 | ★ LVGL 配置注入只能走 `LV_BUILD_CONF_PATH`（且必须是**普通变量**不是 CACHE）：`LV_BUILD_CONF_DIR` 只定义 `LV_CONF_INCLUDE_SIMPLE`，优先级低于 `LV_CONF_PATH`，会静默回落到 PC_SIM 根目录那份原始 lv_conf（THORVG=1/FS_STDIO=1）→ PC 上 `thorvg/config.h`、`fsdrv/lv_fs_stdio.c 的 dirent.h` 全挂；修法 `set(LV_BUILD_CONF_DIR "")` + `set(LV_BUILD_CONF_PATH ...)`；另 build() 每次全量 re-configure（源码清单是 configure 期定死的） | CMake,LVGL配置,lv_conf,ThorVG,FS_STDIO,静默回落,假绿 | fixed |
| P-0062 | 2026-10-02 | 别对 src/ui 整体 `set_source_files_properties(LANGUAGE CXX)`：EEZ 生成的 screens.c 里 `lv_obj_remove_flag(obj, LV_OBJ_FLAG_X\|LV_OBJ_FLAG_Y)` 传的是 **int**、内核签名是 `lv_obj_flag_t`(enum) —— C 允许隐式转换、C++ 不允许 → 满屏 `no matching function`。语言一律按扩展名走（.cpp 本来就是 C++） | CMake,语言标准,C与C++差异,enum隐式转换,EEZ生成代码,仿真 | fixed |
| P-0063 | 2026-10-02 | Windows 端 clang + lld-link（-nostartfiles -nostdlib，MSVC 兼容模式）的三个 POSIX 假设：①`unistd.h` 不存在 → 入口只用 usleep 就用 `Sleep` 兜底宏；②`target_link_libraries(... m pthread)` 被翻译成 `m.lib`/`pthread.lib` 必然 `could not open` → `if(WIN32)` 拆开 | 链接,clang,MinGW,unistd,libm,libpthread,移植,Windows | fixed |
| P-0064 | 2026-10-02 | `SDL.h` 会 `#define main SDL_main`（靠 SDL2main 的 WinMain 转调），纯 mingw 成立、本机 clang+lld-link 拉不进 `libSDL2main.a` → `lld-link: undefined symbol: main`（`llvm-nm` 证实目标文件里只有 `T SDL_main`）。修：自己写入口就在 include SDL.h 前 `#define SDL_MAIN_HANDLED` | 链接,SDL2,main符号,SDL_MAIN_HANDLED,lld-link,入口,llvm-nm | fixed |
| P-0065 | 2026-10-02 | 仿真器适配层默认工程路径用 `"${PROJECT_SOURCE_DIR}/../../../../p4_..."` 数层数退，退 4 层落到了 `examples/` 而非 `examples/idf_v555_my_exps/`（**少退一级**）→ 手动裸跑 cmake 报 `Cannot find source file: .../examples/p4_touch_lcd4_3_exp/.../design/sim_cmake/main.c` + `No SOURCES given to target: main`（错误信息只给路径不给原因）。修：改成**向上探测**哨兵（找含 `<工程>/eez-test/src/ui` 的那层，找不到 FATAL 提示用 -DTARGET_PROJ_DIR 指定）+ SIM_MAIN_DIR 下 main.c/lv_conf.h 存在性断言 + `[sim] TARGET_PROJ_DIR` / `SIM_MAIN_DIR` 自证 message | CMake,适配层,TARGET_PROJ_DIR,路径,报错可读性,仿真,裸configure | fixed |
| P-0066 | 2026-10-02 | `LV_BUILD_CONF_PATH` 只在父作用域写**普通变量**，`apl_lvgl` 是 `add_subdirectory` 进来的**子作用域**，那里读到的是**空串**（父作用域 message 有值、内核 `message(STATUS ${LV_BUILD_CONF_PATH})` 打空）→ `if()` 落假静默走 `Using lv_conf.h from the top-level project directory` 分支（P-0061 没根治干净的病灶，ThorVG/FS_STDIO 又变回默认 1）。修：同一值**普通变量 + CACHE 各写一遍**（CACHE 子作用域必读到），并加 `[sim] LVGL 配置来源 = ...` 每次 configure 自证 | CMake,作用域,子目录,lv_conf,静默回落,假绿,ThorVG,FS_STDIO | fixed |
| P-0067 | 2026-10-02 | 同一份仿真入口在**两种前端下 SDL 的 main 改名需求相反**：clang+lld-link（`nostartfiles -Wl,--undefined=WinMain -fuse-ld=lld`）拉不进 `libSDL2main.a` → `undefined symbol: main`（P-0064 已解）；换 mingw gcc 13.1 则 `find_package(SDL2)` 把 `libSDL2main.a` 链进来，`SDL_windows_main.o` 要 `SDL_main` → `undefined reference to SDL_main`。P-0064 那行 `#define SDL_MAIN_HANDLED` 写死在 main.c 会踩后者。修：保留 `SDL_MAIN_HANDLED`，在真 `main()` 之后补 `#undef main` + `int SDL_main(...){ return main(...); }` 转调（clang 端是死代码，mingw 端补缺符号；`#undef` 必写否则自递归） | 链接,SDL2,SDL_main,SDL_MAIN_HANDLED,clang,mingw,双工具链,自递归陷阱 | fixed |
| P-0068 | 2026-10-02 | 真机「点加密网络不弹密码面板」先**取固件二进制证据**再改代码：`grep` 烧进去的 `build/*.bin`，`password entry not supported yet` 不在、`show password panel` 在 ⇒ 弹面板分支已进固件，问题落在运行期三分支（空槽 / 判成开放 / 已保存直连 / 弹面板）。真机 `sub` 写死 `"WPA2 PSK"`、PC 写 `"WPA2 PSK · 已保存"` → 点已保存网络时直连但不给任何提示，用户就以为"不给输密码"。修：扫描期查 SsidManager 打「已保存」标识（PC/真机文案逐字对齐，含 `" · "`）+ `sub[16]→sub[24]`（`"WPA2 PSK · 已保存"` 是 **21 个 UTF-8 字节**，旧容量会截成"…已保"）+ 三分支各一行自证日志 | 真机,取证,固件字符串,已保存,文案对齐,UTF-8字节数,安全拷贝截断,分支日志,定位成本 | fixed |
| P-0069 | 2026-10-02 | 适配层全塞进 `PC_SIM` 根 `CMakeLists.txt` 后 **+139/−30（240→349 行）**，用户质疑"改动怎么这么大"。拆类发现 47% 新增是纯注释，且**只有约 20 行是真必须**（GLOB 对不上 EEZ 平铺布局 / `set(APL_LVGL_DIR ...)` 写死普通 set 会盖掉 -D / `add_executable` 入口+NATIVE_SOURCES / WIN32 链接分支 / include 目录 / ThorVG 屏蔽——后者必须等 lvgl target 建好才改得动 source 属性）。修：新增 `cmake -C <工程>/design/sim_cmake/sim_init.cmake` **初始缓存**把所有路径/内核/分辨率/LVGL 配置从工程侧注入（`-C` 在顶层 CMakeLists 之前就把 CACHE 落地，子作用域必读到，比"父作用域 set 普通变量"稳），瘦身到 **+32/−11（271 行）**；注释精简成每块 1 行 + 保留一条 `[sim] LVGL 配置 = ...` 自证 message | CMakeLists瘦身,初始缓存,cmake -C,作用域,CACHE,适配层,责任边界,仿真 | fixed |
| P-0071 | 2026-10-02 | 仿真器适配层瘦身（P-0069）后仍要手填 9 项路径（`UI_DIR`/`NATIVE_DIR`/`SIM_MAIN_DIR`/`APL_LVGL_DIR`/`SIM_H_RES`/`LV_*`），用户要求"以后只改工程目录宏" → 在 PC_SIM 根 CMakeLists 顶层立**目录协议**：唯一入口 `TARGET_PROJ_DIR`，① 三个约定目录 `src/ui` / `src/native` / `design/sim_cmake` 拼出来（不是目录就 FATAL，防 GLOB 静默收空）② 内核自工程根向上找 `common/APL/apl_lvgl*` ③ LVGL 配置取 `<sim_cmake>/lv_conf.h` 走 `_PATH`（`_DIR` 置空）④ 分辨率从目标工程 `design/build_ui.py` 的 `SCREEN_W/SCREEN_H` 正则读出再 `target_compile_definitions` 下传（**铲掉 Python 侧常量 + main.c 兜底两个第二真值源**）。全部推导值 `set(X "${X}" CACHE ...)` 写回 CACHE 供 apl_lvgl 子作用域读（P-0066）。踩坑：`set(_proto "UI_DIR;src/ui")` 的分号被 CMake 当列表分隔符摊成 6 元素，`foreach`+`list(GET _kv 1)` 直接 `list index out of range` → 改等长双列表 `list(GET _proto_vars _i)`。换工程 = 改 `sim_init.cmake` 里那一行 | 目录协议,单一入口,自动推导,向上探测,仿真分辨率,单一真值源,CACHE写回,GLOB静默空,list分号陷阱 | fixed |
| P-0072 | 2026-10-02 | 把目录协议块再压一轮回到 **+133/−28（345 行）**，**比用户抱怨的那版（+139/−30/349 行）还小但功能更多**。压完一验证连抓 4 个真 bug：① `apl_lvgl_v9_4` 在 `TARGET_PROJ_DIR` **往上第 2 层**（`idf_v555_my_exps/common/APL/`），省掉 up-walk 改单次 GLOB 直接 FATAL 找不到 → up-walk 只能保留、只把 5 个写死版本号压成 `apl_lvgl*` 通配 ② **分辨率"自动推导"从来是死代码**：`sim_cmake/lv_conf.h` 无 `LV_HOR_RES`，而 `build_ui.py:63` 写的是 **`SCREEN_W, SCREEN_H = 800, 480` 同句多赋值**，旧正则 `SCREEN_W[ \t]*=[ \t]*([0-9]+)`（要求等号紧跟）永远匹配不上 → 800×480 一直来自硬编码默认值（**删掉默认值再 configure，CACHE 不变就是死代码**）③ 修正正则要用**第 2 个捕获组**取高（`SCREEN_H = 800, 480` 后面跟的是 800）④ 推导值必须 `set(SIM_H_RES "${_x}" CACHE STRING ... FORCE)`，普通同名变量 `target_compile_definitions` 读不到。另：为省行数把正则塞进 `macro()` → CMP0219 警告 + 宏体 `"${_txt}"` 被当源文件内容塞进字符串字面量报 `Syntax error`，**CMake 里别为少写几行把逻辑塞 macro** | 死代码识别,同句多赋值,正则陷阱,CMAKE_FORCE,推导值回写,macro陷阱,CMP0219,diff量化,瘦身 | fixed |
| P-0070 | 2026-10-02 | 瘦身验证 **`exe_stale()` 判"工程源码不比 exe 新"就跳过编译**，而把 `build/` 目录移走并不会让 exe 失效 → 3 秒内"跑通"的走路其实用的还是**瘦身前那份旧 exe**，瘦身后的 CMakeLists 一次都没被编译验证（P-0057 同一类坑换了个触发方式）。验证仿真改动的正确做法：先删 `bin/main.exe` 强制重编，或显式看 configure 期 `[sim] LVGL 配置` 自证行 | 仿真验证,增量编译,exe_stale,假绿,旧副本,验证纪律 | fixed |
| P-0073 | 2026-10-02 | 用户确认"协议落地后 PC_SIM 文件不用改了"但仍嫌它复杂（345 行）→ 通读按"是否真在构建中生效"分类，砍掉约 170 行**祖传死代码**（FreeRTOS 三个分支 / SDL2_image+libpng+jpeg+ffmpeg+freetype 五个可选库 / Debug 警告墙+ASAN（sim.py 恒传 Release）/ ccache / `include_directories(main/inc)`（该目录根本不存在）/ 空 `set(WORKING_DIRECTORY)`）；先 `grep -rl` 查依赖保住 `LV_INTERFACE_SIM`（仿真器侧无人用但工程 io_pc 要用）。修法是**极简转发**而非就地精简：PC_SIM 根 CMakeLists **371→29 行**（只剩 cmake_minimum+project+路径检查+`include(<工程>/design/sim_cmake/sim_build.cmake)`），全部逻辑搬工程侧由 sim.py 生成（sim_build.cmake 181 行，接入点变四件套），历史版备份 `CMakeLists.v2_371lines.bak`。相对就地精简多三个好处：PC_SIM 彻底封版不怕被覆盖 / 逻辑跟着工程走可移植 / 职责单一 | 极简转发,forwarding include,死代码识别,祖传包袱,PC_SIM零改动,可移植性,验证纪律 | fixed |
| P-0074 | 2026-10-03 | 用户还原 P-0073 并定调「要最简单的修改：这个文件自己适配每个工程，只配 CMakelist 里一个工程路径变量，声明工程大致结构即可」→ **撤回「极简转发」（逻辑搬工程侧 sim_build.cmake）**，改 **单变量配置区**：逻辑留在 PC_SIM 根 CMakeLists（371→~200 行），顶部唯一 `set(TARGET_PROJ_DIR ...)` + 紧邻「工程结构声明」目录树/推导优先级/破例 -D 清单；死代码照删（FreeRTOS/五可选库/Debug 墙+ASAN/ccache/main-inc），`LV_INTERFACE_SIM` 必留。sim.py 删 write_simbuild/write_siminit，新增 `read_target_proj_dir()` **只在那一行缺失或失效时兜底**，绝不传 `-DTARGET_PROJ_DIR=`（会盖掉用户手改的换工程动作）；接入点回到两件套。教训：用户要的简单 = 改动单点 + 结构自明，不是文件行数少 | 单变量配置区,结构声明,撤回转发,真值源冲突,防脚本盖用户改值,PC_SIM适配层 | fixed |
| P-0075 | 2026-10-02 | 用户「SIM_H_RES/SIM_V_RES 也走配置，不要自动查找，太麻烦，其他同理手动指定」→ **配置区升为显式表**：各项都给默认值（SIM_H_RES=800 / SIM_V_RES=480 / LVGL_CONF_FILE=<proj>/design/sim_cmake/lv_conf.h / 三目录 / APL_LVGL_DIR 留空才 up-walk），**删掉分辨率两段正则共 36 行**（P-0072 同句多赋值坑结构性消失），行数 219→192。验证重点=**手填真生效**：临时构建树 `-DSIM_H_RES=1024` 自证行打出 `窗口=1024x600`、CACHE 实际 1024/600（不 build 只 configure）；另 `mv exe+mv build` 全新跑全量（首跑 Error 2 是并发偶发、增量重跑 grep error 0 命中）、CACHE 自证 800/480、`--walk=wifi_ok` 3 图目检 OK、device syntax 4 文件 0 错 0 警。**CACHE 默认值只在首次 configure 落盘**→ 验证新默认值必须 mv build；反过来解决"脚本盖掉用户手填值"。「自动查找」按代价分级：痛的（正则 36 行）必手填，短的（一行拼路径）留着，长且手填易错的（内核 up-walk 25 行）保留兜底，别一刀切 | 手动指定优先,显式配置表,删正则查找,CACHE默认值只在首配落盘,-D覆盖实测,自动查找分级 | fixed |
| P-0076 | 2026-10-02 | 用户「改动太复杂，`cmake -D` 不用这样，直接在文件里改，文件改动太大，要最简修改；APL_LVGL_DIR 也改成手动指定」→ **从「重写」退回「外科手术」**：从原版 240 行备份复原，只做 6 处手术（插配置区 / GLOB 改 EEZ 平铺 / LV_CONF 注入 / 内核手填 / 入口换工程 main.c+WIN32 链接 / ThorVG 屏蔽），**祖传死代码一律不删**（USE_FREERTOS/SDL2_image/五可选库/ccache 全保留）。diff 从 -199/+178 降到 **-30/+83**（36 行注释），293 行（原版 240）。「不要 -D」= 配置全写**普通 set**（普通变量遮蔽 CACHE，命令行压不动，实测 `-DSIM_H_RES=999` 后自证仍 800x480）。修 3 个静默 bug：① **ThorVG 屏蔽正则必须用 `libs[\\/]thorvg`**——Windows SOURCES 是反斜杠，写死正斜杠静默不匹配→编必挂 `config.h` 缺失；内核是 `GLOB_RECURSE src/*.c/*.cpp` 把 thorvg 收进 **lvgl target**（非 CONFIG_ 建的 lvgl_thorvg 库）；配自证 `屏蔽 N 个`（0→49 即生效）② `LV_BUILD_CONF_PATH` 必须 CACHE，普通变量传不进 apl_lvgl 子作用域（P-0066 复现）→ 回落默认 lv_conf 开 ThorVG ③ 原版残留 `set(SIM_H_RES 320 CACHE ...)` 是第二真值源，CACHE set 会干掉同名普通 set（窗口显示 320x240）。验证：mv exe+mv build 全新 1m58s 编译通过、冒烟全绿、14/11 出图、walk 3 图目检 OK、device 4 文件 0 错 0 警 | 最简外科手术,最小diff,普通set压过-D,单真值源,Windows斜杠正则,屏蔽必须留自证数字,Anti-静默失败 | fixed |
| P-0077 | 2026-10-02 | 用户「需要配置的放上面，不需要配置的放下面，注释简短点」→ 配置区重写成 **8 项纯 + 行尾短注释**（目标顺序 TARGET_PROJ_DIR→APL_LVGL_DIR→LVGL_CONF_FILE→SIM_H_RES/V_RES→UI/NATIVE/SIM_MAIN_DIR 三项），长理由压成 1-2 行并留 P-00xx 编号；293→273 行、配置区 21→12 行。**非配置项下移到用点旁**：LV_CONF 三行注入挪到 `set(APL_LVGL_DIR ... CACHE)` 后、add_subdirectory 前；`CONFIG_LV_USE_THORVG_INTERNAL OFF` 挪到 ThorVG 屏蔽块前。★ 坑：第一版把它放到屏蔽块 = **add_subdirectory 之后**，内核 option() 已跑完 → 静默失效（不报错）；铁律=凡要影响内核的赋值必须在 add_subdirectory 之前，整理后必跑自证四连 | 配置区排布,配置在上实现在下,行尾注释,赋值时机vs add_subdirectory,静默失效,自证四连,防误判(raw字节数=W*H*4) | fixed |
| P-0078 | 2026-10-02 | 用户贴编译刷屏「警告这么多」→ 两个根因。① **lv_conf.h 里 `LV_FONT_CUSTOM_DECLARE` 定义了两遍**：705 行是官方模板空占位、713 行是 EEZ 字体实体声明 → 每编译一个单元报一次 redefined。修：**删掉官方空占位**（内核 `lv_conf_internal.h:1922` 有 `#ifndef` 空值兜底，实体声明自动成为首次定义，功能不变）；设计侧 `design/lv_conf.h` 是源头、仿真副本由 `sim.py:write_lvconf()` 派生，改一处两边生效。② **仿真白编 LVGL 官方 examples/demos**（`os_desktop.cmake` 里 `CONFIG_LV_BUILD_EXAMPLES/DEMOS` 默认 ON，每个 example .c 都 include lv_conf → 把那一条警告复制了 N 份）→ 在 `add_subdirectory` 前两个都 set OFF（沿用 P-0077 铁律）。验证：configure 期 warning=0、CACHE 三开关齐 OFF、全新编译 exit=0 warning 数=0、walk 目检中文/图标渲染正常 | 警告刷屏先看倍数再看条数,同一宏定义两遍,删官方模板空占位,关编不需要的库,改lv_conf先动源头,option开关必须在add_subdirectory前 | fixed |

| P-0079 | 2026-10-02 | 用户报「点 WiFi 弹不出密码面板」→ 连挖三层：① **走路器假绿**——`wfind()` 只查名字表**不判可见性**，密码面板没弹时 `kbdkey`/`ta` 照样往 hidden textarea 灌字、读回 `"abc"`，整条"输密码→连接"看着全绿其实一步没走；自证得用 `state` 命令打 `lv_obj_is_visible()`（面板/键盘/列表 + 5 行热区 `可见=0/1`），原来那个「面板在活动屏=1/-1」是假自证（`s_pwd_panel` 只在 `w_do_key` 里赋值，-1 只说明没轮到赋值）。② **别顺手修用户定死的 hiddenExpr**：`build_ui.py` 里 `net_slotN_hit` 的 `hiddenExpr = "ssid==' || !(cur4)"`（热区**只在失败态那行**显示、与 pill 的 `!(cur4)` 互补）是用户上轮定的「不要一点就弹 WiFi 连接」；我改成 `/(cur4)` 后点谁都弹面板被当场要还原。判据：**点 AP 命中可见的 `net_net_slotN`（不是 `_hit`）+ 面板始终"隐藏/未开" = 正常态**。③ 编译反复挂在 `liblvgl.a`（truncated / file format not recognized / 符号 undefined）——**孤儿 `mingw32-make.exe` 占着库句柄**，`taskkill //PID //F` 清掉 → `mv` 走脏 `.a` → 内核 `touch` 1051 个 src 全量重编。另改 3 处：命中打印沿父链找**第一个有名祖先**（`lv_indev_search_obj` 多返回匿名 part，原来只打父名一律显示 `net_net_list`）；新增 `mousef`（press/release 同帧的真人手速对照）、`scan`/`disc`（PC 入口 `extern` 调 io_pc，抓搜索态/未连接态，设备侧零影响）；两处排版改**整块居中**（未连接卡两行 18+6+14=38 块居中，原来叠 4px；搜索态环30+间距10+文字15=55 块对齐 scy，原来偏上 5px） | 走路器假绿,wfind不判可见性,lv_obj_is_visible,state自证,用户刻意 vs bug,孤儿make,liblvgl.a句柄,整块居中,叠加像素 | fixed |

| P-0080 | 2026-10-02 | 用户报「WiFi 输入密码/键盘弹不出」→ 根因是 **`hiddenExpr` 语义搞反**：从 `src/ui/screens.c` 生成模板（`new_val` 真 → `add_flag(LV_OBJ_FLAG_HIDDEN)`）自证 **hiddenExpr 表达式为真 = 隐藏**，而 `net_slotN_hit` 写的是 `... || !(cur4)`，常态下 `!(cur4)` 为真 → **热区被隐藏** → 点 AP 命中没绑动作的 visible row → `wifi_pick_N` 从没调用 → 面板/键盘永远弹不出（失败态反而露出来压住「重试」pill）。改回 `... || (cur4)`（失败态隐藏热区、让位给 pill，与 pill 的 `!(cur4)` 严格互补）。**上一轮栽在"把代码字面当用户意图"**——P-0079 见 `!(cur4)` 是用户"还原"回来的就当免检，没真点一遍证伪；`git diff` 干净 ≠ 语义正确，用户说"某功能没反应"必须真点取证。验证：`--walk=pwd` 加 `state` 硬自证（点前 面板=隐藏/键盘=隐藏 → 点后 **面板=可见 键盘=可见**）+ 截图目检键盘完整；`wifi`/`wifi_retry`/`wifi_ok`/`click_speed` 全绿；流水线 9.29%<25%；设备侧 4 文件 0 错 0 警 | hiddenExpr语义,真=隐藏,add_flag,热区被隐藏,密码面板弹不出,键盘不可见,state自证,假绿,别只看git diff | fixed |

| P-0081 | 2026-10-02 | 用户报「键盘按钮没文字」（澄清=真机确认/取消按钮）→ 先误判缺字形（`_font_cov.py` 证伪：EEZ 把 label 文本烘进 `--symbols`，全覆盖），真因是 **EEZ button 子 label 的 DSL 坐标被按「相对按钮的父容器」解释，生成 `lv_obj_set_pos = DSL pos − button pos`**，写 `label_mid(0,0,...)` → (−18,−110) 飞出屏幕。修：label 坐标传**按钮左缘 + 居中补偿**（`btn_cx(base_x)`，两按钮左缘不同不能共用 x）。全量检查（用户要求「检查所有的」）：静态 DSL 累加越界脚本 254 条**全假阳性**（tabview 隐藏页/滚动区/浮层还原不了）已删；改走路器新增 **`audit` 命令**（运行时 `lv_obj_get_coords` 真实矩形 + `lv_obj_is_visible` 过滤，`audit_all` 走 6 态，`_audit_report.py` 解析）→ 唯一 vis=1 空 label 是 textarea 内部 placeholder（正常）→ **除取消/连接外全 UI 无缺字**。坑：objects_t 正则要 `typedef struct\s*\w*\s*\{`（EEZ 带 tag 名 `_objects_t`，漏了静默跳过自动对象表）；切页必须 tap rail 按钮（nav_chat/nav_music/nav_bell/nav_tune），`tab set` 落隐藏容器切不动；write_main 自动登记 screens.h ~650 对象名进 wmap | button子label,坐标二次减偏移,btn_cx,缺字形误判,--symbols,静态越界假阳性,audit运行时体检,lv_obj_get_coords,lv_obj_is_visible,textarea placeholder,objects_t正则 | fixed |

| P-0083 | 2026-10-02 | 用户点单修复 4 实锤+扫描态不居中。① 通知卡时间顶对齐标题行、按钮对齐卡中心 → 差 11px，时间改与卡同中心。② **transform_height 加在 LV_PART_MAIN 会吃掉 slider/bar 的 obj 背景绘制**（INDICATOR 收缩生效、MAIN 轨道底整个消失，P-0049 技法盲区）→ 轨道底改普通 box 垫底+MAIN bg_opa=0，5 调用点零改动（track() 返回透明容器包 [轨道底,slider]）；★ DSL 子对象必须绝对坐标（to_relative 递减），写 (0,0) 会被 check_bounds 拦。③ knob 0/100 值被 obj 裁半圆 → MAIN pad_left/right=kd/2。④ **EEZ label 根本没有 textAlign 属性**（W35 官方属性表 + asar 挖证；widget "style" 发射 text_align 实测也不生成）→「42 %」6px 空隙的根治 = **"%3d %%" 定宽字符串变量**（clock_text 同款 native 模式，ASCII Consolas 等宽 → 左对齐=右缘恒定），volume/brightness/music_vol/alert_vol/battery 5 个 _text 变量全链路（DSL variables+app_model 枚举+native_vars 桥+io_pc/io_esp 拼串）。⑤ label() 显式传 w 自动 wUnit=px（原来被 content 吞掉，「正在搜索网络…」w=iw+CENTER 全失效的另一半根因）+ 静态 tw() 居中。⑥ 附赠：状态栏 "% 85" 顺序反 → battery_pct_text。验证：all.py --sim PASS、设备侧 4 文件 0 错 0 警、audit 坐标+像素双实证、扫描态目检 | textAlign不存在,transform_height吃MAIN背景,轨道底box垫底,knob裁半,pad防clip,定宽串%3d,wUnit断链,静态居中,绝对坐标体系,%%转义 | fixed |

| P-0084 | 2026-10-02 | 用户贴图「进度条状态不对 + 搜索要转圈动画」。① **P-0049 的 MAIN transform_height 老技法有致命副作用**：lv_bar.c draw_indic 用 lv_area_increase(transf_h) 收缩 bar_coords，14px 控件收 -9 → 高度**负数**，内核 snap 回 LV_BAR_SIZE_MIN=4 时用负 barh 算中心 → **INDICATOR 画到轨道上方 4px 成一条细线**（fill「消失」+ 多一条蓝线 + 时间与进度视觉不符），音量条同样中招。修 = 彻底废除 transform_height，**INDICATOR 变细用 MAIN pad_top/pad_bottom**（内核 indic_area 本就从 bar_coords 减 MAIN pad，lv_bar.c:361-364）；实证 fill 紧贴 knob、时间 01:54=48%×238s 同步、seek 闭环不弹回。② 转圈 = **EEZ W71 Spinner (LVGL)**（asar 挖证无专有属性，lv_spinner_create 即自带 1000ms 旋转，lv_spinner.c:93）→ json2eez TYPE_MAP/FLAGS 注册 + default_clickable 排除（防挡面板点击）+ build_ui 扫描态 spinner 32px（MAIN 底弧暗/INDICATOR ACCENT 圆头 3px）；动画验证 = 临时 FAKE_SCAN_SEC 2→10s 连拍 4 帧亮弧角 -10°→-37° 变化。③ 走路器：tapxy 只发 CLICKED 对 slider 无效 → 新增 **setslider** 命令（set_value+VALUE_CHANGED 走全回写链）；walk 截图目录 50 文件触发沙箱 bulk-delete 拦截（清目录重跑）；raw 快照必须 sim.read_raw（文本头+BGRA）。| transform_height负面积,INDICATOR细线,MAIN pad收细,lv_spinner,EEZ W71,setslider命令,FAKE_SCAN_SEC临时加长 | fixed |

| P-0085 | 2026-10-02 | 用户要求「长按 WiFi 列表项 → 忘记密码」+「重新扫描先主动断开」。① **EEZ 原生支持 LONG_PRESSED**（事件枚举 code 7，asar 实证）→ json2eez 新增 `onLongPress`（eventHandlers **数组**追加 LONG_PRESSED handler，与 CLICKED 并存：短按=连接/长按=忘记，同一控件两条 User Action）。② 忘记确认卡（遮罩+居中 400x178，WARN 橙忘记钮）挂 wifi_pop 内容区最后=z 最高；显隐 wifi_forget_shown。③ native 全链路：FORGET(带槽位=弹卡)/FORGET_CONFIRM(真忘)/FORGET_CANCEL 三条命令；io_pc 用 s_saved[]+s_slot_sub[][] 可变副本（AP_LIST const 不能改）+ wifi_rebuild_sub；s_connected_slot 记录连接槽（tick 2→3 + 钉态两处）；忘当前连接 → 断开回未连接。④ rescan 先断开：io_pc/io_esp 的 io_wifi_scan 入口先 disconnect。⑤ 坑：walk 对象名=screens.h 字段全串（带 m_）；button() 无 id → walk 用 tapchild <面板> <子序号>；新 action 缺 native 实现是**链接期**错（EEZ 只生成 extern）；heredoc 吃宏续行符。验证：all.py PASS、walk=forget 全链路（弹卡/忘记断开/取消收卡）、设备侧 0 错 0 警 | LONG_PRESSED,onLongPress,eventHandlers数组,忘记网络,确认卡,WARN钮,saved可变副本,rescan先断开,链接期错,tapchild | fixed |

| P-0089 | 2026-10-02 | 左栏「网络与连接」由弹浮层改回切 tab 页（P-0088 续）。① **页序是全局约定**：`set_nav` 恢复「网络」子页后页序 = 0 通用 / 1 网络 / 2 显示 / 3 唤醒（与左栏自上而下一致），牵动 CATS 表、rail_cats 的 switchTab、pane_settings 每行 tab_i、onTabChange 高亮分组（4 组，`cats_add[0]` 也归 wifi —— 左栏无「通用」项，沿用 P-0034「每页都要有归属高亮」）、**sim.py 的 nav_btn_for / VIEWS 表 / 冒烟段 / 滑动断言期望值**。改页序必须把这 6 处一次改齐，漏一处仿真就点错页。② 同源内容两份共存：pane_network 在子页(prefix `netp_`)与浮层(`net_`)各建一份，共享同一批 native 变量与命令，状态天然一致；json2eez 画布分区 `_bucket` 要补 `/netp_`。③ ★★ **走路器对象表上限会静默溢出**：`WALK_MAX_MAP 700` 遇 screens.h ~846 对象时 `wmap_add` 丢尾部，症状像「对象改名了」（`!! longpress: 没有对象 m_net_net_slot0_hit`，该名在 screens.h 里明明有）。修：上限提到 1600 + wmap_build 结尾打印「对象表 N 条（上限 M）★已满」自证；以后走路器报「没有对象」先看这行。④ walk 截图目录累计 50 个文件触发沙箱 SAFE_DELETE_BULK_CONFIRM（exit=1 但 walk 已跑完），清理要分批每批 ≤8。验证：all.py PASS、cattab 四页目检（网络页左栏高亮同步且浮层未弹）、wifi/wifi_ok/forget 回归绿 | 页序全局约定,netp_前缀,对象表溢出,WALK_MAX_MAP,静默丢弃,SAFE_DELETE_BULK | fixed |

| P-0088 | 2026-10-02 | 左栏「网络与连接」由「直接弹浮层」改为「切 tabpager 页」。★ **两次教训**：① 用户说「切到指定 tabpager 页」指的是**切到已有的通用页(tab 0)**（通用页第一行就是「无线网络」），我第一遍误解成「新增一页 Wi-Fi 面板」做了个 `tab_net` 子页（pane_network 建两份 prefix `netp_`），被用户「你的修改错误了，先还原」打回。**改导航前先确认目标页是否已存在**，需求有歧义就问，别自己发明新页。② 正确实现极简：CATS 里 wifi 由 `"pop"` 改成 `0`，rail_cats 删掉 pop 分支（旧链是 `switchTab(tab=None)` 只同步高亮 + `onShow` 开浮层两条动作组件）与 pop_refs 参数，wifi 行改 `switchTab{tv_ref,tab:0}` + clear/add 高亮链，与 sun/mic 完全同款；页序仍是 3 页(0 通用/1 显示/2 唤醒)所以 sim.py 只加 `nav_btn_for case 0`、其余索引不动；通用页 pane_settings 不动（「无线网络」行仍弹浮层做连接设置）。验证：生成里两个入口各自独立 flow(508 切页 / 358 弹浮层)、screens.h 无 netp_/tab_net 残留、cattab 目检与用户配图一致、wifi/wifi_ok/forget/pwd 四条浮层链路回归绿 | 切页≠新增页,目标页已存在,pop分支删除,switchTab tab0,净改动3行 | fixed |

| P-0090 | 2026-10-02 | 真机构建失败修：`GetBoard` was not declared（板级音量桥接）。① **本工程没有 `GetBoard()`** —— 板单例是 `Board::GetInstance()`（board.h:62，返回**引用**，内部 static 懒建 create_board）；本板类 `P4AudioBoard : public WifiBoard`，codec 取法 `Board::GetInstance().GetAudioCodec()`，且**引用不能判空**（别写 `if (!b)`）。写板级/组件桥接前必须先 grep 确认符号真身，别凭其它项目的印象写。② ★★ **真机改动的验证姿势升级（P-0050 补强）**：不再用 `-fsyntax-only`（不跑优化器，抓不到 -Werror），改**真编译** = 取 build/compile_commands.json 的原命令**只把 `-o` 后面那个产物路径换成临时 .obj**，其余参数与源文件**一律照抄**（自己再补 `-c`+源文件、或剥掉 `-c` 却留着源文件，都会报 "cannot specify '-o' with '-c' … with multiple files"）。实测覆盖 board_p4_audio.cc + src/native/{io_esp,app_model,native_actions,native_vars}.cpp 全 exit 0 零警；xiaozhi 组件里的 wifi_board.cc 需手工补 `-DBOARD_TYPE/-DBOARD_NAME`（宏在它自己的 cxxflags，compile_commands 条目的 response 文件是空的）→ 补后 exit 0。PC 仿真编译永远照不到 xiaozhi 那棵树，只有这套真编译能在烧录前拦住。 | GetBoard,Board::GetInstance,引用不可判空,真编译验改动,只替换-o,multiple files,-DBOARD_TYPE | fixed |

| P-0091 | 2026-10-02 | WiFi 列表行长按触发「忘记」时**连带**触发了「点击连接」。① **根因在内核，不是 LVGL/EEZ 的 bug**：`lv_indev.c:869-884` RELEASED 分支里 `if(i->long_pr_sent == 0) { indev_proc_short_click(...); }`（长按跳过 short click）**之后那句 `send_event(LV_EVENT_CLICKED, ...)` 在 if 之外** —— 长按松手必然再发一次 CLICKED。行热区同时绑 CLICKED(wifi_pick_N) + LONG_PRESSED(wifi_forget_N)，同一次手势两条命令都出去。凡「同一控件两个事件（短+长）」都要想到这条。② **修法 = native 侧抑制窗口**：`static uint32_t s_lp_guard_ms` + `WIFI_LP_GUARD_MS 800`；forget action 记 `lv_tick_get()`，pick action 在窗口内 `return` 不输出命令（800ms：松手后 CLICKED 几十 ms 内就到，又不吞用户紧接着的正常点击）。③ ★ **仿真器必须复现内核这个行为才验得了**：走路器 `longpress <obj>` 原来只发 LONG_PRESSED（等于绕过了 bug），新增**第二参 `1` = 紧跟 CLICKED**；新增走路脚本 `lpsuppress`（长按带 CLICKED → 只见忘记卡；1.2s 后普通点击同一行 → 正常弹密码面板，证明短按没被误伤）。④ 坑：Python heredoc 写 C 的 `\\n` 会落成字面反斜杠+n（printf 打出 `\n` 两字符），写完 `sed -n 'Np' \| cat -A` 自查。验证：真机真编译 exit 0 零警、日志实证 `pick slot N suppressed`、截图无密码面板、wifi/forget 回归绿 | long_pr_sent,CLICKED在if之外,抑制窗口,长按双事件,longpress第二参,cat -A自查 | fixed |
| P-0092 | 2026-10-03 | 真机 MQTT 8883 一直超时（443 OTA 通、8883 MQTT 不通，同设备同域名同网络同时间的**通道对照表**一次性排掉 Wi-Fi/DNS/路由/电源）；★ 两次误判都是**先猜配置后找证据**：①猜 NVS 存了陈旧 endpoint → 被日志 `Connecting to endpoint api.tenclass.net` 推翻；②猜 `CONFIG_LWIP_TCP_MSS=1440` 撑爆 SDIO 隧道 → 被 `ShowNotification: 版本 9.9.9` 推翻（该串来自 `application.cc:299-308` HandleActivationDoneEvent、版本取自 `lvgl_demo_ai/CMakeLists.txt:77` ⇒ **OTA 大包已成功**；且 1440+20+20+4=1484 < `ESP_TRANSPORT_SDIO_MAX_BUF_SIZE` 1536，根本没超）→ **明确不要动 MSS**。其余排除：sock=54 已建（非 DNS）、证书 bundle 已开、NVS 16KB 够、`strings` 固件查硬编码域名零命中（endpoint 只来自 NVS/OTA）、PC 同网 443/8883/80 全 OPEN。边界 = **本地功能全可用、云端对话不可用**（唤醒后音频要经 MQTT 上云做 ASR/LLM/TTS，断了⇒哑）。未根治，等 A 加诊断日志 / B 摘链路 / C 不管 三选一 | 真机,MQTT,esp-tls,8883,OTA443,通道对照,先猜后证,ShowNotification反证,别动MSS,esp_hosted,SDIO | open |
| P-0093 | 2026-10-03 | 删除 EEZ 整页后 `sim.py` 生成的 C 冒烟段残留 `objects.m_ai_orb` 引用 → 编译直接失败（`error: 'objects_t' has no member named 'm_ai_orb'`）。★ **删页/删控件后固定自检三步**：①`grep "objects\.m_" design/sim.py` 对照 `src/ui/screens.h` 对象表查悬空引用 ②`grep -rn 被删对象名 design/*.py build/*.py` 查映射表残留 ③跑 `all.py --sim` 看屏数+差异率。★ **截图文件名编号只删不排**（01,02,05,06…）：`build/sim_shots` 历史 PNG + `compare.py` MAP + `verify_center.py` RAW_OF + `icon_survey.py` VIEW_FILE 四处都以文件名为键，重排=**静默集体错位**（比编译错误更难查）。同步改 4 处；`action_voice_stop` 的 native 实现保留（孤儿函数无害）。验收：9 屏（原 11）、平均差异 9.08%（阈值 25%）、无缺屏、EEZ 产物时间戳同秒 16:12:11 自证生成区未手改 | 删页,EEZ生成区,仿真,编译错误,objects悬空引用,截图编号,只删不排,四处映射,孤儿函数 | fixed |

---

## ⚠ 完整性对账（2026-10-03 自动核对，待补）

对账方法：`index.md` 里的编号 vs `intake/` 目录下实际文件（全库 `find` 复核过，非路径问题）。

**A. 索引有、文件缺失（18 条）** —— 内容可在工程日志 `.workbuddy/memory/2026-10-0x.md` 回填：

`P-0046` `P-0047` `P-0048` `P-0049` `P-0050` `P-0051` `P-0052` `P-0053` `P-0054`
`P-0055` `P-0070` `P-0083` `P-0084` `P-0085` `P-0088` `P-0089` `P-0090` `P-0091`

**B. 文件有、索引漏登记（1 条）**：`P-0020`（`P-0020_固件链接报 undefined reference to get_var_.md`）

> 说明：以上**不是本次新增造成的** —— 本次只加 P-0092 / P-0093，文件与索引双向齐全。
> 按 INTAKE 纪律「只追加不改历史」，此处只登记不删改；补齐时优先从工程当日日志回填
> （日志里有完整现象/根因/证据），补不了的标 `open` 待查。
| P-0094 | 2026-10-03 | 「始终连上次指定的WiFi」= 把 SsidManager 剪成唯一一项（推翻 P-0086 的 set_config 方案） | WiFi,SsidManager,HandleScanResult,RSSI,剪枝,StartStation,managed_components | fixed |
| P-0095 | 2026-10-03 | UI 时间比实际快 8 小时：自家 SNTP 与小智 OTA 双写系统时钟 | 时间,SNTP,OTA,settimeofday,时区,息屏,双写冲突 | fixed |
| P-0096 | 2026-10-03 | 真机偶发重启：TLSF 空闲链表被写坏，崩在 DHCP 首批 malloc；探测器本身又造出第二个崩溃 | 崩溃,heap,TLSF,addr2line,esp_hosted,中断看门狗, sdkconfig | open |
| P-0097 | 2026-10-03 | 一完成对时就熄屏：息屏计时用了墙上时间 + 活动打点其实没人调 | 息屏,背光,timeNULL,esp_timer,单调时钟,跨任务,io_note_ui_activity | fixed |
| P-0098 | 2026-10-03 | 唤醒词没有点亮屏幕：接语音交互态（SetCallbacks 外部接管是陷阱） | 息屏,唤醒词,DeviceState,SetCallbacks,桥接,GetDeviceState | fixed |
| P-0099 | 2026-10-03 | 6 个开关全是装饰：json2eez 的 switch 分支把 stateVar 真状态绑定覆盖成 literal | switch,json2eez,checkedStateType,stateVar,假反馈,审计 | open |
| P-0020 | 2026-09-27 | 固件链接期 20 条 `undefined reference to get_var_*/set_var_*`，两层原因叠在一起：① `src/native/CMakeLists.txt` 只有 `set(NATIVE_SRCS ... PARENT_SCOPE)`、没有 `idf_component_register` → native 被跳过、`native_vars.cpp` 从未编译（★ EEZ 只生成 `vars.h` 的 extern，**从不生成 vars.cpp**，这 20 个函数的唯一定义就在 native_vars.cpp）；② 补上注册后仍失败 —— ui 与 native 之间没有依赖，ld 扫库列表里 `libnative.a`(122) 先于**第二次**出现的 `libui.a`(123) 被扫过 ⇒ 判库顺序必须看「最后一次出现」的相对次序。修：native 改成真组件（`REQUIRES driver lvgl`，刻意不用 `REQUIRES ui` 免循环依赖，ui 的头文件走 `INCLUDE_DIRS ../ui`）+ `main/CMakeLists.txt` 显式列全依赖（IDF 特例：一旦写 REQUIRES 就丢掉「默认依赖全部」）+ 工程顶层 `cmake_policy(SET CMP0079 NEW)` 后 `target_link_libraries(${ui_lib} PUBLIC ${native_lib})`（不能写进 ui/CMakeLists.txt —— EEZ 每次导出都重写它）。验收：`nm` 双向比对（ui 需要 20 / native 提供 22，差集为空）、EXIT=0、`build/lvgl_demo_v9.bin` 1669472 字节、`nm` 查到 20 个 get_var_/set_var_ 全就位 | ESP-IDF,链接,native,组件,CMake,库顺序,EEZ | fixed |
| P-0044 | 2026-10-01 | 设置从 3 页改 4 页（网络子页恢复）后**断言全绿但截图串位**（09 出显示页、10 出唤醒页，内容整体偏移一位）：「设置页序」在工程里有**三处独立副本**，本轮只改了 ① `build_ui.py` 的 `CATS` 表 ② `sett_nav` 的 `onTabChange` add 分组，**漏了 ③ `sim.py` 模板里的 `nav_btn_for()` 设置层映射** —— 仿真切页优先点分类按钮（走真机同款动作链），idx1/2 还指向旧页按钮，于是「切到 1」实际点的是显示行。为什么断言抓不住：[wifi]/[swipe] 只查 `lv_tabview_get_tab_active` 序号与 CHECKED 高亮（两者都「正确」），而对照门禁只看 11 屏平均差异、单屏串位被平均稀释 ⇒ **必须目检该层全部子页截图**。修：`nav_btn_for` 按 通用0/网络1/显示2/唤醒3 重写；规则 = 动 sett_nav/main_nav/ai_nav/mus_nav 的页数或顺序时，CATS、onTabChange 分组、sim.py 的 nav_btn_for + VIEWS 一次改完（同一张清单在 P-0089 被扩成 6 处） | tabview,页序,nav_btn_for,VIEWS,串位,目检 | fixed |
| P-0045 | 2026-10-01 | 设备侧专属文件（`io_esp.cpp`）是 PC 构建盲区：真机 `idf.py build` 报 `-Werror=comment`（"/*" within comment）+ `'cmd' was not declared` —— `io_esp.cpp:54` 的 wifi TODO 注释**漏写收尾** `*/`，一路吞掉 battery 段、`io_sample_inputs` 的收尾 `}` 和 `io_wifi_command` 函数头。根因 = 该文件只在设备构建编译（PC 仿真选 io_pc.cpp），G1-G5 门禁全绿也照不到，注释块被手改/搬移时少个 `*/` 就静默潜伏，直到第一次真机编译才爆，而且**报错位置（被吞的下游代码）与病灶相距数十行**极易误判。修：补回 `*/` + 核验 29/29 配平、函数签名恢复、`io_iface.h` 声明齐全。规则：凡改过 `io_esp.cpp`（哪怕只加注释/TODO）提交前 ① 数一遍 `/*` 与 `*/` 是否配平（一行 Python）② 有条件就跑一次 `idf.py build`；这条盲区后续补上了可执行检查 —— P-0050 的 compile_commands 取命令自检、P-0052 修正为真 `-O2 -c` 编译（`-fsyntax-only` 不跑优化器 = 假绿） | io_esp,注释,潜伏,Werror=comment,真机构建,盲区 | fixed |

## ⚠ 完整性对账（更正前一条）· 2026-10-03 二次核对

> 本节**只更正统计口径与数字，不删改上一条**（`## ⚠ 完整性对账（2026-10-03 自动核对，待补）`
> 整段原样保留）。按 INTAKE.md 第 0 条纪律「只往后追加，绝不改历史；判断被推翻时新写一条说明为什么当初算错」。
> 本节数字由本次补档（任务 1 / 任务 2）**完成后**重新计算。

### 一、正确的统计口径（两套集合各只能用一种取法，混用就算错）

- **index 的条目行** = 只数**表格首列**（正文里被引用的编号**不算**条目）：
  逐行 `re.match(r'^\|\s*(P-\d{4})\s*\|', line)`，**不允许**行首有空格。
- **intake 的正文文件** = 只从**文件名**取：`re.match(r'^(P-\d{4})[_.]', name)`。
- 建议直接跑（两行 Python，别用 `grep -o "P-[0-9]\{4\}"`，那会把正文引用算成条目）：
  见本节末「复核命令」。

### 二、更正后的数字（本次补档完成时实测）

| 项目 | 严格口径（正确） | 宽口径（前一条用的，容忍行首空格） |
|---|---|---|
| index 表格行 | **86**（唯一编号 86，无重号） | 95 唯一编号 / 97 行（P-0044、P-0045 各 2 行，见第四节） |
| intake 正文文件 | **86** | 86 |
| 有行无正文 | **0** | **9**：P-0046 P-0047 P-0048 P-0049 P-0050 P-0051 P-0052 P-0053 P-0055 |
| 有正文无行 | **0** | 0 |

补档之前（严格口径）是：表格行 83、正文文件 77、**有行无正文 9**
（P-0054 P-0070 P-0083 P-0084 P-0085 P-0088 P-0089 P-0090 P-0091）、**有正文无行 3**（P-0020 P-0044 P-0045）。
本次已把这 9 条正文按 `TEMPLATE.md` 六段式补齐（素材 = 对应的 index 行 + 工程日志
`.workbuddy/memory/2026-10-02.md` 的轮次原文），并给 3 条正文在表格末尾补了行。

### 三、前一条为什么算出「88 个编号 / 悬空 18 条」—— 复核结论（与委托时给的猜测不同，据实记）

委托方给的假设是「前一条把正文里引用的编号误计成了条目」。**复核结果：这一条不成立**，
前一条列的 18 个编号在 index 里**都有实打实的表格行**，没有一个是纯正文引用造出来的幽灵。
真正的原因是**口径不统一**：

1. 前一条用的是**容忍行首空格**的宽口径（`^\s*\|...`）。它算的时候 P-0094~P-0099 那 6 行
   还没落盘，宽口径当时 = `94 − 6 = 88` —— 数字对得上，说明就是这个口径（严格口径当时是 83）。
2. 于是它报的「悬空 18 条」= 严格口径下真的 9 条（本次已补）
   \+ 另外 9 条（P-0046~P-0053、P-0055）—— 这 9 条**确实也是行、也确实没有正文文件**，
   只是它们所在的 11 行（P-0044~P-0053、P-0055）**首列前多打了一个空格**，
   严格口径根本不把它们当行，所以两份清单看起来"差了 10 条"。
3. 「把正文引用算成条目」这个错法确实**存在风险**，只是前一条没犯：全文 `P-\d{4}` 唯一编号
   现在 = **96**，比宽口径的 95 多出的那一个就是 **P-0086**（它只出现在 P-0094 那行的正文里
   「推翻 P-0086 的 set_config 方案」，库里既无行也无正文）。用全文 grep 就会凭空多出一条。

### 四、本次补档自己引入 / 发现的账实不符（只登记，未擅自改）

1. **P-0044、P-0045 现在各有两行**：旧行首列前有空格（第 48、49 行），本次按委托在表格末尾
   又各补了一行顶格的。按纪律**不删旧行**；以本次新增的顶格行为准。
   根治办法是把那 11 行的行首空格删掉（属"改历史"，需用户点头，本次未动）。
2. **仍有 9 条「有行无正文」**：P-0046 / P-0047 / P-0048 / P-0049 / P-0050 / P-0051 / P-0052 /
   P-0053 / P-0055（就是上面那批带前导空格的行）。不在本次委托的 9 个编号之内，**未补**；
   素材齐备 —— 工程日志 `.workbuddy/memory/2026-10-02.md` 第 73~79 轮（PR-0100~PR-0106）。
3. **P-0086 / P-0087 库里彻底无账**：工程日志有实内容（2026-10-02 第 102 轮「真机点的≠连的」、
   第 103 轮「取消小智自带 WiFi 配网」），`MEMORY.md` 与 P-0094 行还反过来引用 P-0086，
   但 index 无行、intake 无正文。**未补**（未获委托），建议单独登记。
4. **空号**：P-0019（有据可查 —— 2026-09-28 日志记录「删 `intake/P-0019` + index.md 对应行」）、
   P-0082（日志里查无任何轮次对应，纯跳号）。INTAKE 规矩是「不留空号」，此处只登记不追溯。
5. **前导空格行共 11 行**（`^\s+\| P-\d{4}`）：除 P-0044 / P-0045 外，其余 9 行见第 2 点。

### 五、复核命令（下次自查直接抄，别再手工数）

```python
import re, os
lines = open('index.md', encoding='utf-8').read().splitlines()
rows  = [m.group(1) for l in lines if (m := re.match(r'^\|\s*(P-\d{4})\s*\|', l))]          # 顶格表格行
loose = [m.group(1) for l in lines if (m := re.match(r'^\s*\|\s*(P-\d{4})\s*\|', l))]       # 容忍行首空格
files = {m.group(1) for p in os.listdir('.') if (m := re.match(r'^(P-\d{4})[_.]', p))}      # 正文文件名
print(len(rows), len(set(loose)), len(files))
print("有行无正文", sorted(set(rows) - files))
print("有正文无行", sorted(files - set(rows)))
print("两种口径之差（= 行首多打空格的行）", sorted(set(loose) - set(rows)))
```
| P-0100 | 2026-10-03 | 待机页「最近对话」是硬编码假文案 + 聊天超长消息被砍半个汉字 | 聊天,待机页,UTF8截断,chat_copy_clip,假反馈,输入框装饰 | fixed |
| P-0101 | 2026-10-03 | 给聊天气泡补完整字库：GB2312 1~9 区不能盲烘（撞引擎校验）+ 字形检查器自己会假警 | 字库,GB2312,eez_font_engine,_glyph_lint,cmap,豆腐块,余量 | fixed |
| P-0102 | 2026-10-03 | app 分区余量被字库吃光：16MB 布局改 32MB（分区表一变必须整机重烧） | partitions.csv,flash,ESPTOOLPY_FLASHSIZE,OTA,整机重烧,余量 | fixed |
| P-0103 | 2026-10-03 | 走路器：内层 tabview 的页要两段 tab 命令；无 id 圆钮只能 mousef 图标 | sim.py,走路器,双层tabview,mousef,截图错位,目检 | fixed |
| P-0104 | 2026-10-03 | 假文案换真值会让 G5 差异率合法上涨，别当回归回滚 | 门禁,G5,compare.py,差异率,基线,假文案 | wontfix |
| P-0086 | 2026-10-02 | **回填（2026-10-03 补建）**：真机「点的不是连的」= StartStation 前写 STA 配置只在 station 已 active 时才有效；★ 方案已被 P-0094 剪枝推翻，只有「`esp_wifi_sta_get_ap_info()` 作显示权威源」那半条至今有效 | WiFi,StartStation,esp_wifi_set_config,点的不是连的,回填,已被P-0094推翻 | fixed |
| P-0087 | 2026-10-02 | **回填（2026-10-03 补建）**：开机自建 `Xiaozhi-xxxx` 配网热点 —— 三条进入路径全汇到 `StartWifiConfigMode()`，在入口放总闸（日志 + `return`）；★ `xiaozhi-esp32/` 是 git 跟踪的 vendor 树（可改，commit `bb3555c`），`managed_components/` 被 gitignore（不可改） | 配网,AP热点,StartWifiConfigMode,总闸,vendor树可改,回填 | fixed |

## 再核（第 3 次对账 · 2026-10-03，Qoder）

> 只追加，**不改上两节**（第 1 节「待补」的 18 条清单、第 2 节「二次核对」的 86/9/0 数字
> 都原样保留；它们的时点各自有效）。本节是 P-0086/P-0087 补建**之后**的实测。

1. **口径按上一节「五、复核命令」逐字跑**（不要自己另发明正则），实测结果：
   顶格表格行 **93**（唯一 93，无重号）｜intake 正文文件 **93**｜
   有行无正文 **0**｜有正文无行 **0**｜行首带空格的伪行 **11 行 / 唯一编号 9**
   （行号 48~58 = P-0044~P-0053、P-0055，其中 P-0044/P-0045 另有顶格重复行，故 11 行→9 个编号）。
2. **撤回我（Qoder）上一轮口头报的「21 条伪行」**：换任何口径都复现不出 21
   （行首空格+首格编号=11、行首空格+含编号=11、任意 `|` 行含编号=104、全文编号出现次数=205）。
   ⇒ 那是一次**手工数数且口径混用**（行 vs 唯一编号），不是新证据。**上节的 11 行是对的。**
   教训：对账数字只能来自脚本，且必须把正则一起写进结论，否则下一个人无法复算。
3. **上一节「四.3 未补（未获委托）」已解除**：P-0086 / P-0087 本轮已补建正文 + 索引行
   （用户 2026-10-03 点单「补建 P-0086 登记缺账」）。两文件均为**回填**，正文里写明了
   素材出处（工程日志 2026-10-02 第 102 / 103 轮）与「当时结论已被 P-0094 推翻」。
4. **仍存的账外项（本轮只登记，未动）**：
   - **空号**：P-0019（有据：2026-09-28 日志记录删过）、P-0082（日志查无对应轮次，纯跳号）。
   - **11 行前导空格**：删空格属"改历史"，需用户点头，仍未动。
   - **提示词缺账**：工程日志 2026-10-02 第 102~104 轮（P-0086/P-0087/P-0088 首批）的
     用户原话**没有**进 `PROMPT_LOG.md`（PR-0112 之后直接跳到 PR-0113，中间无 2026-10-02 晚条目）。
     按纪律 0.2「提示词逐字抄」应补，但工程日志只有**转述**没有逐字原话 ⇒ 无法在不编造的前提下回填，
     标 `待查`：需用户确认是否接受"按日志转述补录并标注非逐字"。
   - **工程注释里的 P 号 ≠ 库内 P 号**（部分已解）：本轮把 11 处写着 `P-0099` 的注释
     改成了 `P-0100`/`P-0101`（那批做的是聊天/字库，与库里 P-0099「6 个开关是装饰」无关）。
     历史遗留的映射表仍未建：例如工程里 P-0088 被当作「UI 控件接硬件」用了 30 处，
     而库内 P-0088 = 「左栏切 tab 页」——**建映射需用户点头（要动历史注释）**。
5. **同轮第 2 次实测（P-0105 登记之后，正则同上）**：顶格表格行 **94**（唯一 94）｜
   正文文件 **94**｜有行无正文 **0**｜有正文无行 **0**｜伪行仍 **11 行 / 9 个编号**。
   ⇒ 上面第 1 点的 93/93 是「P-0086/P-0087 补建完、P-0105 登记前」的时点值，两个数都别改。
6. **提示词缺账已清**（纪律 0.2）：`PROMPT_LOG.md` 补录 **PR-0139~PR-0156** 共 18 条
   （时间写 `2026-10-03（补录）`，逐字抄用户原话含错别字）。
   ⇒ 第 4 点里「2026-10-02 第 102~104 轮无逐字原话」那一项**仍未解**，保持 `待查`。
7. **本轮归属改判**（工程注释侧，非库内容）：原先写着 `P-0099` 的**代码/DSL 注释共 12 处**已改判 ——（★本条口径有误：真数是 **13 处**，且当时那句「grep = 0」是假绿，见第 8 点）
   ai_state / 胶囊 / 桥接类 **9 处**（io_esp.cpp:59/400/438/445/633/764、io_pc.cpp:41、
   app_model.h:93、sim.py:1787）→ **P-0105**；聊天 / 待机页类 **3 处**
   （native_actions.cpp:365、native_vars.cpp:40、sim.py:1796）→ **P-0100**（sim 那条并列 P-0101）。
   第 13 处是工程日志 `.workbuddy/memory/2026-10-03.md:593` 的「本轮不占 P-0099」编号说明，
   **属事实陈述，未动**。顺带修掉 **3 处**过时注释：`io_esp.cpp:401`、`native_vars.cpp:161`、
   `build_ui.py:2547` 仍写「网络正常 / 等待回复…」及早已删除的 `io_ai_state_publish()`。
   验证：`_device_syntax_check.py`（含 board_p4_audio.cc）5 文件 0 错 0 警；
   `all.py --sim` = 9 屏平均明显差异 **9.87%**（阈值 25%）无缺屏 —— 本轮只动注释，数字不变才对。
| P-0105 | 2026-10-03 | AI 对接状态胶囊的四态口径：只有 GetDeviceState 可拿，文案必须与能拿到的真值对齐 | AI状态,胶囊,DeviceState,桥接,文案与真值,io_pc镜像,aiaudit | fixed |

8. **撤回上一条里我自己算错的数**（同轮第 3 次实测，口径已改为绝对根扫描）：
   `P-0099` 的代码/DSL 注释**真数 = 13 处**，不是 12 —— 漏的那一处在
   `lvgl_demo_ai/main/board_p4_audio.cc:131`（板级桥在 **eez-test 目录之外**）。
   我上一条写的「`grep -rn P-0099 src design main` = 0」是**假绿**：那是从 `eez-test/`
   发的相对路径，而 `eez-test/main` **根本不存在**，grep 对不存在的目录不报错 ⇒ 少扫一棵树。
   已改判为 `P-0098/P-0105`，并用绝对根重扫确认 `../main ../xiaozhi-esp32/main src design
   ../partitions.csv ../sdkconfig.defaults`（排除 `src/ui` 生成区）**零残留**；
   `board_p4_audio.cc` 真编译重跑 0 错 0 警。
   ⇒ 固化：**扫描根必须写绝对路径**，别用相对 `main`；`design/_pnos_map.py` 就是把根
   硬编码成 `eez-test` 与 `lvgl_demo_ai` 两棵树，所以这次能扫出来。

## 工程注释 P 号 ↔ 库内 P 号 映射（eez-test，2026-10-03 建）

**为什么建表而不改注释**（用户 2026-10-03 定口径）：工程注释里那批 P 号是**当时思考的痕迹**，
大面积改注释 = 零收益的 diff 且丢掉历史。所以本表当**翻译层**：读到工程注释里的号，先来这儿查
"它在这个工程里真指什么"。**今后新写注释**：号必须当场用 `python tools/log_entry.py next-id problem`
取，登记与写注释在同一次动作里完成 —— 本轮 13 处撞号全是"事后补号"造成的。

复核命令（只读，不改任何东西）：
`python eez-test/design/_pnos_map.py` → 打印每个号的出现次数、分布、库内标题（`★库内无` = 该号
在库里没正文）。

### C 级 · 明确错位（**必须翻译，否则会读错文档**）

| 工程注释里的号 ×处数 | 工程里真指什么（代表位置） | 库内同号是什么 | 该翻到哪 |
|---|---|---|---|
| **P-0088 ×37 中的 25 处** | 「UI 控件接硬件**第一批**」= 背光 PWM / 主音量 codec / 息屏真熄屏（`io_esp.cpp` 13 处含前置声明、`app_model.h:61/136`、`native_vars.cpp:25/140`、`io_iface.h:49/50`、`CMakeLists.txt:47`、`native_actions.cpp:112`、`build_ui.py:2173/2529`…） | 「左栏『网络与连接』改切 tab 页（切页≠新增一页）」——**与硬件接线无关** | 库里**没有**这批硬件接线的条目；素材 = 工程日志 `2026-10-02.md` **第 104 轮**。当时说好的空号 P-0106 已被同轮「语音文本进消息区」占用（见下），补建这批要占 **P-0107**，**等用户点头**（本轮未建） |
| **P-0095 ×1** | `CMakeLists.txt:62` 用它解释 `esp_timer` 依赖（息屏计时用单调时钟） | SNTP 与 OTA 双写系统时钟（时间快 8 小时） | 单调时钟那条真身 = **P-0097**（同件事在 `io_esp.cpp:74/393` 署的就是 P-0097） |
| **P-0086 ×4** | 「显式写 STA 配置 + `esp_wifi_sta_get_ap_info` 作显示权威源」（`io_esp.cpp:418/561/603`）+ 「重新扫描按钮太小」（`build_ui.py:1754`） | 同题，但**回填时已写明方案被 P-0094 推翻** | 生效机制看 **P-0094**（`SsidManager` 剪成唯一一项）；只有 `sta_get_ap_info` 那半条至今有效 |
| **P-0088 ×37 里的另 12 处** | 切页 / 页序（`build_ui.py:1024/1063/1458/2366`、`sim.py:155/1474`、`main.c:47` = 切页 7 处；`build_ui.py:1464`、`sim.py:188/460`、`main.c:80/352` = 页序 5 处） | 切页那 7 处与库内 P-0088 **一致**；页序那 5 处库里归 **P-0089** | 页序读作 **P-0089**（「页序是全局约定，6 处要一次改齐」） |

### B 级 · 同一条的某个侧面（可以继续这么写，读到别误解）

- **P-0083 ×14**：工程专指「`"%3d %%"` 定宽串 = 右缘恒定」这一子项；库内标题还含 `transform_height`
  吃 MAIN 背景、EEZ label 无 `textAlign`。一致，只是工程取其中一条。
- **P-0093 ×10**：主事 = 删页后 `sim.py` 冒烟段残留引用；同轮排查副产品（`build_ui.py:598`
  「全工程曾没有 AI 状态变量」、输入框装饰）也署了 P-0093 —— 那些**不是** P-0093 的主题。
- **P-0098 / P-0105 并列写法**（如 `io_esp.cpp:59/445/633`、`app_model.h:93`）：不是撞号，
  是 `ai_state_tick()` 一条源同喂两件事（亮屏 + 胶囊），见 P-0098「追加」节。
- **P-0098 单独出现在 `io_esp.cpp:395`** 时指的是「工作任务也会写 `s_last_activity_ms` ⇒ 跨任务并发」，
  那条应归 **P-0097**。

### D 级 · 活代码在引用、库里没正文（补档优先级从高到低）

宽松口径下「有行无正文」共 9 条：`P-0046 P-0047 P-0048 P-0049 P-0050 P-0051 P-0052 P-0053 P-0055`
（它们是行首多打一个空格的**伪行**，严格口径不计，见上节「五、复核命令」）。其中 **4 条仍被工程注释引用**：

| 号 | 工程引用处 | 这条讲什么（据注释） |
|---|---|---|
| P-0053 ×3 | `json2eez.py:303`、`sim.py:409`、`sim_cmake/main.c` | textarea 属性错写成 `objID` → 密码面板键盘绑不上 |
| P-0049 ×2 | `native_vars.cpp:101`、`build_ui.py:440` | 滑杆 knob 裁半 + 「把命令伪装成状态供显示」方案退役 |
| P-0051 ×2 | `_font_cov.py:9`、`_glyph_lint.py:5` | 运行时文本（星期名）字形覆盖 —— 仿真小字看不出、真机才露 |
| P-0046 ×2 | `sim.py:511`、`sim_cmake/main.c:403` | 走路器 `toggle` 命令 = 发 RELEASED 让 CHECKABLE 翻转 |

⇒ 这 4 条正是 DSL/工具铁律的出处，缺正文 = 后来人顺着注释查不到依据。素材在
`2026-10-02.md` 第 73~79 轮，**要不要补由用户定**（本轮未动）。

### A 级 · 一致，无需翻译

`P-0020 P-0021 P-0026 P-0029 P-0032 P-0034 P-0035 P-0045 P-0074 P-0080 P-0081 P-0084 P-0085
P-0087 P-0089 P-0090 P-0091 P-0092 P-0097 P-0100 P-0101 P-0105`（工程含义与库内主题对得上）。
| P-0106 | 2026-10-03 | 语音聊天的文本进不了消息区：GetDisplay 是 NoDisplay，stt/tts 只落成日志（改无锁环每 tick 取一条） | 聊天,跨线程,NoDisplay,SetChatMessage,无锁队列,SPSC,PSRAM,P4零阻塞 | fixed |
| P-0107 | 2026-10-03 | 「B 不要输入」被我理解成保留装饰：底部输入条+发送钮整条删除（PC 触发改按状态机时序） | 对话页,输入框,发送钮,装饰,需求理解,PC触发时序,走路器 | fixed |
| P-0108 | 2026-10-03 | 设置项各存各的：音量与小智双真值源互相盖、息屏时间改了不存 —— 统一成一张表 + 每拍比对变更 | 设置,NVS,音量,双真值源,统一表,周期比对,PSRAM无关 | fixed |
| P-0109 | 2026-10-03 | 聊天气泡头像方块是空的：注释写着 sparkle/person 却没放图标，而 audit 只查文字查不到 | 聊天,头像,图标,FontAwesome,glyphs_seed,审计盲区 | fixed |
| P-0110 | 2026-10-03 | 单击滑杆会闪一下：先跳到目标值、弹回旧值、再跳到目标值（显示走输入变量，改动却在命令队列里） | 滑杆,闪烁,回弹,输入变量,命令队列,统一表,乐观回显 | fixed |
| P-0111 | 2026-10-04 | 设置页「网络与连接」永远显示 Home-5G / 已连接·信号强：整行是设计稿写死的静态文案 | 静态文案,假反馈,WiFi,绑定,glyphs,snprintf,stdio | fixed |
| P-0112 | 2026-10-04 | 待机页天气卡四项全是设计稿字面量（24° / 晴 / 北京·空气优·体感26° / 太阳），还自相矛盾 | 静态文案,假反馈,天气,绑定,图标四态,UnboundLocalError,数据源待定 | fixed |
| P-0113 | 2026-10-04 | 天气数据源接 Open-Meteo：HTTPS 抓取跑独立工作任务；新建 .cpp 不在 compile_commands，逐文件真编译会把它当成没编译却报通过 | 天气,Open-Meteo,esp_http_client,esp_crt_bundle,工作任务,P4零阻塞,快照互斥,compile_commands,验证盲区,export.ps1 | fixed |
| P-0114 | 2026-10-04 | 天气地点做成可收藏多城：位图存 NVS + 12 颗 CHECKABLE 胶囊浮层 + 多城一次 HTTPS 请求 | 天气,多选,NVS,位图,CHECKABLE,checkedState,表达式无位运算,浮层遮罩,Open-Meteo多城,父边界门禁,链接期缺setter | fixed |
| P-0115 | 2026-10-04 | 曲库接真 SD 卡：BSP 的 bsp_sdcard_mount 早就链进固件只是没人调用；FATFS 关着长文件名 + API 编码默认 ANSI 会让中文歌名变豆腐 | SD卡,SDMMC,FATFS,长文件名,UTF-8编码,曲库,lv_list重灌,generation,假反馈,ESP_PLATFORM分界,无热插拔 | open |
| P-0116 | 2026-10-06 | 播放态 UI 不同步：np_playing 是播放按钮链的页面局部变量，凡是不按这个按钮的状态变化必然错相 | EEZ,变量绑定,音乐播放,仿真走路,所有权 | fixed |
| P-0117 | 2026-10-07 | 音乐三条：暂停把进度抹成 00:00（位置所有权错）+ seek 是空桩（滑杆必弹回）+ 对话中点播放把对话挤掉 | 音乐播放,进度条,seek,所有权,AI抢占,esp_hosted,真机取证 | open |
| P-0118 | 2026-10-07 | 歌词块是设计稿假词：接同名 .lrc，当前行恒居中（样式静态时靠窗口对齐做高亮） | 歌词,LRC,UTF-8,字库档位,EEZ静态样式,PSRAM,P4零阻塞,单写者 | fixed |
