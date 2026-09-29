# 提示词日志（PROMPT_LOG）

> 追加式：**只往后加，不改历史**。每条对应「用户 → AI」的一次输入，
> 用于日后追查「当时为什么要改这个」。写入方式见 `../INTAKE.md`。
> 格式由 `tools/log_entry.py prompt` 生成；手写请照抄同一格式。
>
> **本库不限 AI 工具**：标题第三段写【实际使用的工具名】（WorkBuddy / Claude Code /
> Cursor / Codex / …），历史条目里的工具名是当时的事实，新条目照实写即可。

---

### PR-0001 · 2026-09-23（补录） · WorkBuddy
  - 提示词：了解一下工程
  - 诉求：摸清工程是干什么的、怎么组织的
  - 产出/结论：确认是 EEZ Studio v3 + LVGL 9.4 工程，单一设计源 `build_voice_ui.py` → `ui_voice.json` → EEZ 工程 → `screens.c`
  - 关联：无

### PR-0002 · 2026-09-23（补录） · WorkBuddy
  - 提示词：你帮我看看UI，你能够每个界面检查一下，跳转是否都正常
  - 诉求：逐屏核对跳转完整性
  - 产出/结论：新增 `design/check_nav.py`；查出 13 屏不可达、3 死胡同、5 处跳自己、3 按钮无事件
  - 关联：无

### PR-0003 · 2026-09-23（补录） · WorkBuddy
  - 提示词：为什么一点击界面，画面来回跳
  - 诉求：定位"点击后画面来回跳"
  - 产出/结论：归纳三类成因（元素压底栏跳错页 / Tab 当前页跳自己 / 一个 source 多连线），见 `skills.md §7.2`
  - 关联：无

### PR-0004 · 2026-09-23（补录） · WorkBuddy
  - 提示词：现在又检查没有问题，再检查一下跳转是否正常，。你可以自己打开，自己点击一下吗
  - 诉求：要 AI 自己打开并能真点击验证
  - 产出/结论：EEZ 编辑器画布无法真点击（canvas 零监听器，被组件外壳截走）→ 改用 `design/sim_nav.py` 命中仿真
  - 关联：无

### PR-0005 · 2026-09-23（补录） · WorkBuddy
  - 提示词：那我还原了
  - 诉求：告知工程已被整体还原
  - 产出/结论：重做修复，改为"不动可见元素、只压布局/改属性"；原因是上一版删了 Settings「通用设置」行
  - 关联：无

### PR-0006 · 2026-09-23（补录） · WorkBuddy
  - 提示词：我只需要确认一点，你可以模拟，并且测试点击效果吗
  - 诉求：确认能否仿真真点击
  - 产出/结论：确认材料本机齐全（LVGL 9.4 源码 / mingw64 / SDL2）
  - 关联：无

### PR-0007 · 2026-09-23（补录） · WorkBuddy
  - 提示词：有GCC ，再 D:\Program_Files\mingw64
  - 诉求：提供编译器位置
  - 产出/结论：记下 gcc/g++ 13.1.0 路径
  - 关联：无

### PR-0008 · 2026-09-23（补录） · WorkBuddy
  - 提示词：有咩有不需要环境，也可以测试的
  - 诉求：问是否有零编译的替代方案
  - 产出/结论：说明 EEZ 组件外壳 DIV 可用 `elementsFromPoint` 反推权威 z 序/几何，可零编译校验命中
  - 关联：无

### PR-0009 · 2026-09-23（补录） · WorkBuddy
  - 提示词：你不要拷贝到 工程目录编译，可以放在桌面上面建立一个文件夹编译，你移动一下 ，现在我的仓库git都变更很多了
  - 诉求：编译产物不要污染仓库
  - 产出/结论：把测试台搬到桌面 `UI_ClickTest`，改为绝对路径
  - 关联：无

