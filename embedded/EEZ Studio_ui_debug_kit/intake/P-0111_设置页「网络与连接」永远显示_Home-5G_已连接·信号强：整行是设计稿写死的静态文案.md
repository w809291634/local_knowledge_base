# P-0111 · 设置页「网络与连接」永远显示 Home-5G / 已连接·信号强：整行是设计稿写死的静态文案

- **工程**：eez-test
- **日期**：2026-10-04
- **工具**：Qoder
- **状态**：fixed
- **标签**：静态文案,假反馈,WiFi,绑定,glyphs,snprintf,stdio
- **关联提示词**：PR-0171

## 现象（看到什么）

用户报「网络与连接中，界面一直显示 HOME-5G，不同步」。截图实证：该行 sub=「已连接 · 信号强」、右侧=「Home-5G」，与真实连接无关（真机连别的 AP 也照显示）

## 复现（怎么稳定重现）

PC 与真机都一样：开机不进 Wi-Fi 浮层，只看设置主页第一行；改连任何网络，那行文字都不动

## 根因（真正的原因）

build_ui.py:1475 的 items 表把 sub 与右侧文字写成字面量（设计稿时代的占位），既没绑变量、native 也没有对应发布路径 ⇒ 纯静态装饰。同类问题此前已在待机页「最近对话」发生过（P-0100），这是第二例。附带查出两个真缺口：① 真机 io_esp 从不置 wifi_state=4、也从不发布 APP_IN_WIFI_ERR ⇒ 设备上永远看不到连接失败与原因（只有 PC 会演 连接超时，两边行为不一致）；② PC 的 wifi_level 是 (t_now/12)%3 每 12 秒轮换的假信号档

## 修复（做了什么）

新增 native 字符串变量 wifi_row_text，由 get_var_wifi_row_text() 现算：读 APP_IN_WIFI_STATE / CONN_SSID / LEVEL / ERR 四个现成输入，拼成「SSID · 已连接 · 信号中」/「扫描中…」「连接中…」「连接失败+原因」「未连接」。按 P-0110 的教训，绑变量的 label 每帧读 getter，读实时状态就不存在慢一拍；再走 io算好→写模型槽→UI读槽 反而多一级会忘发布的缓存。DSL 侧：该行 sub 改 text=None + var=wifi_row_text + glyphs=WIFI_ROW_GLYPHS + id=wifi_status（生成名 m_set_wifi_status），右侧静态文字删除只留箭头。顺带修 native_vars.cpp 缺 include stdio.h（设备侧靠 lvgl.h 间接带进来，PC 的 clang 直接报 snprintf was not declared）

## 证据（数字 / 命令输出）

目检 build/sim_shots/07_settings.png：该行显示「HomeNet-5G · 已连接 · 信号中」（PC 假状态），写死的 Home-5G 已消失。门禁 all.py --sim = 9 屏 9.92%（07 设置主页 6.71%→6.74%，假文案换真值的合法上涨，见 P-0104）；_glyph_lint（venv 解释器）= DSL 可种 6863 码位、运行时中文全覆盖 OK；真编译 4 文件 0 错 0 警

## 沉淀（新增断言 / 案例 / 文档）

P-0100 的同类第二例 ⇒ 通则：设计稿里的状态类文案（已连接/在线/信号强/电量）一律不许留字面量，要么绑变量要么删。待办两项：真机补 wifi 失败态与原因（需 WifiManager 超时/密码错事件）；PC 假 wifi_level 轮换要在注释里注明只在仿真存在
