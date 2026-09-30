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


### PR-0049 · 2026-09-29 16:55 · WorkBuddy
  - 提示词：你在 本地 经验库 的总结是对的吗 ／ 按照官方文档，你绝的哪些按键使用action ，哪些使用 vars ／ 好的，那就帮我修改当前代码，要求修改准确
  - 诉求：先核验知识库总结是否有误，再按官方语义给出按钮「用 User Action 还是 native 变量」的分类，最后执行迁移（要求准确）
  - 产出/结论：①**知识库 §11.11 五条技术事实全部正确**（三件套、`{ 0 }` 空表经 lvgl-build.ts:2722-2724 实证、DSL 约定、两个静默坑、固件接入、executeLvglActionHook 辨析），PR-0048 亦无错误结论；但**缺口**是只讲了 User Action 一条路 → 已补第 6 条（官方三条合法路径：Action 直调 / Flow→SetVariable / Watch 组件 A91；官方无推荐明文、native 变量专章仍是 "Chapter XX" 占位符）+ 第 7 条（sync_variables 坑）。②**分类前的三条实测硬数据**改变了结论：ui.json 里 `"var":` 只命中 clock_text/clock_date 共 4 处（→ 7 个命令型变量**无任何 UI 绑定**）；8 个输出变量 getter 全是 app_get_output_last 回声（不反映真实状态）；四个 slider_row 是纯绘制无事件（→ brightness 变量无控件使用）。③**执行迁移**：7 个命令型（chat_send / wifi_command / mic_toggle / dnd_toggle / auto_brightness_toggle / wake_toggle / wake_dnd_toggle）onClick→onAction，变量从 16 删到 9（只留真状态）。**关键设计：APP_OUT_* 枚举与 app_model / io_* 出口一律不动**——两条路线共用同一条命令队列，这是零风险的关键。④**新踩坑**：json2eez 的 sync_variables 有「保留工程里多出来的变量」逻辑（kept），把 DSL 已删变量当成手工变量复活 → vars.h 仍生成 extern 而 native_vars.cpp 实现已删 → 链接期 undefined reference；已改为与 sync_actions 一致的整体重建（单向管线原则）。验收：EEZ build 0 error，actions.h/ui.c 8 项，vars.h 残留 0，screens.c 9 处回调体非空（防静默空分支），声明与实现符号 diff 一致；冒烟 8 条命令回显全触发 + 11/11 屏，G5=8.58%（上轮 8.61%）无回归，G4/G5 PASS。G1 的 A8 FAIL 经查为**既有口径过时**（本工程单屏架构已废 goto，design 统计恒为 0；改动前后 ui.json 的 goto 数都是 0），非本次引入
  - 关联：PR-0048（User Action 机制）、§11.11 第 6/7 条


---

## PR-0050 字体生成结论纠错：GUI 会烘焙，headless CLI 不会（2026-09-29）

**用户质疑（原话）**：「EEZ CLI build 会删掉 ui_font_*.c 且不重，我看了会重建啊」
/ 「你的结论错误了，我在 eez 的 ui 中，使用 check 和 build 会生产文件，你弄错了，
你的验证方法是不是错误了」。

**结论：用户是对的，我的验证方法有错。** 错在「用单次观察否定能力」——
我删掉一个字体文件后跑了一次 CLI build，见它没回来，就推出「EEZ 不生成字体」。
「这一次没发生」只能证明这条路径这次没触发，不能证明 EEZ 没有该能力，
更不能覆盖 GUI 路径。下结论前应先查配置开关与产物清单，再对 GUI / CLI 分别下判断。

**实测三层事实（已可复现）**：

1. EEZ **有**烘焙能力（源码级）：app.asar 内 `getName("ui_font_", ...)` +
   lv_font_conv 全套参数（size/bpp/no_compress/lcd/lv_fallback/opts_string），
   交给 `new Worker(path.join(__dirname,"lvgl-worker.js"))` 执行。
   工程侧 `embedFonts=True`、`renderingEngine='LVGL'`、fonts[] 11 条 TTF 路径有效，
   `fonts.h` 里 11 条声明也是 EEZ 写的 → **GUI Check and Build 确实产出 ui_font_*.c**。
