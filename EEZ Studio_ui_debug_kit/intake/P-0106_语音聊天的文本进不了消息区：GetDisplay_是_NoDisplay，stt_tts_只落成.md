# P-0106 · 语音聊天的文本进不了消息区：GetDisplay 是 NoDisplay，stt/tts 只落成日志（改无锁环每 tick 取一条）

- **工程**：eez-test
- **日期**：2026-10-03
- **工具**：Qoder
- **状态**：fixed
- **标签**：聊天,跨线程,NoDisplay,SetChatMessage,无锁队列,SPSC,PSRAM,P4零阻塞
- **关联提示词**：PR-0159

## 现象（看到什么）

用户报「我和 AI 语音聊天时，对话记录没有实时文字更新」。真机消息区永远只有开机三条种子；喊话、AI 回答全程不出新行

## 复现（怎么稳定重现）

真机：唤醒对话后看消息区行数不变。PC 复现不了「不动」，因为 io_pc 自己会 chat_append（假状态机直写），这正好掩盖了真机缺的那一段 ⇒ 仿真优先铁律要按「同一条路」而非「同一个结果」来镜像

## 根因（真正的原因）

两处断链：① main/board_p4_audio.cc 文件头明写「故意不覆盖 GetDisplay()」，Board::GetDisplay()（board.cc:56）返回 static NoDisplay，于是 application.cc:543-558 把 stt(role=user)/tts sentence_start(role=assistant) 交给 Display::SetChatMessage 后只变成 ESP_LOGW 一行；② 全工程 chat_append 的调用者只有开机种子与 io_pc 假回复，真机零调用者。另：用户否决了「跨线程拿 bsp_display_lock 直调 LVGL」的接法——那会让 LVGL 线程为一行文本睡过去，违反 P4 零阻塞铁律

## 修复（做了什么）

无锁 SPSC 环替代锁：native_actions.cpp 加 chat_q_push/chat_q_pump（8 槽 ×260B，s_q_in 只由生产者写、s_q_out 只由消费者写，RV32 上 32 位对齐读写原子，判满用无符号回绕相减；满则丢最新并 printf 留痕；生产者先写完槽内容最后一步才前移 in）；app_model.cpp user_io_tick() 每 tick chat_q_pump() 取**一条**（用户点单）；板级新增 P4ChatDisplay : NoDisplay 只覆写 SetChatMessage，按 role 转 chat_q_push(from_ai, content)，GetDisplay() 返回它——其余显示调用继续走基类日志实现，屏仍归 EEZ UI；io_pc 的假回复/发送也改走 chat_q_push，让队列本身在仿真里被验到

## 证据（数字 / 命令输出）

design/_device_syntax_check.py：io_esp/native_actions/app_model/native_vars + board_p4_audio.cc = 5 文件 0 错 0 警（含 display.h 与 NoDisplay 继承）。PC --walk=chataudit：日志 [io_pc] AI reply queued(count=4) 紧接 [native] chat +AI: …（证明入队->出队->建气泡三段都走通），气泡尾部「…」截断正常，待机页 m_txt_6=20:29 / m_txt_7=好的，已经为你找到相关的歌单并开始播放了…，该有文字却没文字且可见=0。门禁 all.py --sim = 9 屏 9.87%（与改前一致，队列不改像素）。符号方向：main 的 PRIV_REQUIRES 已含 native（main/CMakeLists.txt:184），main 对象先扫 ⇒ 板级调 native 无 P-0020 那种库顺序风险。真机待烧：内容仍取决于 P-0092（MQTT 8883 不通则云端不回包）

## 沉淀（新增断言 / 案例 / 文档）

app_model.h：chat_q_push 的「单生产者假设」警告（将来接文本输入法会变成第二个生产者，须换 mutex 或分队列）；io_esp io_chat_send TODO 里删掉「回调里加 bsp_display_lock 直调 LVGL」那条旧建议；PSRAM 结论：本 config 未开 SPIRAM_ALLOW_BSS_SEG_EXTERNAL_MEMORY ⇒ 静态数组进不了 PSRAM，且 map 实测 .dram0.bss 81KB/内部段 956KB、剩余约 670KB，2.1KB 队列不值得搬
