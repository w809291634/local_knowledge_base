# P-0114 · 天气地点做成可收藏多城：位图存 NVS + 12 颗 CHECKABLE 胶囊浮层 + 多城一次 HTTPS 请求

- **工程**：eez-test
- **日期**：2026-10-04
- **工具**：Qoder
- **状态**：fixed
- **标签**：天气,多选,NVS,位图,CHECKABLE,checkedState,表达式无位运算,浮层遮罩,Open-Meteo多城,父边界门禁,链接期缺setter
- **关联提示词**：PR-0175,PR-0176

## 现象（看到什么）

P-0113 的天气卡只能看固定一城（北京）。用户要：城市在设置里可选、要存 NVS、默认武汉；进一步澄清为「列表里多种城市、勾选其中几个、主页卡片周期翻转显示、手动切城时重置翻转计时」。

## 复现（怎么稳定重现）

设置 → 显示与音量 → 天气地点 → 弹浮层勾 4 城 → 完成；待机页天气卡显示第 0 城；再勾第 5 城必须被拒并在下一帧弹回未勾选；重启后勾选状态必须还在（NVS）。

## 根因（真正的原因）

不是 bug，是三条能力边界要绕：①**EEZ 表达式引擎没有位运算**（json2eez.py:357 只实证 == != < > <= >= && ||）⇒ 一个 mask 变量喂不了 12 个勾选态，必须一位一个 bool 视图变量；②浮层必须垫全尺寸遮罩，否则横滑穿透到 tabview pager（P3⑥ 老坑）；③收藏上限只能在**写侧**守（set_var 里拒绝），不能指望 UI 禁用 —— 靠 EEZ 每帧把变量推回 CHECKED 实现『点不动自己弹回』。

## 修复（做了什么）

g_set 加 wx_mask(u16 位图) + NVS 键 wxmsk（load 时按表长截位、按上限裁数）；io_weather 拆成『两端共用的城市表/收藏工具』+『#if ESP_PLATFORM 的抓取半截』，12 城表下标即位号；抓取改成**一次请求带逗号列表**（Open-Meteo 的 latitude/longitude 支持多值，返回 current 数组，单城时是对象 ⇒ 两种形状都解析），WX_BODY_MAX 896→4096；工作任务每拍比 g_set.wx_mask，变了 ≤5s 内重抓（不等 15 分钟周期）；native_vars 用宏生成 12 对 wx_sel_N（get/set 读写同一个位，满 4 城时写侧直接 return）+ wx_city_text 摘要 getter 现算；UI 侧 12 颗 CHECKABLE 胶囊 stateVar=wx_sel_N（复用 P3⑤ 随机/循环那套双向绑定），行按钮/遮罩/完成走 onClick setVar，零新增 native action；11px 明细档补 12 城用字（13px 有 GB2312 全量兜底）。

## 证据（数字 / 命令输出）

三级：①design/_verify_weather.py 用**各自官方编译命令**跑 6 个 native 文件全 rc=0/0 错/0 警；②PC 门禁 all.py --sim rc=0、9 屏 9.91% 无缺屏；走路器新增 wxcity（37 步）实测：摘要 『武汉』→ 勾两城关浮层后『武汉·北京·上海』→ 待机页明细『武汉 · 体感 26° · 湿度 45%』→ 再勾广州+深圳后摘要『武汉·北京·上海 +1』，且截图 33_w5_capped.png 里**深圳显示为未勾选**（= 写侧拒绝 + tick 回推 CHECKED 双向都真跑通，不是只看着亮）；对象表 606 条 / 上限 1600 未溢出；③idf.py build rc=0，lvgl_demo_v9.bin 0x4CC540（≈5.05MB）/ app 分区 8MB ⇒ 空闲 40%。★ 过程中被抓到两处：json2eez 父边界门禁拦下『子[11] 下边缘 128 超出父高 124』（我按 480 高估了 c3 的 124 实际可用高，收 8px 行距解决）；目检抓到『完成』按钮与第 4 行南京胶囊重叠（面板 268→292 高、label 改 label_cmid 居中）。另有一处链接期真错：EEZ 给每个 native 变量都生成 get+set 引用，我漏实现 wx_edit_shown ⇒ undefined reference（纯 UI 内部状态也要槽位 + 双向实现）。