2. headless CLI `--build-project` **不烘焙**（3 次一致）：删光 11 个 ui_font_*.c
   与 `.eez-project-build` 再 build → 产出 0 个字体、0 报错、2.2s、无 `Extracting font` 日志。
3. **orphan 清理会删字体**（最坑）：EEZ 收尾 unlink「上次清单里有、本次没重写」的文件
   （`s = t.filter(e => !r.has(e))` + `Deleted orphaned file: ${t}`，unlink 失败被 catch 吞）。
   GUI 构建后清单含 11 个字体 → 紧接跑 CLI 打 10 条 `Deleted orphaned file:` 全删；
   CLI 构建后清单不含字体 → 再跑 CLI 不删。缺文件那个 unlink 抛错被吞，所以是 10 不是 11。

**改到的地方**：`design/gen_fonts.py` 头部注释、`design/eez_build.py` 踩坑第 4 条、
`design/all.py` 步骤 4 说明、项目 MEMORY.md（新增「字体到底谁生成」+ 方法论教训）、
kit `skills.md` §3.2 命令行注释 + **新增 §11.12**。

**工作区状态**：实验删掉的字体已由 `gen_fonts.py` 全部重建（11 个），
`.eez-project-build` 现为 CLI 真实清单（不含字体，后续 CLI 不会再删）。

**关联**：PR-0049（User Action 迁移）、skills.md §11.11、§11.12


---

## PR-0051 改用 EEZ Studio 官方生成字体（2026-09-29，用户原则性要求）

**用户要求**：「我不想你使用脚本生成字体，应该使用官方软件生成字体」。

**执行**：把字体产出权交回 EEZ Studio，脚本彻底停止烘焙。

**根因查明（反编译 app.asar）**：`project-editor/store/fonts-cache.js`
```
getFontsCacheFilePath(){ return this.projectStore.filePath + "-fonts-cache" }
async load(){ if (settings.general.cacheFonts) { ...读缓存... } }
```
`cacheFonts=False` → EEZ **不加载任何字体缓存**，只能现场跑 Worker 烘焙；而现场烘焙
这条链在 headless CLI 下不产出（PR-0050 实测 0 个字体 / 0 报错 / 2.2s）。
本工程当时正是 `cacheFonts:False` 且 `test.eez-project-fonts-cache` 不存在。

**改动**：
- `design/json2eez.py`：`ensure_build_settings` 新增 `settings.general.cacheFonts = True`
  （附完整根因注释；保持「ui.json/脚本为真值源」的单向管线，未手改工程）。
- `design/gen_fonts.py`：**重写** —— 删除 lv_font_conv 调用与 NODE/FA_FONT 常量，
  不再生成任何字体；改为 ①校验 `src/ui/ui_font_*.c` 齐全 ②从已生成文件读实测度量
  → `design/font_metrics.json` ③缺失时打印「去 EEZ Studio Check and Build」指引并返回非 0。
- `design/all.py` / `eez_build.py` / `eez_check_build.py`：注释与错误提示同步
  （`eez_check_build.py` 是 CMake 编译前钩子，缺字体直接中断编译）。

**验证**：`json2eez.py` → 工程 `cacheFonts=True`；`eez_build.py` → 0 error、2.1s、
字体未丢（当前清单不含字体，orphan 不触发）；`gen_fonts.py` → 11/11 ok、度量回写、无烘焙。

**待用户执行（GUI 只能人工操作）**：在 EEZ Studio 打开 `test.eez-project`
执行 Check and Build → 官方烘焙字体并写出 `test.eez-project-fonts-cache`；
之后 CLI build 即可直接取官方结果输出字体。**注意**：GUI 构建会重写
`.eez-project-build` 清单使其含字体，紧接着的一次 CLI build 可能把字体当 orphan 删掉
—— 此时回 GUI 再 Build 一次即可，不要用脚本兜底。

**关联**：PR-0050（字体结论纠错）、skills.md §11.12 第 4/5 条


---

## PR-0052 字体官方生成 + 后台自动触发（2026-09-29）

**用户补充要求**：「我就是不想非要我 GUI 编译，而是通过后台触发」。
即：字体仍要 EEZ Studio 官方生成，但**不能要求人去点菜单**。