### PR-0010 · 2026-09-23（补录） · WorkBuddy
  - 提示词：不是有编译模板吗，为什么 还在编译阶段 ，有 lvgl 配置模板
  - 诉求：疑问为何还要现编
  - 产出/结论：模板默认 LVGL 9.2，须换 9.4 并关 ThorVG/Lottie，故仍需一次完整编译
  - 关联：无

### PR-0011 · 2026-09-23（补录） · WorkBuddy
  - 提示词：好像卡住了
  - 诉求：反馈卡住
  - 产出/结论：说明程序跑完不自动退出（SDL 窗口挂住），需 `timeout` 包一层
  - 关联：无

### PR-0012 · 2026-09-23（补录） · WorkBuddy
  - 提示词：你现在在干嘛
  - 诉求：询问当前进度
  - 产出/结论：汇报编译进度
  - 关联：无

### PR-0013 · 2026-09-23（补录） · WorkBuddy
  - 提示词：为什么显示一个后台任务运行中
  - 诉求：询问后台任务
  - 产出/结论：说明是编译后台任务
  - 关联：无

### PR-0014 · 2026-09-23（补录） · WorkBuddy
  - 提示词：可以帮我关闭掉
  - 诉求：关闭后台任务
  - 产出/结论：用 PowerShell 对进程对象 `Kill()` 关掉 EEZ（`taskkill` 权限不足）
  - 关联：无

### PR-0015 · 2026-09-23（补录） · WorkBuddy
  - 提示词：你帮我梳理一份 UI 测试项目，根据这个测试案例，能够输出稳定的UI
  - 诉求：把经验做成能稳定产出 UI 的测试项目
  - 产出/结论：形成 UI 测试条例 D/G/R 三段
  - 关联：无

### PR-0016 · 2026-09-23（补录） · WorkBuddy
  - 提示词：根据当前经验，总结一下，examples\idf_v541_my_exps\Template\spilcd_spiopt_eez_lv_port_pc_tem_atks3\main\test\ui_debug_kit 帮我在这个目录输出一个skills.md ，能够方便下一个项目实现 UI 自动设计和对照查验问题，然后自动使用仿真器仿真，仿真器的路径可以运行技能时候问我，同时帮我梳理一份 UI 测试条例，根据这个测试条例，能够输出稳定的UI
  - 诉求：在 ui_debug_kit 输出 skills.md（面向下个项目）+ UI 测试条例；仿真器路径运行时询问用户
  - 产出/结论：交付 `ui_debug_kit/skills.md` + `ui_test/` 三脚本（audit_ui / gen_clicks / run_gate）
  - 关联：无

### PR-0017 · 2026-09-23（补录） · WorkBuddy
  - 提示词：audit_ui.py   gen_clicks.py run_gate.py 不可以放在kit 中码
  - 诉求：这三个脚本应该放进工具箱，而不是散在工程里
  - 产出/结论：迁入 `ui_debug_kit/tools/`，彻底配置化、去掉硬编码；删除 `ui_test/`
  - 关联：无

### PR-0018 · 2026-09-23（补录） · WorkBuddy
  - 提示词：继续
  - 诉求：继续完成迁移收尾
  - 产出/结论：核对文件状态、跑通门禁（G1 FAIL 仅 3 个已知项，G2/G3/G4 PASS）
  - 关联：无

### PR-0019 · 2026-09-23（补录） · WorkBuddy
  - 提示词：仔细检查一下这个技能，是否可以
  - 诉求：对整套技能做可用性审计
  - 产出/结论：修 2 个真缺陷（缺 Pillow 裸崩、tab_bar 模板陷阱），同步文档与 CHANGELOG v0.4.1
  - 关联：P-0001, P-0002

