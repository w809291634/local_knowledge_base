# P-0119 · 自定义语音命令走 MCP 工具注册：跨线程投环 + AI 忙时压队执行（别在设备端匹配句子）

- **工程**：p4_touch_lcd4_3_exp/lvgl_demo_ai/eez-test
- **日期**：2026-10-08
- **工具**：Qoder
- **状态**：fixed
- **标签**：MCP,语音命令,线程边界,无锁环,AI抢占冲突,tabview切页,仿真载体
- **关联提示词**：PR-0188

## 现象（看到什么）

需求（不是 bug）：想加自定义语音命令，例如说「打开音乐」就切到音乐页并开始播放。问该走哪条路。

## 复现（怎么稳定重现）

design/sim.py 走路脚本 voicecmd：待在对话页 → 把假 AI 态钉成「聆听」→ voice open_music 入队 → 断言命令被压住（AI 页天气卡仍可见）→ 放开成「在线」→ 断言切页成功且已在播放。

## 根因（真正的原因）

两条候选路查清了：①MCP 工具（mcp_server.h:316 GetInstance + :324 AddTool，内建的就是 self.audio_speaker.set_volume 那一套）—— 云端模型按 name+description 自己决定调，设备侧零关键词匹配；②本地离线命令词 —— 这棵 xiaozhi 树里 grep 不到 multinet/esp_mn，要用就得自己引 esp-sr 模型并烘命令词，占 flash/RAM 还和唤醒词抢资源。选 ①。

## 修复（做了什么）

1) 注册点 = 板级 P4AudioBoard::InitializeTools()（构造函数里调）。★ 这不是我发明的位置：xiaozhi 自己在 mcp_server.cc:41 写了约定「Do not add custom tools here. Custom tools must be added in the board's InitializeTools function」—— 照它走就不动 vendored 文件。
2) 工具名 self.media.open_music，描述里把中文说法列出来（打开音乐/播放音乐/放首歌/我想听音乐）。**会不会被调用取决于这段描述**，设备侧不做任何关键词匹配。
3) 回调跑在小智主循环线程 ⇒ 绝不碰 lv_*：投一条进 native_actions.cpp 新增的无锁环 voice_cmd_push / voice_cmd_pump（形状照 chat_q_push，方向反过来；满则丢最新 + 留痕；入队计数最后一步才写）。对外只暴露 voice_cmd_open_music() 一个函数、不传 id —— 省掉「板级和 native 各存一份枚举」这种会走样的同步。
4) ★ 关键冲突：命令到达时 AI 往往正在说「好的，正在为你打开音乐」。这时候执行，会撞上 P-0116 第三轮那条「对话中点播放 = 结束对话」的规则，把 AI 自己的回复掐掉。所以 pump 里判 AI 忙（APP_IN_AI_STATE>=2）就**先压着**，等它空闲再执行；压过 15 秒直接丢弃（云端卡住时不该让命令永远悬着）。
5) 执行 = lv_tabview_set_active(objects.m_main_nav, 1) 切页 + 播放在未播时投 APP_OUT_MUSIC_PLAY_PAUSE —— 走和手指点播放键**同一条命令通道**，不开第二条真值路径。

## 证据（数字 / 命令输出）

走路 voicecmd：基线 m_ai_wx_temp vis=1（在对话页）/ m_np_pause_ic vis=0（没播）→ ai 2 后入队 → 日志「语音命令：AI 正在说话，先压着等它说完」且 wx_temp 仍 vis=1 → ai 1 后 → 「语音命令: 打开音乐（切 tab=mus + 播放）」+「[io_pc] music: 播放」→ wx_temp vis=0（切走了）、pause_ic vis=1（音乐页且正在播）。
★ 载体第一版选错了：用 m_np_play_ic 判「在不在音乐页」，但播放态下它本来就隐藏，vis=0 两种含义混在一起判不出 —— 换成「AI 页天气卡 + 音乐页 pause_ic」双载体才对。
门禁 all.py --sim 9.90%（DSL 一字未改，与上一轮同值 ⇒ 本轮纯管道改动没弄坏静态层）；设备 9 个 native 文件官方命令真编译 0 error；idf.py build rc=0，lvgl_demo_v9.bin 0x4eda90（+1.9KB），38% free。

## 沉淀（新增断言 / 案例 / 文档）

1) 加「语音/远程入口」的正解是**注册能力**，不是匹配句子：MCP 工具的 description 写不清就永远不会被模型选中；反过来，在设备端写关键词匹配等于和云端模型抢活，以后每加一句都要重烧固件。
2) 新入口必须过三道检查：**注册点在哪（别改 vendored 文件）→ 回调在哪个线程（跨线程就投环）→ 和既有优先级规则冲不冲突**。本例第三条最容易被漏：设备已经有「AI 忙时点播放会结束对话」，而这条命令恰恰在 AI 忙时到达 —— 不压队就会自己掐自己。
3) 远程命令要「等本地空闲再执行 + 超时丢弃」，别写成立即执行：立即执行常常和当前正在进行的交互抢资源，而丢弃保证不会永远悬着。
4) 断言载体要能区分两种状态：一个在别的状态下也会变成 0 的对象，不能当「在不在这一页」的证据。


---

## ★ 追加（真机第一轮）：链路是通的，没切页怪我的等待条件 —— `>=2` 把「聆听中」也算成忙

### 真机日志（关键四行）
```
I (63922) StateMachine: State: listening -> speaking
I (63994) user_io_esp: ai state: 2 -> 3 (phase=3 wifi_up=1)
I (64401) Application: << % search_music...
[native] 语音命令：等了 15 秒 AI 还没空闲，丢弃
```

