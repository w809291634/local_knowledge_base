# P-0056 · LVGL 9.4 的 keyboard 按键不在 children 里（`child_count` 恒 0，`key` 走路命令失效）

- **日期**：2026-10-02（PR-0107 / 交互走路器）
- **工具**：WorkBuddy + PC 仿真器（`sim.py --walk`）
- **症状**：走路器 `key a` / `key b` / `key 1` / `key del` 全部回
  `!! key a 没匹配到键盘按钮（键盘上共 0 个键）`，而屏幕上密码面板的键盘画得好好的。
- **根因**：LVGL 9.4 的 `lv_keyboard` 是**内嵌 buttonmatrix**（`struct _lv_keyboard_t
  { lv_buttonmatrix_t btnm; ... }`），按键不是 keyboard 的 child
  —— `lv_obj_get_child_count(pwd_kb)` 恒为 0。顺着试还发现：
  `lv_obj_get_text` 在 9.4 没这个 API；`lv_keyboard_get_btn_text`（老写法）只吃
  `btn_id`(uint32) 不吃对象；`LV_KEYBOARD_OK/DEL` 这两个宏 9.4 里根本不存在
  （键盘文字是字面量 "OK" / `LV_SYMBOL_BACKSPACE` 图标）。
  能拿文本的只有 `lv_keyboard_get_button_text(kb, btn_id)`，而 **btn 按创建顺序
  进 buttonmatrix 的 children 索引**，所以遍历 children 的下标 == btn_id。
- **规则**：
  1. 走路器/自动化别用「点 children 找按键」那一套（在 9.x keyboard 上必然 0 个）。
  2. 要验证「输密码」这种路径：先用 `text <obj> <str>` 往 textarea 灌字
     （验证 passwordMode 回显），要真点键盘就 `tree <kb> 2` 量出单元格矩形再 `tapxy`。
  3. 量坐标时注意 P-0055：LVGL 键盘每帧被 `lv_keyboard` 构造函数重排，
     DSL 坐标 ≠ 屏幕坐标。
- **状态**：fixed（`key` 命令保留但文档写清失效原因；`text` 成为输密码主路径）