### PR-0020 · 2026-09-23 14:16 · WorkBuddy
  - 提示词：这个技能的结构我要求，后期我使用这个技能开发的时候，遇到新的问题，我要求可以将这个问题可以输出到这个技能里面，不管是什么AI工具，同时你要将 我跟你 交流的提示词记录到技能里面，方便后续追查
  - 诉求：给技能加"新问题登记 + 提示词留痕"的结构，且不依赖具体 AI 工具
  - 产出/结论：新增 `INTAKE.md` 规约 + `intake/`（问题登记，P-####）+ `prompts/`（提示词日志，PR-####）+ `tools/log_entry.py`（通用写入器）；并回填本次全部提示词
  - 关联：无
### PR-0021 · 2026-09-23 14:38 · WorkBuddy
  - 提示词：现在这个UI，我要求底部状态栏不滑动，选择界面时候
  - 诉求：切页（选界面）时底部状态栏不要滑动
  - 产出/结论：确认采用淡入过渡：json2eez fadeMode 默认 MOVE_LEFT->FADE_IN，重建 EEZ 工程与 ui.c(assets blob 0x05->0x09)
  - 关联：（待补）

### PR-0022 · 2026-09-23 16:29 · WorkBuddy
  - 提示词：我发现界面中很多按钮开关无效，这里你要适配一下
  - 诉求：让界面里的开关能用
  - 产出/结论：定位到 switch() 是装饰容器；EEZ 有 LVGLSwitchWidget（自带 CHECKABLE）
  - 关联：（待补）

### PR-0023 · 2026-09-23 16:29 · WorkBuddy
  - 提示词：依然很多 界面中的 开关 按钮无法点击，无法使用
  - 诉求：确认仍未修好，要求彻底修复
  - 产出/结论：把 16 个 switch() 改为真 LVGLSwitchWidget，重建工程与 screens.c；新增断言 A9
  - 关联：（待补）

### PR-0024 · 2026-09-23 17:41 · WorkBuddy
  - 提示词：根据  技能 和 设计图，帮我生成对应的UI界面 ，要求完全和设计稿一致，
  - 诉求：（待补）
  - 产出/结论：（待补）
  - 关联：（待补）

### PR-0025 · 2026-09-23 17:41 · WorkBuddy
  - 提示词：使用D:/esp32_8266_files/esp-idf-v5.4.1/examples/idf_v541_my_exps/common/PC_SIM 作为模拟器
  - 诉求：（待补）
  - 产出/结论：（待补）
  - 关联：（待补）

### PR-0026 · 2026-09-23 19:09 · WorkBuddy
  - 提示词：输出到技能内
  - 诉求：（待补）
  - 产出/结论：（待补）
  - 关联：（待补）

### PR-0027 · 2026-09-23 20:17 · WorkBuddy
  - 提示词：我发现现在每个子对象，都是并列关系，没有形成父子关系，也不是相对布局
  - 诉求：（待补）
  - 产出/结论：（待补）
  - 关联：（待补）

### PR-0028 · 2026-09-23 20:17 · WorkBuddy
  - 提示词：我要求每个对象的name不同，不然我说那个对象有问题，我不好描述
  - 诉求：（待补）
  - 产出/结论：（待补）
  - 关联：（待补）

### PR-0029 · 2026-09-23 20:17 · WorkBuddy
  - 提示词：继续、
  - 诉求：（待补）
  - 产出/结论：（待补）
  - 关联：（待补）

### PR-0030 · 2026-09-27 13:33 · WorkBuddy
  - 提示词：读取当前工程，使用C:/Users/Administrator/Desktop/local_knowledge_base/EEZ Studio_ui_debug_kit 这个本地知识库
  - 诉求：读取工程并以该本地知识库为方法论/工具集接管 UI 调试工作
  - 产出/结论：验证知识库可从工程根经 cwd 向上找到 ui_debug_kit.config.json（kit.py 关键路径全 OK，仅预览/仿真目录未生成）。跑 G1 断言 A1/A2/A3/A4/A6/A8/A9 全 OK（A5/A7 无底栏跳过），G4 组件树 11 页/50 跳转全通过。G5 需先出仿真图。
  - 关联：（待补）