**先排除的死路（都实测过）**：
- headless CLI `--build-project`：cacheFonts 改 True 后重测，删光字体+清单再 build，
  仍产出 **0 个字体、0 报错、2.3s**，缓存文件也不生成 → CLI 的提取链彻底不工作。
- 单纯「脚本拉起 EEZ Studio 打开工程」：等 **150s**，缓存与字体**均未出现**
  → 打开工程本身不触发烘焙，必须触发 Build 动作。

**可行解（已落地 `design/eez_gui_build.py`）**：
asar 反编译发现主菜单带快捷键
`{label:"Check", accelerator:"CmdOrCtrl+K"}` / `{label:"Build", accelerator:"CmdOrCtrl+B"}`。
于是脚本：拉起 `EEZ Studio.exe <工程>` → PowerShell `Get-Process | MainWindowTitle`
轮询等窗口 → `WScript.Shell.AppActivate(pid)` + `SendKeys("^b")` → 等 ui_font_*.c 落盘
→ `taskkill`。**实测 4 秒生成 11 个字体，全程无人干预。**
坑：① 只发 Ctrl+B，先发 Ctrl+K 会因 Check 结果框挡住后续按键；
    ② 启动前必须 `env.pop("ELECTRON_RUN_AS_NODE")`，否则 Electron 退化成 Node 起不来 GUI。

**接入**：`all.py` 与 `eez_check_build.py`（CMake 编译前钩子）顺序改为
`eez_build(CLI) → eez_gui_build(官方字体) → gen_fonts(校验+度量)`。
脚本默认「字体齐全就跳过」，正常编译不弹窗口；`--force` 强制重跑。

**产物核对**：官方字体比旧脚本烘焙版小 28~80B（头部差异），
**11 个字号实测度量与旧版完全一致** → 布局无需改动。
src/ui：8 个 action、11 条 fonts.h 声明、清单含 11 个字体、screens.c 978KB。

**关联**：PR-0050（字体结论纠错）、PR-0051（改用官方生成）、skills.md §11.12 第 5/6 条

---

## PR-0053 字体方案 C：解包调 EEZ 自带引擎（2026-09-29 定稿）

**诉求**：用户明确选 C ——「解包调 EEZ 自带引擎」。要求：官方引擎产出、
纯后台可触发（不开 GUI）、最好有官方文档依据。

**官方文档核查**：784 页 Reference Guide 对 `headless` / `build-project` /
`command line` / `cacheFonts` / `embedFonts` **零命中**；P11.2 只说字体用
`https://github.com/lvgl/lv_font_conv`。即：**官方没有推荐的命令行字体路径**，
只能自己搭。`useDockerDesktop` 是「full simulator」（Emscripten 仿真），与字体无关。

**结论**：把 app.asar 里的引擎解出来在 Node 里跑。组件：
`build/.../font-extract/lvgl-worker.js` + `node_modules/lv_font_conv`
（freetype wasm 以 base64 内嵌在 ft_render.js，自包含）+ opentype.js / make-error / bit-buffer。
调用：`global.self = ctx` → `require(worker)` → `ctx.onmessage({data:{args,output}})`。
**一个进程连烘 11 个字体约 2 秒**（`ft_render.destroy()` 不影响下一个）。

**结果**：与 EEZ Studio GUI 点 Build 的产物 **11/11 逐字节完全一致**。
清空 src/ui 全部字体后重烘、再跑全链路 `design/all.py`，两次校验均 11/11 一致。
字号度量不变（12/3/9 … 55/12/43），布局无需改动。

**7 个必须踩准的点**（错一个就对不上）：
1. asar 头部 JSON 长度在第 4 个 uint32（offset 16 起），`BASE=16+header_size`
2. C 源码**没被** base64 编码（`String.prototype.toString(enc)` 忽略参数）
3. 主字体 symbols 取顶层 `lvglSymbols`；`lvglGlyphs.symbols` 含 FontAwesome，烘会报错
4. 附加源字段是 `{filePath, lvglRanges, lvglSymbols}`
5. `lv_include` 来自 `settings.build.lvglInclude`
6. `opts_string`：`--symbols` 在 `--range` 前，附加源在 `--format lvgl` 后
7. 落盘后处理：折叠 3+ 换行为 2 个 + 去掉末尾空白（官方产物末尾无换行）

