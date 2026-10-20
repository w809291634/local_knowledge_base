# P-0163 · WiFi 全流程 UI 的三个 EEZ 实现事实：隐藏表达式 JSON 键名是 hiddenFlag；Textarea 的 text 是 input 单向；字体条目 source 必须全量字体

- **工程**：EEz_stidio_examples/app-wifi-connect
- **日期**：2026-10-20
- **工具**：WorkBuddy
- **状态**：fixed
- **标签**：WiFi,hiddenFlag,hiddenFlagType,textarea,keyboard,native变量桥,动作,字体条目,lv_font_conv,居中,自动演示,假indev
- **关联提示词**：PR-0279

## 现象（看到什么）

①密码面板 hiddenFlag 表达式写了 hiddenExpr 键 → 静默无效，面板盖住全屏吸收点击，行点击全失效；②EEZ GUI 打开工程报 Font "cn14" extraction failed: doesn't have any characters included in range；③连接要读键盘输入的密码但 textarea 的 text 不能绑变量

## 复现（怎么稳定重现）

LVGL 9.4 v3 工程：隐藏控件字段用 hiddenExpr；字体条目 source 指 font-entry-form 的 159 字形子集 TTF 而 lvglRanges 含新文案字符；Textarea 绑 string 变量后开键盘打字

## 根因（真正的原因）

①隐藏表达式在 .eez-project JSON 里的键名是 hiddenFlag（配 hiddenFlagType:/expression/），hiddenExpr 是 build_ui.py DSL 层字段名（P-0080 语义 true=隐藏 不变）——键名写错被静默忽略；②字体条目 source 指子集 TTF，GUI 按 lvglRanges 提取字形时字符不在子集里即报 extraction failed；③LVGLTextareaWidget 的 text 是 makeLvglExpressionProperty("text","string","input") 单向输入，tick 会用变量值覆盖打字内容

## 修复（做了什么）

①JSON 键改 hiddenFlag（tap 后 panel_hidden 1→0 实证生效）；②字体条目 source 指向全量 fonts/simhei.ttf（拷入工程保相对路径 P-0035），.c 仍用 lv_font_conv 按 symbols 子集化（gen_font.py，CLI 构建后跑）；③密码在 wifi_connect 动作里 lv_textarea_get_text(objects.pwd_ta) 读取（objects 全局可见）；Keyboard 的 textarea 属性在 EEZ 里直接指定绑定对象（生成 lv_keyboard_set_textarea）；居中用 text_align:/CENTER/

## 证据（数字 / 命令输出）

panel_hidden=0→修复后随 g_pick 1/0 切换；自动演示日志链 scan done→TAP→pick=1→panel_hidden=0→connect→wifi=1→connected→[DEMO] done；GUI 打开工程字体提取不再报错（source 换全量后）；CLI+PC_SIM 0 错

## 沉淀（新增断言 / 案例 / 文档）

app-wifi-connect/README.md、根 README 索引、workspace memory 2026-10-20

## 补充：逐字审计 + 两条新坑（2026-10-20）

- **逐字审计工具 audit_chars.py**：遍历工程全部 text/placeholder/表达式字符串
  字面量，与字体字符集比对列出缺字（含私有区 U+E000-F8FF 检查）。首跑实抓
  两个豆腐源：`入`（placeholder"输入密码"漏字）+ 私有区 U+F003 锁形占位符
  （改用文本"锁"并入字符集）。改文案/加标签后必跑。
- **新坑：gen_font 顺序**——CLI 重建 src/ui 时孤儿清理会删已烘字体 .c
  （undefined reference to ui_font_cn14），**gen_font 必须在 cli_build 之后**；
  新建 .c 后删 build_rel（file GLOB 不自动重扫）。
- 工作流定稿：build_example → cli_build → audit_chars → gen_font → sim build。

## 补充 2：GUI Run 两处豆腐的定位（textarea placeholder + 表达式 label）