## 沉淀（新增断言 / 案例 / 文档）

通则一：**纯 UI 内部状态变量也必须有 APP_IN_* 槽 + get/set 双实现**，少一个就是链接期炸（notif_filter / wifi_forget_shown 是现成范式）。通则二：**CHECKABLE 走路必须用 toggle（RELEASED），tap 不翻状态**（P-0046），否则『点了没反应』会被当成通过。通则三：验证『上限被守住』不能只看摘要数字，要看那颗胶囊**弹回未勾选** —— 这才是双向绑定生效的功能证据。另：城市名单两处（build_ui.py 的 WX_CITY_NAMES 与 io_weather.cpp 的 WX_CITY[]）必须同序同字，已加 assert + 注释把口径钉住，11px 白名单由名单 join 生成，避免漏字。

## ★ 批2 追加（同轮）：卡片 ‹ › 手动翻 + 8 秒自动翻，翻转态**不进 NVS**

用户口径：「会在主页中显示，可以周期翻转，也可以手动滑动选择，每次滑动时候，会重置自动翻转的时间」
⇒ 手动机制选甲（卡内 ‹ ›，不与外层 tabview 的横滑抢手势），间隔 8 秒，收藏上限 4 城。

做法：`io_weather` 的**两端共用半截**里加显示态 `s_view` + `s_flip_at_ms` 与三个函数
（`io_weather_view / _step / _tick`），真机 `io_weather_publish()` 与 PC `pc_weather_publish()`
都改成"先 tick 再取第 view 城"⇒ 同一套翻转逻辑两边真跑同一份代码，不是 PC 演一遍真机演一遍。
卡片右上角两颗 24px 圆钮 → `action_wx_view_prev/next` → `io_weather_view_step(±1)`（内部重置计时）；
User Action 从 32 增到 34。

三条口径值得记：
1. **`view` 存"已收藏列表里的位置"而不是城市下标** —— 取消勾选中间某城时后面自动补位，
   不会翻到空城；`view >= n` 时夹回 `n-1`。
2. **翻转/轮播这类显示态不进 `g_set`、不进 NVS**：它每 8 秒就变一次，进表 = 每 8 秒写一次 Flash
   （实打实的磨损，且 `app_settings_tick` 的 memcmp 去抖对"周期性变化"完全无效）。
   所以它是 io_weather 的私有 static，表里只留真正要记的 `wx_mask`。
3. **计时用 `lv_tick_get()` + 有符号回绕比较**（`(int32_t)(now - due) < 0` 判未到点），
   P-0097 那条"用墙上时间导致对时一跳就熄屏/翻转错乱"的坑不再踩；收藏 <2 城时既不翻也不立基准。

验证（数字）：走路 `wxcity` 扩到 50 步，断言写法刻意**不比城市名、只比变化**
（A → 点 › → B 必须不同 → 点 ‹ → 必须回到 A → 静置 8.6s → 必须又变）——
因为走路本身耗掉十几秒，自动翻转随时插进来，认死城市名会假失败。
实测：`北京·体感21°·湿度43%` → `上海·22°/46%` → `北京` → (8.6s) → `上海` ⇒ 手动两向 + 自动翻转全中。
目检 `40_w6_view_a.png`：箭头在卡片右上角（文字块垂直居中，顶边 y0+45；箭头 y0+8..32）与两行文字零碰撞。
门禁 `all.py --sim` rc=0、9 屏 **9.93%** 无缺屏；6 个 native 文件官方命令 0 错 0 警；
`idf.py build` rc=0，`lvgl_demo_v9.bin = 0x4CCAB0`（≈5.05MB）/ 8MB ⇒ **空闲 40%**。

⇒ 新断言（进 skills 的那类通则）：**轮播/翻转这类高频变化的显示态不要塞进设置表和 NVS**，
统一表只收"用户会去调、且要跨重启保留"的项；否则 memcmp 去抖形同虚设，Flash 每几秒被写一次。


## ★★★ 批3 追加（同轮）：手势 + 翻转动效，以及"不获取数据"的两个真因