**落地**：新增 `design/eez_font_engine.py`（解包+烘焙+落盘+增量跳过）；
`all.py` / `eez_check_build.py` 顺序改为
`eez_build(CLI) → eez_font_engine(官方引擎) → gen_fonts(校验+度量)`；
**删除** `design/eez_gui_build.py`（旧方案 B，已废）；
`gen_fonts.py` 的缺失指引改为引导跑 `eez_font_engine.py --force`。
引擎缓存 `%LOCALAPPDATA%/eez-font-engine/<hash>`，不污染工程。

**关联**：PR-0050/0051/0052、skills.md §11.12 第 5/6 条

---

## PR-0054 — 「刚生成的脚本要不要进本地知识库」：内核进库，胶水留工程

- **工具**：WorkBuddy　**日期**：2026-09-29　**关联**：PR-0053、skills.md §11.12/§11.13

**诉求**：用户问「刚刚生成的这些脚本是不是也要保留到本地知识经验库中」（问了两遍）。

**冲突点**：工具箱自己的规矩是「工程专属的构建流水线不属于工具箱」，
但「解包 + 调 EEZ 官方引擎烘焙」这件事**并不工程专属** —— 换任何 EEZ 工程都一样能用。
整份拷进库会违反规矩，不拷进来下次又要从零反编译一遍 asar。

**定案（拆两层）**：
- `tools/eez_font_bake.py` = **内核**（工程无关，进库）：
  `find_asar / find_node / extract_engine / ensure_engine / bake / kernel_hash`，
  多平台路径候选 + `EEZ_STUDIO_ASAR` / `EEZ_NODE` 环境变量覆盖，
  `bake()` 只写 out_dir + manifest.json，**不碰任何工程目录**。
- `design/eez_font_engine.py` = **胶水**（工程专属，留在工程）：
  调内核 → 搬到 `src/ui` → 增量状态 `.font_bake_state.json` → 孤儿清理。

**防分叉**：`kernel_hash()` = 内核 `BAKE_JS` 的 sha256，改烘焙行为指纹就变
（本轮 `242c651b…c50af`）。工程侧应 import 内核并校验指纹，**不要复制 BAKE_JS** ——
否则工具箱升级后工程里那份还在跑旧逻辑，且产物看着"正常"，无从发现。

**验收**：`--info` 正确定位本机 asar/node/引擎缓存；独立烘焙 11 个字体全部 OK
（44546 … 446836 B，单字体 100–180 ms）。

**方法论**（值得记住的一条）：判断「代码该放知识库还是工程」时，
别按"是不是这次写的脚本"来分，按**"换一个工程还要不要改"**来分。
要改的留在工程，不用改的抽出来进库 —— 边界划在**可复用性**上，不划在产生时间上。

**关联**：PR-0053、skills.md §11.12 第 6 点「代码分两层」、§11.13 第六节

---

### PR-0055 · 2026-09-29（续 PR-0049/0054） · WorkBuddy
  - 提示词（合并三条）：「这个UI 中按钮触发回调 和 变量，有没有软件设计框架图」／
    「我说的是 触发 user action 和 native 变量 ，具体什么框架，怎么区分仿真器、硬件 ，
    每个文件需要实现什么函数，要详细一点的框图，输出到工程中，另外字库也可以放在工程中，
    不要放在桌面」／「你觉得这个框架好吗，同时这个框架中需要标明哪些是用户添加的代码，
    同时整理到本地经验库中」
  - 诉求：① 给出 UI 回调（User Action）与 native 变量的软件设计框架图；② 详细说明
    仿真器/硬件如何区分、每个文件实现什么函数；③ 框图输出到工程；④ 字库从桌面迁到工程；
    ⑤ 标注框架中哪些代码是用户添加的；⑥ 评价框架好坏；⑦ 整理进本地知识库
  - 产出/结论：工程侧产出 `design/architecture/framework.md`（四层结构 + A/B/C 三条数据流
    + 每文件函数核对清单 + 仿真/硬件切换矩阵 + 字库进工程 + 第 7 节诚实评价）与
    `callback_var_framework.svg`（四条带用颜色区分 EEZ 生成 vs 用户添加 + 图例）；字库
    从桌面迁到 `design/fonts/`（`json2eez.sync_fonts` 强制归一化主字体源，修复半桌面半工程的
    残留）；知识库侧新增 `skills.md §11.14`（四层+归属标记约定+A/B/C 边界纪律+仿真硬件切换
    +扩展4处同步清单+框架评价）与 CHANGELOG v0.8.7。评价要点：框架方向对、隔离干净、
    仿真硬件可互换，但「命令 vs 变量」边界是人肉纪律非机器强制（PR-0049 把 7 个命令型变量
    迁回 A 通道是成熟关键）；最高优先级加固 = 加信号向导+残留符号断言固化进 all.py、输出
    变量 getter 回声与真值回采(走 C)分离
  - 关联：PR-0049（命令迁回 A 通道）、PR-0054（内核/胶水分层）、§11.11、§11.14