- 截图核对：按钮"连 接/取 消"与顶部"已发现 6 个网络"正常（挂了 cn14），
  豆腐只剩 **textarea 的 placeholder"输入密码"**（textarea 没挂 text_font →
  placeholder 用默认字体渲染）→ 修法：textarea localStyles 也加
  `text_font:"cn14"`（placeholder 用控件字体渲染，别只给 label 挂字体）。
- ★ **placeholder 也要进字体字符集**：placeholder"输入密码"的 `入` 就是首跑
  漏掉的字——audit_chars.py 已覆盖 placeholder 字段。
- ★ GUI Run 的渲染差异：Keyboard 控件在 WASM 预览里可能不渲染（区域空白）；
  表达式 label（记住密码）在 GUI Run 的字体应用与 PC_SIM 不完全一致——
  **中文渲染的最终验收以 PC_SIM 为准**（烘好的字体 .c 已落地），GUI Run
  只验布局；改字体相关配置后在 GUI 里重新 Run 让提取缓存刷新。
- 工作流不变：build_example → cli_build → audit_chars → gen_font →
  （改 build_rel 后）sim build。

## ★ v3：动态列表改为"io 层链表 + C 渲染"（应用户"链表方式表达"需求）

- v2 的 4 槽位变量模式（EEZ 渲染行）退场；新形态：
  **io 层维护 wifi_ap 链表**（ssid/rssi/lock/connected/next，wifi_ap_first/gen 遍历入口）
  + **wifi_ui_sync.cpp**（user_io_tick 每拍调用：gen 变化 → lv_obj_clean(list_box)
  → 遍历链表重建行；行点击回调按索引回链表查节点置 APP_IN_PICK_SSID）。
- EEZ 侧收敛到极简：6 变量 + 4 动作 + 空容器 list_box。
  验证日志：gen=1 建 4 行 → 点行 pick='Office-2G' → 连接后 gen=2 徽标更新。
- 选型定论：**定长数据走变量桥（表达式联动），动态长度数据走 C 渲染**
  （retry-until-success 模式照抄 lvgl_demo_ai 的 ui_data_sync）。
- v3 编译小坑：同目录头用 `#include "app_model.h"` 别写 `../`；C 文件记得
  `<stdio.h>`（printf）与 `<stdint.h>`（intptr_t）。

## ★ PC 真 WiFi 后端（io_win.cpp，Windows WLAN API）——架构通用性实证

- 新增 `platform/io_win.cpp`（`APP_WIFI_REAL` 宏控，默认空编译）+ 
  `run_sim_realwifi.bat`（独立 build_rel_rw + 宏 + 链库）——同一 UI/契约，
  三后端：io_pc 假数据 / io_win 电脑真 WiFi / io_esp 嵌入式。
- 实测：真机扫描 13/12 个真实网络（两次不同=实时），SSID/信号/锁正确渲染，
  list_box 挂 SCROLLABLE 支持超一屏滚动；连接走 WlanSetProfile(WPA2PSK XML) +
  WlanConnect（真连接会切电脑网络，演示默认只扫描）。
- mingw 四坑：①链接库必须在目标文件之后——用
  `-DCMAKE_CXX_STANDARD_LIBRARIES=-lwlanapi` 注入（放前面/环境变量无效）；
  ②头缺 WLAN_AVAILABLE_NETWORK_CONNECTED(0x1)/HAS_PROFILE(0x2) 宏（本地补）；
  ③auth 枚举名 `DOT11_AUTH_ALGO_80211_OPEN`（非 MS 的 dot11_auth_algorithm_none）；
  ④连接参数字段 `strProfile`（非 strProfileName）。
- ★ 自证方法升级：GPU 渲染窗口 BitBlt/PrintWindow 都可能黑屏 → **lv_snapshot
  从 LVGL 帧缓冲出图**（lv_conf 开 LV_USE_SNAPSHOT，include 路径
  "src/others/snapshot/lv_snapshot.h"，注意 apl_lvgl include 根是 LVGL 根目录）。
  截图实抓 UI 静态文案全正常 + 运行期中文 SSID 部分方框（演示字库只含静态文案，
  真机按产品扩字库——预期内）。

