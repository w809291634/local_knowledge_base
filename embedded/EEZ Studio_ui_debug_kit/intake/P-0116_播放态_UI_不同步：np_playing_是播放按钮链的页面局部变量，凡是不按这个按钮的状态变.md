# P-0116 · 播放态 UI 不同步：np_playing 是播放按钮链的页面局部变量，凡是不按这个按钮的状态变化必然错相

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_ai/eez-test
- **日期**：2026-10-06
- **工具**：Qoder
- **状态**：fixed
- **标签**：EEZ,变量绑定,音乐播放,仿真走路,所有权
- **关联提示词**：PR-0179,PR-0180

## 现象（看到什么）

真机播放器已经能出声、AI 唤醒时也能让路，但正在播放页的播放/暂停图标与唱片律动和真实播放状态不同步：点曲库行直接开播、一首放完自动下一首、AI 让路后续播、SD 卡被换/曲表重扫这几条路都不经过播放按钮，图标就一直停在旧态。PC 仿真走路 npplay 同样复现（点曲库行后 m_np_play_ic/m_np_pause_ic 可见性不变）。

## 复现（怎么稳定重现）

python design/sim.py --walk=npplay —— tap nav_music → gettext 两枚图标 → tap m_np_play_btn ×2 → tab mus 1 → tapxy 400 250（点第 3 行）→ tab mus 0 → gettext 两枚图标。修复前第 ③ 段没有任何变化。

## 根因（真正的原因）

np_playing 是 EEZ **页面局部变量**（design/json2eez.py 的 local_vars），唯一的写者是播放按钮CLICKED 上挂的 SetVariable(np_playing = 1 - np_playing)。真值在播放任务的 s_playing（io_music_player.cpp:205 只有解码器开成功才置 1），UI 从没读过它一次 ⇒ 凡是「不按这个按钮」引起的状态变化必然错相：点曲库行开播（io_esp.cpp:1331 io_music_select→music_start_current）、自动下一首（io_esp.cpp:1045 music_advance_after_finish）、AI 让路（播放器淡出冻结、s_playing 不动）、换卡重扫（io_music_rescan→music_stop）。违反 skills.md §11.21/§11.22：显示用的变量和真值不是同一块内存，UI 自己当状态机。

## 修复（做了什么）

把 np_playing 升成 native 输入变量，UI 只读：
1) src/native/app_model.h 新增 APP_IN_NP_PLAYING；native_vars.cpp 加 get_var_np_playing()（转 app_get_input_i）+ set_var_np_playing()（空实现，UI 不许写）；
2) io_esp.cpp:795 每拍发布 s_playing（用户意图）&& io_music_player_playing()（真在播）——AI 让路期间仍是 1，图标不会被一次对话打断成「暂停」（那是假象）；
3) io_pc.cpp:521 同点位发布 s_pc_playing，PC 只镜像通路不镜像结果；同时 io_music_select 补 s_pc_playing=1，与真机「点行即播」同语义（原来两端不一致）；
4) json2eez.py npAnim 律动链：链首 SetVariable 删掉，改成 CLICKED→music_play_cmd→Delay(80ms)→IsTrue(np_playing)→循环，循环体每帧再读一次 ⇒ 停/起都跟真值；80ms 那一拍是必需的：命令要等 native tick 才回推，链首立刻读会读到旧值走 False 分支。
5) 顺带（同族）：io_music_player.cpp 加 s_cur_idx（开成功才记号，停/放完/失败回 -1）+ io_music_player_index()，C9 停止与播放请求同帧到达时先落停止再补投播放。

## 证据（数字 / 命令输出）

①仿真走路 build/walk_npplay.log：播放中 imgrot 536→1206（在转），暂停后 0→0（冻住）；三条路径图标全对，其中 ③「点曲库行、全程没按播放键」→ 曲库选中第 2 首 → music: #2 → play_ic vis=0 / pause_ic vis=1；截图 25_p4_selected_playing.png 上歌名/歌手/进度/暂停键全对齐。
②门禁 design/all.py --sim：有效对比 9 屏，平均明显差异 9.93%（阈值 25%），无缺屏。
③设备侧官方逐文件编译 design/_verify_weather.py：8 个 native 文件全 OK（含新加的 io_music_player.cpp），0 error 0 warning。
④idf.py build：Project build complete，lvgl_demo_v9.bin 0x4ec1f0，最小 app 分区 0x800000，38% free；3 条 warning 全是 cc1plus 对 C 专用选项的老噪音。

## 沉淀（新增断言 / 案例 / 文档）