## PR-0056 · 2026-09-29/30 · 滑动高亮跟随 + 无线网络下拉浮层 + 自查

- 提示词（原话）：「1、现在UI设计的还不是很好，比如 上下滑动时候，左边的tab没有跟着变动，
  设置界面也是一样 2、点击无线网络时候，可以产生一个下拉窗口，而不是屏幕往下滑，
  下拉时候，将其他选项往下移的效果， 3、我希望有些问题你自己检查」
  （同轮前序补充：「UI中所有按钮和界面点击测试一下，同时按照正常行业页面设计和动画，
  要求好看同时准确」）
- 诉求：① 滑动切 tab 左侧 rail/设置 cats 高亮要跟随；② 无线网络行改弹下拉浮层，
  不推挤其他行；③ AI 自查问题（不要只报告，要自己验证）。
- 产出/结论：① tabview VALUE_CHANGED → native `sync_rail_main/cats`（onTabChange DSL
  新字段）+ **程序切页 animated:false 铁律**（陈旧 SCROLL_END 竞态 P-0029，
  冒烟断言抓到 off-by-one 后修上游 json2eez.py）；② json2eez 新增 onShow/onHide →
  objClearFlag/objAddFlag(HIDDEN)，wifi_dropdown 遮罩+卡片绝对定位零推挤，
  工程 JSON 14 条 HIDDEN 动作（2 show + 12 hide）；③ 自查闭环：grep HIDDEN
  screens.c=0 误判 → 澄清 flow 动作在 eez-flow.cpp 运行时解释 → native printf 插桩 +
  冒烟全量状态 dump 一次定位 → 修复复跑全绿 → 移除临时代码。最终 sim 冒烟
  8/8 断言全过 + G5 11/11 屏平均 8.67%（阈值 25%）。知识库 §11.15 + CHANGELOG v0.8.8
  + intake P-0029。
- 关联：PR-0055、§11.9、§11.10、§11.15、P-0028、P-0029

## PR-0057 · 2026-09-30 · 纯 EEZ flow 重构 + 选型铁律定稿 + 经验入库

- 提示词（原话，按序合并）：
  ①「所以以后明确规定，能够在eez中能实现的动画，不要填写到用户程序中」
  ②「你重新打开，我关闭了」（要求重开交互仿真窗口）
  ③「我测试可以的，你帮我总结一下，后期要求优先输出用EEZ里面控制UI，包括各个控件的
    联动，仅仅控制外部硬件的允许使用用户代码，如果实在没有办法的话，需要通知我，
    同时将当前经验总结到经验库中」
- 诉求：① 定铁律：EEZ 能实现的不进用户程序；② 铁律定稿（EEZ 优先 / 硬件才用户代码 /
  实在没办法先通知）；③ 验收 P-0029 高亮同步 native 方案 → 推翻重做纯 EEZ flow；
  ④ 经验总结进经验库。
- 产出/结论：native `sync_rail_main/cats` 退役，换页高亮同步改**纯 EEZ flow 链**
  （VALUE_CHANGED → objClearState×N + tabviewGetActiveTab→页面局部变量 → @seqout →
  CompareActionComponent(var,i,"=").True → objAddState 第 i 组）；asar 序列化四要点
  实证（assignable 无 Type 后缀 / Compare 结构 / @seqout 传播时机 / localVariables），
  一次通过零试错。回归：6 条 [swipe] 断言全绿（一字未改）+ 11 屏对照 8.59%
  （阈值 25%）；用户交互仿真实测「我测试可以的」。知识库：skills.md §11.17 +
  CHANGELOG v0.9.0 + intake P-0030 + 契约新增选型铁律节；铁律另落项目/用户级
  MEMORY.md 与当日日志。