### PR-0031 · 2026-09-27 17:03 · WorkBuddy
  - 提示词：继续（接续上下文）：核验字体图标码位 + 跑 G5 设计稿对照
  - 诉求：确认 v0.9 的三级门禁在当前 D 盘工程全绿，补齐之前未跑的 G5 仿真对照
  - 产出/结论：G1/G4/G5 全部 PASS；11 屏设计稿 vs 仿真实机平均明显差异 8.14%（阈值 25%）；字体 22 组 symbol 声明无缺字
  - 关联：（待补）

### PR-0032 · 2026-09-27 18:05 · WorkBuddy
  - 提示词：你适配了我的工程吗
  - 诉求：确认 ui_debug_kit 工具箱是否真正适配当前 D 盘工程，而不是看着 PASS 实际漏检
  - 产出/结论：新建 tools/config_check.py 做配置适配体检：最初 OK37/WARN2/ERROR0，修正后 OK38/WARN0/ERROR0 完全适配。修了三处：① tree_check 未配墨迹偏移时用 y+1..y+px+1 系统性低估下边界（13px 差 3px、54px 差 15px）→ 改为 PIL 实测，从严后 G4 仍全通过；② 配置 type_values 漏声明 bar(9)/switch(6)/screen(11)；③ 体检脚本自己把 11 页去重显示成 1 页。
  - 关联：（待补）

### PR-0033 · 2026-09-27 20:37 · WorkBuddy
  - 提示词：所有的按键单击，可以增加打印
  - 诉求：UI 上每次按键单击都要打印日志，能看出点中了谁、要跳哪去
  - 产出/结论：新增 click_trace 单击打印钩子（src/native/click_trace.{h,cpp} + 自动生成的 click_map.{h,cpp}）。运行时按命中对象中心点反查控件 id/goto，打印 [CLICK] 页 id goto 坐标。不动 EEZ 生成代码。顺带补上 G3 命中闸门：81 个控件 11 屏 0 未命中，门禁 3 组变 4 组全 PASS。
  - 关联：（待补）

### PR-0034 · 2026-09-28 06:48 · WorkBuddy
  - 提示词：我不想用 examples\idf_v555_my_exps\p4_touch_lcd4_3_exp\lvgl_demo_ai\eez-test\src\native\click_map.cpp 这种方法，并本地知识库移除，因为这种方法显得很傻
  - 诉求：放弃「运行时按坐标反查控件身份」的单击打印方案（click_trace/click_map/G3 命中仿真），项目与本地知识库一并移除
  - 产出/结论：项目侧删 6 个文件（click_trace.{h,cpp}、click_map.{h,cpp}、gen_click_map.py、gate_g3.py）并清干净 9 处引用（main.c / native CMakeLists / native README / all.py / eez_check_build.py / sim.py --probe·--click-all / ui_debug_kit.config.json G3 门禁 / eez-test README / main CMakeLists），grep 复查 0 残留。知识库侧删 skills.md 全部命中仿真/G3 表述（L3/L4 重编号为 L2/L3）、config_check.py 与 run_gate.py 的 G3 引用、INTAKE.md 示例字样、intake/P-0019（坐标查表误判坑）；gen_clicks.py 保留（从设计源正向生成真点击用例，非坐标反查）。**后续方案：改用 EEZ 原生用户事件 executeLvglActionHook（控件身份由 EEZ 点击回调自带，无需坐标表），尚未实现。**
  - 关联：P-0019（已随方案删除）

### PR-0035 · 2026-09-28 08:52 · WorkBuddy
  - 提示词：根据本地知识库，自己核对一下UI，我感觉图像都不对
  - 诉求：（待补）
  - 产出/结论：（待补）
  - 关联：（待补）