用户报「天气好像后期加载后，不会获取数据了」+ 要「手势滑动选城、有切换效果、可以 3D 滚动」。

### 根因一：接口形状我照记忆写错了（硬证据 = 当场抓一次）
我以为多地点是 `{"current":[{..},{..}]}`，实测顶层是**数组**、每个元素各自带 `current` **对象**：
```
[{"latitude":30.61,"current":{"temperature_2m":21.7,...}},
 {"latitude":39.89,"location_id":1,"current":{...}}]
```
⇒ `cJSON_GetObjectItemCaseSensitive(root,"current")` 在数组上返回 NULL ⇒ **勾 ≥2 城永远解析失败**，
单城（默认武汉）正常 —— 与"后来才不获取"完全对得上（用户刚勾了多城）。
已改成两条路径：顶层数组 ⇒ 逐元素取各自 `current`；顶层对象 ⇒ 单城。数组顺序实测 == 请求顺序。

### 根因二：退避游标只在成功时更新 ⇒ 失败后每 5 秒一次 TLS 握手
`changed = (want != s_fetched_mask)` 而 `s_fetched_mask` 只在成功时写 ⇒ 一旦从未成功过，
`changed` 恒真，60 秒退避被完全绕过。两个 bug 叠在一起才表现为"彻底不上数据 + 疑似限流"。
⇒ 改成 `s_attempted_mask`：**记尝试不记成功**，失败老实等 60 秒；用户再改勾会把 changed 拉回真、立刻重试。

### 批3 手势与动效（用户选甲）
- 卡内横滑：PRESSED 记点 + 摘掉祖先链的 `SCROLLABLE`（LVGL 是在**移动时**沿链找可滚容器，
  所以按下这一刻摘掉就来得及），RELEASED 算 `|dx|>=34 且 |dx|>|dy|` → `io_weather_view_step(±1)`，
  抬手恢复。⇒ 卡片上滑 = 换城，卡片外滑 = 照旧换页；`‹ ›` 保留。
- 动效：`lv_anim` 260ms，绕"进入侧那条竖边"当轴（pivot 放左/右缘）从 ±12° 转回 0° + 缩放 70%→100% +
  透明度 90→255；`completed_cb` 里把三个样式值显式归零，不留残变换。
  触发点是"这一拍发布的城市变了"（`io_weather_view_pulse()` 返回方向），真机与 PC 的 publish 都调
  ⇒ 自动翻 / `‹ ›` / 手势三条路共用同一个动效，不各写一遍。
- ★ 踩点记录：`PAGE_ROLES` 按位置分配的 id **不进 objects 表**（实测 screens.h 里没有 `m_ai_weather_card`），
  必须给节点显式 `id=` 才能被 native 拿到 —— 手势监听挂不上时先查这个。
- ★ `lv_obj_set_style_opa_layer` 不存在，本工程 LVGL 9 是 `opa_layered`（setter/getter 都查了
  `lv_obj_style_gen.h` 才写）；`lv_abs` 也不赌在哪个头里，本地宏。

### 验证（动效不能用截图断言）
走路器新增 `getrot <obj>` 读 `transform_rotation / transform_scale_x / opa_layered`：
换城后 80ms 采到 `rot=-50 scale=219 opa=179`，播完采到 `rot=0 scale=255 opa=255` ⇒ 在跑且归零。
（同一步的 `shot` 图看着"没倾斜"是因为 shot 之前又泵了几帧、260ms 早播完 —— 截图不能验短动效。）
门禁 rc=0、9 屏 9.92% 无缺屏；6 个 native 文件官方命令 0 错 0 警；`idf.py build` rc=0，
`bin 0x4CD170` / 8MB 分区空闲 40%。
LVGL 9 的 transform 会把"对象+子树"画进 ARGB 中间层再整体变换（`lv_refr.c` 的
`lv_obj_redraw(new_layer, obj)` → `lv_draw_layer(...)`）⇒ 容器带动效会带着子控件一起动；
代价是那张中间层（290×128 ≈ 148KB/帧），**短时可用、别常驻**，真机若嫌重就调
`WX_ANIM_MS` / `WX_TILT_DEG` 两个宏。