- 关联：PR-0056、§11.14、§11.15、§11.17、P-0029、P-0030

## PR-0058 · 2026-09-30 · Wi-Fi 扫描/连接状态机：按行业标准落地（hiddenExpr 实战）

- 提示词（原话，按序合并）：
  ①「wifi连接时候应该会有扫描，这个扫描和连接逻辑的UI我看不行，你觉的应该怎么设计」
  ②「先按照行业标准做法来做，你先执行」
  ③（会话续接）「Please continue with the conversation based on the summarized context above」
- 诉求：① 重新设计 Wi-Fi 扫描/连接的 UI 形态与流程；② **按行业标准做法做，直接执行**
  （不要停在方案阶段等确认）；③ 承接被打断的任务 50（native 侧扫描/连接）。
- 产出/结论：**5 态状态机**（`wifi_state` 0 列表(空闲) / 1 扫描中 / 2 连接中 / 3 已连接 /
  4 连接失败）+ `wifi_conn_slot` + 每槽 ssid/sub/rssi/lock，槽位固定 5 个
  （`NET_SLOTS` 与 `APP_WIFI_SLOTS` 两处同步——EEZ 是静态 UI，无法动态生成不定长列表）。
  **UI 侧全部走 EEZ 声明式 `hiddenExpr`**，零用户代码，符合 PR-0057 选型铁律；
  native 只管三条硬件命令 `io_wifi_scan` / `io_wifi_disconnect` / `io_wifi_pick(slot)`。
  工程侧改动：`app_model.h`（APP_IN_COUNT 7→31；字符串缓冲从 `g_in_str[2][48]`
  靠 `(int)id - APP_IN_CLOCK_TEXT` 隐式下标，改为**每个输入 id 一个独立 64B 缓冲**，
  避免加 13 个字符串后改枚举顺序就串位）、`io_iface.h`/`io_pc.cpp`/`io_esp.cpp`、
  `native_actions.cpp` 新增 7 个动作（`wifi_pick_0..4` 用宏生成，函数体只有一行
  `app_set_output`）、`native_vars.cpp` 24 个槽位 getter 用宏生成（不手抄）。
  仿真侧：io_pc 假 Wi-Fi 从「每 5 tick 无脑轮 0/1/2」改为**真流程**（AP_LIST 5 个、
  扫描 2s / 连接 2s、TP-LINK 首次连超时让人看到失败态）+ **`EEZ_SIM_STATE=<n>[,slot]`
  钉态钩子**（`_putenv("")` 刷新 CRT 环境后 getenv 才读得到；`s_pinned` 阻止时间推进覆盖）。
- **四个坑（§11.18）**：① hiddenExpr **禁嵌套括号**（嵌套会落盘成
  `!(!(...))` 导致判定失真 → 互斥控件叠字），要展开成独立条件用 `&&` 串；
  ② **pill 宽度必须 x=0 锚点**：先 `pill(0,0)` 取 w → 反推 `pill_x = rx - w` → 再 shift，
  邻居用 `pill_x` 定位（用 `fw` 反推会算进 pill 内部，`wifi_err` x 702 → 656）；
  ③ 行容器与行内按钮**禁绑同一 action**（事件冒泡发两条命令），改「行纯展示 +
  独立透明热区按钮」且 hiddenExpr 互补；④ 右对齐 `label_right` 飘 1~2px →
  用 `label(rx - tw(text, px), ...)`。另：`·` 类分隔符必须进 `NET_GLYPHS` 预收集字形。
- 验收：`design/all.py --shots` 全绿（EEZ build `No error and no warning`、11 屏出图、
  6 条 `[swipe]` 运行时断言全过）；四态拼版图 `build/sim_shots/09b_wifi_states.png`
  （列表+已连接 / 扫描中 / 连接中 / 失败+重试）逐态核对无叠字。
- 遗留待用户确认：① 槽位数 5 是否够（可改 6/8）② 是否做密码输入面板 + 屏上数字键盘
  ③ 形态用页内三区（已采用）还是弹层 `wifi_pop`。
- 关联：PR-0057（选型铁律）、§11.14（A/B/C 通道）、§11.17、§11.18、P-0031