### PR-0036 · 2026-09-28 09:15 · WorkBuddy
  - 提示词：我看了还是没有改好啊
  - 诉求：对 G5 修复后的设置页仍不满意，指出 UI 没改到位
  - 产出/结论：全分辨率复核发现设置左栏 tab 按钮被 LVGL 默认 pct(100)+grow(1) 撑成巨块，重写 fix_tabview.py 按四个 tabview 形态分别注入布局修复
  - 关联：（待补）

### PR-0037 · 2026-09-28 09:15 · WorkBuddy
  - 提示词：我要求你把UI改好
  - 诉求：明确要求把 UI 彻底改好而非停在平均差异数字
  - 产出/结论：第二轮修复：rail 图标化 + 列表行 + 顶栏胶囊；复核再抓出 prefix_ids 前缀导致 rail 图标字形未烘焙（P-0024），修复后 11 屏全过、图标齐全
  - 关联：P-0024

### PR-0038 · 2026-09-28 09:46 · WorkBuddy
  - 提示词：我要求都是使用 eez来生成UI，不要自己编写C代码 / 严格执行 EEZ 编辑，eez check \eez output，这样来生成代码
  - 诉求：UI 全部由 EEZ 工程原生定义并走 EEZ 构建输出，废除往生成代码里注入 C 补丁的 fix_tabview 路线
  - 产出/结论：反编译 EEZ 0.29 生成器模板确认：settings.general.darkTheme 可控 dark 参数（主/次色硬编码 BLUE/RED）；LV_FONT_DEFAULT 经 LV_FONT_CUSTOM_DECLARE 指向烘焙 13px 字体；rail tabName 直接写 FA 图标字符。fix_tabview.py 已删除，all.py 移除该步，G5=24.39%（原生形态与设计稿的形态差），11 屏图标/中文/深色全原生渲染
  - 关联：P-0025

### PR-0039 · 2026-09-28 10:40 · WorkBuddy
  - 提示词：我发现 还有字体问题。UI界面不够美观，你仔细仔细核对
  - 诉求：逐屏仔细核对字体与美观问题并修复
  - 产出/结论：逐屏核对+放大裁剪定位三处：rail 图标 13px 偏小且无文字、设置左栏被 LVGL tab 按钮填满机制均分成 111px 整格、Home-5G 副标题被延迟胶囊遮挡。反编译发现 EEZ 内置 tab 栏定制口子——LVGLContainerWidget 作 tabview 第一个子对象时样式发射到 lv_tabview_get_tab_bar（第二个子对象→content）。json2eez 注入首子样式容器：rail 17px 字体+图标\\n中文两行、导航栏 15px、设置左栏 pad 收成 ~50px 紧凑行+页面底色；LVGL 源码实证 text_font/text_align 可继承。G5 24.39%→17.10%，11/11 屏过，EEZ 原生零 C 补丁
  - 关联：P-0026

### PR-0040 · 2026-09-28 11:20 · WorkBuddy
  - 提示词：我要求修改后也要跟设计图效果一致 ，想想办法
  - 诉求：UI 视觉必须与 designer/v1.0 设计稿一致，想办法把原生 tab 栏形态改成设计稿形态
  - 产出/结论：四个 tabview 全 tabSize=0 隐藏原生栏，用设计稿 rail()/rail_cats() 容器重建导航，按钮绑 EEZ 原生动作 tabviewSetActiveTab(id 60) 切 tab，json2eez 新增 switchTab→LVGLActionComponent 生成。核心坑：动作 object 写重写前 id → 16 个 Widget index not found（identifiers 只收录被引用 widget + assign_ids 加页面前缀），修法=switchTab 持 DSL 节点引用、main() 在 assign_ids 后解析成最终 id。EEZ build 0 error，G5 17.10%→8.84%，11/11 屏全过
  - 关联：P-0027  - 勘误（同日核对后补）：前缀重写发生在 build_ui.py 的 assign_ids（PAGE_ALIAS Main=m），非 json2eez；主 rail 全屏仅一份实例、高亮静态固定「对话」，切音乐/通知/设置 tab 不跟随（05 页实证，已知未修），「每 tab 挂副本」仅设置左栏 rail_cats 成立