1) 显示态变量的唯一写者必须是**持有真值的那一侧**。EEZ 页面局部变量当状态机，只在「它自己那个控件触发」时才对；真值一旦有多个变更源（按钮之外还有列表、自动换歌、外部让路、重扫），就必然错相 —— 这类「UI 不同步」不是刷新时机问题，是**所有权问题**。
2) 律动/动画链同理：链首只**发命令**，读回真值再决定循环启停；发完命令要留一拍（本例 Delay 80ms）等 native 回推，否则读到旧值。
3) 走路器按屏幕坐标点击必须复用内核自己的命中函数 lv_indev_search_obj，并按 pointer_search_obj（lv_indev.c:1597）的顺序搜 sys→top→act_scr→bottom 四层。自己拼「对象表+一层子对象」的平面候选池有三处必错：运行期建的控件（lv_list 行）压根不在表里、候选池上限静默截断、父链累加坐标不看 tabview/列表滚动偏移 —— 而且打偏了照样打印「命中」，不自证就会把工具问题当成产品问题追。
4) EEZ 对 image 控件的 SET_PROPERTY angle 走的是 lv_image_set_rotation（存在图像描述符里），不是样式 transform_rotation。探针读错来源会恒报 0，把「动画在跑」误判成「动画没跑」；验动画要先确认属性落在哪个存储上。
5) Windows 上 subprocess 管道文本模式默认按系统码（GBK）解子进程输出：中文日志会先变乱码，再在 print 时被 GBK 编码器拒掉（UnicodeEncodeError: 'gbk' codec can't encode '\ufffd'），整条走路半途失败。capture_output + text 的调用一律钉 encoding="utf-8"。


## ★ 追加更正（同一轮内，登记时引错条款）

「根因」段末写的"违反 §11.21/§11.22"里 **§11.22 引错**：那一条是"借 compile_commands.json 做真编译取证的硬规矩"，与本题无关。
正确的引用是 **§11.21（绑变量控件 get/set 必须同内存）+ 本轮新增的 §11.26（状态显示的所有权：写者只能是持有真值的那一侧）**。
原文不改写，按追加式纪律在此更正。


---

## ★ 追加更正（2026-10-06 第二轮：产品口径由用户改掉，上面「让路仍算在播」的判断作废）

### 用户原话（逐字）

> 现在逻辑还是不对，我要求 播放音乐时候，可以被 语音唤醒 给 暂停掉，并且动画 UI 要求和 音乐播放的 暂停状态一致，
> 而不是 明明已经切换到 AI 对话，但是 播放器的UI 界面中 还是转动，同时当语音退出时候，如果需要再次播放音乐，
> 应该需要再次点击播放按钮 ，而不是像现在这样直接返回播放音乐

### 我错在哪

「AI 让路期间播放器仍算在播、说完自动续」这条**不是用户定的，是我替产品定的**（还写进了本条「修复」段第 3 点
和 skills.md §11.26 第 3 条）。让路（duck / 淡出冻结）和暂停（stop）是两个语义，"打断结束后要不要自动恢复"
更是纯产品选择 —— 该问的没问。

### 改后的规则（真机 io_esp.cpp / PC io_pc.cpp 同一条）

```c
if ((s_ai_state == 2 || s_ai_state == 3) && s_playing) music_stop();   /* 电平触发 */
```

- 不需要边沿跟踪"什么时候进的聆听"：`music_stop()` 同步清掉意图 `s_playing`，下一拍条件自然不成立。
- 图标与唱片律动**不用另改一行** —— A 组已经把 `np_playing` 收成 `意图 && 真在播` 单源，
  意图被清 ⇒ `play_ic` 立刻可见、npAnim 循环体 `IsTrue(np_playing)` 走到 False 分支复位（唱片停转、波纹归位）。
  这正是"动画 UI 和暂停状态一致"的落点。
- 退出对话（3→1）后没有任何东西把意图置回 1 ⇒ 必须再点播放键（`io_music_play_pause`）。
- 延迟：`ai_state_tick()` 一轮 200ms + 一拍发布 ≤ ~0.25s；播放器内部那条 `app_music_out_allowed()`
  淡出保留，负责抢占瞬间的声音，不再承担暂停语义。
- 配套工具：新增走路命令 `ai <0..3|off>`（落点 `io_pc_ai_pin`，`extern "C"`，不进 `io_iface.h`）；
  `npplay` 开头钉 `ai 1` 才不会被抢占规则打断成随机结果；新增 `npyield` 一支专验本规则。

### 证据

`build/walk_npyield.log`：y0 播放中 `pause_ic vis=1` + `imgrot 536→1139`（在转）→ `ai 2` 打印
`[io_pc] AI 抢占 -> 音乐暂停（不自动续播，需再点播放）` → y1 `play_ic vis=1` + `imgrot 0→0`（冻住）→
`ai 1` 退出 → y2 仍 `play_ic vis=1` + `imgrot 0→0`（**没有自动续播**）→ 点播放键 → y3 `pause_ic vis=1`。
截图 `build/sim_shots/walk_npyield/19_y1_ai_paused.png`：状态栏「聆听中…」，播放器是 ▶（暂停态）、唱片静止。
门禁 `all.py --sim` 平均明显差异 9.95% 无缺屏；设备 8 个 native 文件官方命令真编译 0 error；
`idf.py build` rc=0，`lvgl_demo_v9.bin 0x4ec2c0`，38% free。

### 这一改带来的两个新已知点（未动，等点单）

1. **AI 占用期间按播放键**：会"闪一帧播放再回暂停"（电平触发的必然结果；命令在 tick 的排空阶段落地，
   下一拍采样阶段就被清掉）。要不要在聆听/回复态把播放键置灰或忽略，是产品选择。
2. `io_music_player_play/stop/mute` 用 `xSemaphoreTake(s_lock, portMAX_DELAY)`，而调用点在 LVGL 线程
   ⇒ 形式上违反 P4 零阻塞铁律。实测锁内只拷一个请求结构（微秒级），风险低，但按规矩应换成有界取锁 + 失败丢弃。