### 两条结论
1. **MCP 链路确认打通**。`等了 15 秒…丢弃` 这行只有在**队列非空**时才会打印
   （`voice_cmd_pump` 第一句就是 `if (s_vq_out == s_vq_in) return;`），
   而真机上唯一的入队点就是工具回调 ⇒ 云端确实调用了 `self.media.open_music`。
   上一轮留的判别问题就此结案。
2. **没切页是压队条件写错**：我判的是 `APP_IN_AI_STATE >= 2`（聆听或回复都算忙）。
   小智连续对话模式下，说完话**回到聆听并长期占着** ⇒ 这个条件永远不满足，
   命令一路压到超时被丢弃。表现就是"云端明明调了工具、屏幕什么也没发生"。

### 修法
只等**真正互斥的那一态**：`== 3`（回复中，TTS 正在播）才让路；`2 聆听中` 立即执行——
聆听不占输出，而且执行时那条「对话中点播放 = 结束对话」的规则正好完成收尾。
超时 15s → 60s（一段长回复也可能几十秒），到点仍丢弃并留日志。
走路 `voicecmd` 现在两段都验：`ai 3` 入队→压住→`ai 1`→执行；`ai 2` 入队→**立即执行**。

### 顺带一条产品侧事实
用户这次说的是歌名「一条街」，云端 agent 走的是它自己的意图 `% search_music...`
（回了一句"没找到叫《一条街》的歌"），**不是我们的设备工具**。
要让设备切页得说动作句（"打开音乐 / 播放音乐 / 放首歌"）—— 这也是工具 description
里要把说法列全的原因：模型是按那句话选工具的。

### 验证
`walk_voice.log`：基线 `m_ai_wx_temp vis=1` → `ai 3` 入队 → 「先压着等它说完」且仍 vis=1 →
`ai 1` → 「语音命令: 打开音乐」+ `music: 播放` → vis=0 / `m_np_pause_ic vis=1`；
回对话页 `ai 2` 入队 → 无"压着"日志、直接执行 → vis=0。
设备 9 个 native 文件 0 error；`idf.py build` rc=0，bin `0x4eda90`，38% free。


---

## ★ 追加（同日）：点歌 —— `self.media.play_song(title)` + `list_music`

### 需求（用户原话）
> 比如我想听什么什么歌时候，可以搜索曲库并播放

### 为什么必须配一个 `list_music`
上一轮真机日志已经演示过后果：用户说歌名「一条街」，模型不知道设备曲库里有什么，
只能走云端自己的意图 `% search_music` 然后回"没找到"。**模型看不见的东西就不会去点。**
所以两个工具配套：
- `self.media.list_music`（无参）→ 返回曲库清单（顿号分隔）；
- `self.media.play_song(title)` → 命中就入队并回"已开始播放《X》"；
  **没命中就把整份清单塞进返回值**，模型下一句能自己改口"没这首，有这些要听哪个"。

### 实现要点
1. 搜索函数放在 **native 侧**（`native_actions.cpp: voice_media_play_by_title`），不放板级：
   这样 PC 仿真也编得到、走路脚本能直接验；板级只写 `AddTool` 和回话文案。
2. 搜索在**调用方线程**（小智主循环）同步做 —— 因为工具回调必须当场回答云端有没有这首歌。
   读的是定长静态表（`app_song_title` 返回数组内的指针，没有可撕裂的指针写），
   最坏是撞上换卡重扫的中间态 ⇒ 少匹配一首，不会崩、不会读野指针。
   **动作仍然投环给 LVGL 线程**（环槽位加了 `idx` 字段），线程纪律没破。
3. 执行走 `APP_OUT_MUSIC_SELECT` = 和"手指点曲库那一行"**同一条命令通道**，
   自带"AI 忙则静默结束对话"和"换曲更新 np_title/np_sub + 进度归零"这一整套，不另开后门。
4. 匹配规则（`media_find_song`）：转小写、去空格、剥 `.mp3/.wav`，然后**互相包含即命中**——
   所以「晚风」命中「晚风心里吹 - 阿梨粤」，「《这条街》」也命中「这条街」，书名号不用特判。
5. DSL 顺带：给歌名/歌手两个 label 补了显式 id（`m_np_title` / `m_np_sub`），
   否则走路只能拿自动名（会随增删控件漂移）断言。

### 验证（走路 voicecmd 扩到三段）
- 压队段：`ai 3` 入队 → 「先压着等它说完」页面不动 → `ai 1` → 切页 + 开播；
- 立即段：`ai 2` 入队 → 无压队日志、直接执行（上一轮 >=2 那个 bug 的回归）；
- 点歌段：`voice list` → 6 条清单；`voice play 晚风` → 命中 #2 →
  `m_np_title = 晚风心里吹`、`m_np_sub = 阿梨粤 · 单曲循环`；
  `voice play 青花瓷` → 没找到 → 日志打出回给云端的清单，且 `m_np_title` 没被动过。
门禁 9.88%（DSL 只加 id）；设备 9 个 native 文件官方命令真编译 0 error；
`idf.py build` rc=0，bin `0x4efae0`（+4.9KB），38% free。

### 只能在真机验的
云端会不会选 `play_song` 这个工具、以及它把歌名抽得干不干净（会不会带《》、带"这首歌"这种废话）。
判据一行：`BoardP4Audio: mcp tool called: self.media.play_song title=...`。