### PR-0041 · 2026-09-28 11:25 · WorkBuddy
  - 提示词：最近添加的经验库中添加的经验，你要仔细核对确认一下是否正确，不要瞎添加结论
  - 诉求：逐条实证核对最近写入的 P-0027/§11.8/PR-0040，不许有无证据的结论
  - 产出/结论：全部断言重新取证——动作 schema（asar registerAction id:60 逐字）、actions[] 表长65/index60（脚本计数）、identifiers 机制（finalize 只 push 被 mark 对象）均证实；查出 2 处错误（assign_ids 归因写成 json2eez，实为 build_ui.py；「每 tab 挂 rail 副本」仅设置左栏成立，主 rail 单实例高亮静态固定）+ 1 处遗漏（主 rail 高亮不跟随 tab，05 页实证，已知未修）。P-0027/§11.8/PR-0040/MEMORY/日志均已修正
  - 关联：P-0027

### PR-0042 · 2026-09-28 11:40 · WorkBuddy
  - 提示词：再仔细检查一下 经验库，有没有有问题的，有问题的要修复
  - 诉求：全库体检（不止最近条目），发现问题就修
  - 产出/结论：① P-0021/0022/0023 状态 open 但实际已修且字段大片待补——补全工程/复现/沉淀/标签/关联提示词，状态改 fixed（P-0021 注明终版=P-0025 原生路线，初版补丁已废除）；② cases/README 索引 B5/B6 挤在同一表格行（多余竖线）——拆开；③ cases 索引 B8/B9 引 PLAYBOOK §5.6/§5.7、PLAYBOOK 内部自引 §5.6 均为失效锚点——改为实际存在节（§4.5 / skills §5.6 / 场景C/D）；④ §11.7 加「已停用（现行=§11.8 路线，机制留档）」标注；⑤ §8 check_nav.py 命令与 §4.1/§6.2 G2 行加「本工程未挂载」注记；⑥ README 目录树 cases 补「B1~B10」说明。历史条目中的 fix_tabview/click_trace/sim_nav 引用属当时事实，按只追加纪律保留不改
  - 关联：P-0021,P-0022,P-0023

### PR-0043 · 2026-09-28 12:30 · WorkBuddy
  - 提示词：我再EEZ中启动测试了，发现有点不对，再设置界面中，小tab为什么点击，为什么是 tab页也动作，应该tab健固定才对，以后所有这种类型的tab pager,tab固定，页滑动
  - 诉求：设置界面点小 tab（分类行）时整个页面（含 tab 栏）跟着滑——要求 tab 键固定、只有页滑动；并确立为以后所有 tab pager 类型的通用规则
  - 产出/结论：rail_cats 4 份副本挂各 set 子 tab 首位（在内容区里）是根因——改单实例外置挂 sett_nav 兄弟位；高亮跟随用 CHECKED 状态链：导航项两态样式（DEFAULT 灰/CHECKED 高亮，子 label 不写色走 text_color 父链继承）+ 初始高亮 checkedState（LVGLWidget 基类属性，asar 实证）+ 点击动作链 objClearState→objAddState→tabviewSetActiveTab（executeLVGLApiComponent 对 actions[] 顺序执行实证，rail 链 9 动作/cats 链 4 动作）；sim.py 改优先模拟真实点击（lv_obj_send_event）+ 补 lv_tick_inc + 截图时间片 400ms。EEZ build 0 error，G5 8.84%→8.54%，10/05 屏目检高亮跟随全对；P-0027 遗留「主 rail 高亮不跟随」同步解决
  - 关联：P-0028,P-0027