## ★ 字库升级：GB2312 标准库子集 7445 字形（解决运行期中文 SSID 豆腐）

- 用户要求"字库参考示例程序，使用标准汉字库，使用一部分"。方案：
  `gb2312_charset()`（Python 'gb2312' 编解码器程序化生成）= GB2312 符号区
  0xA1A1-0xA9FE + 一二级汉字 0xB0A1-0xF7FE = **7445 字形**。
- 产物：ui_font_cn14.c ~5MB 源码（二进制 ~1.2MB @14px bpp4）；
  截图实证：中文 SSID"1号楼6层WiFi"等完整渲染（此前方框）。
- 真机预算：一二级全量 +700~900KB（与 KB 09 号作业卡数字一致）；
  只要一级字库（3755 字，~380KB）改生成器 hi 范围即可。
- lv_font_conv 传 7445 字 symbols：subprocess 列表参数（CreateProcess 32KB 上限内），
  不要走 cmd.exe shell（8191 上限会截断）。
- 真模式加测试钩子：WIFI_AUTOSCAN/WIFI_AUTOEXIT 环境变量（默认关，零自动化不变）。

## ★ 补充：flow 检查错误是非致命的——CLI "ok" 会掩盖表达式引用错变量

- 用户 GUI 构建报 `identifier 'wifi_conn_ssid' is neither input or local or global
  variable`（×2）：v3 变量改名 conn_ssid 时**底部状态表达式漏改**。EEZ 的 flow
  检查错误**不阻断构建**（"2 errors and no warning" 后照样 Build successfully
  finished），产物带坏表达式运行（该 label 永远空/错）。
- 修：cli_build.py 增加守卫——正则抓 `N errors and no warning`，N>0 判
  FLOW_ERRORS 并打印明细行； Renamed wifi_conn_ssid → conn_ssid（3 处）。
- ★ 规矩：**"Build successfully finished" ≠ 0 错误**；CLI 封装必须同时检查
  flow 检查错误计数。变量改名时用全局搜索（build_example.py + 表达式字符串）。

## ★ 补充：字体 extraction failed 的正解 = 按 TTF cmap 过滤字符集

- GUI 报 `doesn't have any characters included in range 0x30fb`：GB2312 符号区的
  ・(U+30FB 间隔号)在 simhei.ttf 的 cmap 里不存在 → EEZ 提取遇"空 range"即报错。
- **正解**：字符集生成后用 fontTools 读 TTF cmap 交集过滤
  （`TTFont.getBestCmap()`，逐字比对，缺字打印并剔除）——build_example.py 的
  `_filter_by_font_cmap()` 已落地（fontTools 缺失时跳过并大声警告，
  跑生成器请用带 fontTools 的 Python——managed env 已装 4.67）。
- 实测：7445 字 GB2312 集过滤后恰好只删 ・ 1 个字；lv_font_conv 侧本来就会
  静默忽略缺字 symbols，所以该过滤只服务于 EEZ GUI 提取。
- ★ 规矩：**自定义字符集 ∩ 字体 cmap 才能进 lvglRanges**——写死字符集换字体
  必炸这条。

## ★ 补充：假模式自动演示修复 + 截图自证闭环

- 截图自证（lv_snapshot）实证：面板"记住密码: 否"/"输入密码" placeholder/
  按钮中文/列表行 SSID+dBm 全部正常渲染——**零豆腐**（GB2312 字库 + cmap
  过滤 + 条目含 ASCII 的组合生效）。
- 修复 1：真模式补丁链误删了假模式的自动扫描块（多轮 replace 改同一段代码
  的事故）→ 已恢复；教训：**多轮补丁改同一函数时，先整段读出再整段重写，
  别叠碎片 replace**。
- 修复 2：演示的"点连接按钮"坐标点击时序偶发抖动 → 改为直接调
  action_wifi_connect（与按钮点击等价：动作只投递，密码取 textarea）。
- 测试钩子定稿（真模式）：WIFI_AUTOSCAN=1（自动扫一次，仅验证）/
  WIFI_AUTOEXIT=1（完成截图退出）；默认全手动。