### PR-0044 · 2026-09-28 13:30 · WorkBuddy
  - 提示词：总结一下经验到 经验库，方便后续快速修改，同时下次对于这种界面时候，要求主要询问我，实现什么效果
  - 诉求：① 把 tab pager 本轮（P-0028）经验以「方便后续快速修改」为导向固化进经验库；② 确立交互约定——下次遇到这类界面（tab pager / 导航类），AI 必须先主动询问用户要实现什么效果，再动手
  - 产出/结论：PLAYBOOK §0 新增第 8 条（先问后做）+ §5 新增场景 E（第 0 步确认清单：固定/滑动、高亮跟随、指示条、挂载位置、子元素颜色、动画；通用规则 4 条：导航单实例外置兄弟位、两态样式+继承+动作链做高亮跟随、验收走真实点击并等动画结束、快速修改三处同步且其余项清除名单必补新项）；skills §11.9 补第 8 条快速修改清单（改动点索引表：build_ui rail()/rail_cats()/s_home()/_resolve_switchtabs、json2eez 动作链段、sim.py nav_btn_for；常见需求最小改动；自检链）与第 9 条交互约定；项目 MEMORY.md 同步交互约定
  - 关联：P-0028

### PR-0045 · 2026-09-28 13:07 · WorkBuddy
  - 提示词：现在 UI经验库  不是只针对 workbuddy ，所有AI都要兼容，并且 仿真器路径也要提示我指定
  - 诉求：① 经验库不绑定 WorkBuddy，任何 AI 都能拿来就用；② 仿真器这类机器相关路径不能硬编码/自行猜测——配置缺失或换电脑失效时必须停下来提示用户指定
  - 产出/结论：确认库主体已是「任何 AI」口径（README/INTAKE/skills），INTAKE 示例 --tool WorkBuddy 改为 <AI 工具名> 占位，PROMPT_LOG 头部补「不限工具、照实写工具名」约定；新增 sim 配置段（template_dir/lvgl_src 必填 + mingw/cmake/sdl2_bin 可选），config_check.py 新增 "F 仿真器" 强校验（缺失/占位符/本机不存在 → ERROR 阻断并提示向用户询问），sim.py 硬编码路径全部改为从 ui_debug_kit.config.json 读、失效硬停打印「请向用户确认新路径」；PLAYBOOK §1.3/§1.4、CONFIG.md §1/§2/§3、README 上手步骤同步规则；本机路径经用户确认后写入工程配置
  - 关联：P-0028（先问后做同族约定）

### PR-0046 · 2026-09-28 22:40 · WorkBuddy
  - 提示词：所以我也要求，在运行仿真时，不能修改EEZ生成的代码，试图修改它生产代码就是错误的，examples\idf_v555_my_exps\p4_touch_lcd4_3_exp\lvgl_demo_ai\eez-test\src\ui 也就是这个里面生成的文件，你不能更改，写进本地经验中
  - 诉求：把「src/ui 等 EEZ 生成目录绝对不可修改」立为铁律——范围不限于平时，运行仿真/调试期间同样禁止；「试图修改生成代码」这个行为本身就是错误；要求写进本地经验库
  - 产出/结论：PLAYBOOK §0 新增第 9 条「代码生成器产物只读（最高优先级铁律）」：{GEN_DIR} 及一切生成器产物只读，调试/仿真/临时验证/"顺手修一下"全禁止；发现生成代码有问题唯一正路是修上游设计源或生成器再重新生成；手改产物三重害处（下次生成静默覆盖蒸发、掩盖真因失去可追溯性、让回归门禁失义）；用户逻辑走生成器预留扩展点或独立目录（native 桥接层/用户事件钩子），不碰产物。工程侧 MEMORY.md 铁律段同步强化（绝对化表述 + 通用版指针，与既有「UI 一律 EEZ 原生定义」铁律并列：前者管产出方式、本条管产物只读）
  - 关联：P-0025（EEZ 全原生路线的延伸约束）

### PR-0047 · 2026-09-28 22:54 · WorkBuddy
  - 提示词：我发现界面中还有很多按钮还没有适配，你自己都适配一次啊
  - 诉求：界面上大量按钮点了没反应，要求 AI 自主把全部未适配按钮配上动作，闭环验收
  - 产出/结论：盘点 27 可交互控件（7 导航已配 / 20 未适配）——根因是 place() 的 strip_goto 剥掉旧页面名 goto 后无替代动作。适配 20 个：12 个 switchTab（待机 p2/p1→ai_nav 对话/记录、4 tile→main_nav 分区+rail 高亮同步 rail_sync、语音返回/历史继续对话→ai_nav 对话、设置 4 行→set_nav 子 tab+cats 高亮同步）、7 个 onClick 写输出命令（fab→chat_send、wifi 总开关→wifi_command 复用、mic/dnd/wake/wake_dnd/auto_brightness 开关→新 toggle 命令）；勿扰行无对应页也输出 dnd_toggle。机制扩展：json2eez 新增 onClick→SetVariableActionComponent（asar 实证 native 变量 codegen 直生 set_var_<name>(value);），新 6 输出变量进 ui.json variables[]+native_vars.cpp 12 函数+app_model 枚举/排空+io_iface+io_pc 回显+io_esp stub。全程零碰 src/ui（铁律 §0.9 首次实战检验：改动全部在上游 design/ 与 src/native/）
  - 关联：P-0027（节点引用铁律）、P-0028（tab pager 规则）


### PR-0048 · 2026-09-29 03:50 · WorkBuddy
  - 提示词：那么请问我看里面除了变量之外，还有用户事件，可以使用用户事件吗，如果可以的话，你帮我举例使用用户事件看看 ／ 要求仔细阅读官方手册
  - 诉求：确认 EEZ「用户事件」（User Events，官方术语 User Actions）在 LVGL 工程的可用性，要求以官方手册为依据（不得只凭 asar 逆向或记忆），并实战举例一条完整链路
  - 产出/结论：仔细读了官方手册（GitHub eez-open/studio docs/reference guide/EEZ Studio reference guide.pdf，784 页，P7.3 Working with Actions / P7.3.2 Creating a User Action / A34.2.16 Event handlers：控件事件 Handler type = Flow|Action，Action 绑工程 Actions 面板 User Action），并交叉验证官方源码（features/action/action.tsx Action{implementationType:"flow"|"native"}；lvgl/build.ts buildActionsDecl 生成 extern void action_<name>(lv_event_t*)、buildActionsArrayDef 生成 ActionExecFunc actions[] 表；lvgl/widgets/Base.tsx native action 生成直调 action_<name>(e)；asar findAsset 实证 eventHandler.action 按名字索引）。结论：**LVGL 工程可用，native User Action 是官方正路**。实战：语音页聆听光球配 voice_stop（native），DSL 顶层 actions[]+onAction → json2eez sync_actions+handlerType:"action" → EEZ build 生成 actions.h/ui.c 动作表/screens.c 直调 → src/native/native_actions.cpp 实现 action_voice_stop→app_set_output(APP_OUT_VOICE_STOP)→io_voice_stop 回显。踩两个坑：①circle() 默认不可点击，光球需显式 clickable=True 否则生成 remove_flag(CLICKABLE) 点击永远落空；②eventHandler.action 必须存动作名（findAsset 按 maps.name 索引），存 objID 生成空 CLICKED 分支且无报错。另踩并行 Edit 同文件覆盖（旧教训复发，orb["onAction"] 被吃掉一轮）。冒烟：[io_pc] UI user-action voice_stop (v=1) 闭环，11/11 截图 G5=8.61% 无回归；真机侧 native/CMakeLists.txt NATIVE_SRCS 补 native_actions.cpp（P-0020 同款坑预防）
  - 关联：PR-0046（§0.9 产物只读——本轮全程只改 design/ 与 src/native/）、§11.11（用户事件机制沉淀）
