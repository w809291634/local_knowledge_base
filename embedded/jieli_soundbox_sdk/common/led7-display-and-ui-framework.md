# 断码显示与 UI 框架：led7 / lcd_seg3x9（杰理 SDK 通用）

> 这块是"自己接一块数码管或断码屏"必须吃透的部分。核心结论：**led7 是纯 GPIO 软件矩阵扫描，不是锁存芯片**；
> UI 层是**表驱动 + 定时器刷新**，不是事件驱动重绘。

## 1. led7 驱动（`cpu/br23/ui_driver/led7/led7_driver.c`，整文件在 `#if TCFG_UI_LED7_ENABLE` 内）

### 脚位模式
`LED7_PIN7 / LED7_PIN12 / LED7_PIN13`（`led7_driver.h:47`）。7 脚 = 4 位数字 + 若干图标共用一套 IO。

### 初始化与平台数据宏
```c
LED7_PLATFORM_DATA_BEGIN(led7_test_data)     // 只展开成 const struct led7_platform_data data = {
    .pin_type = LED7_PIN7,
    .pin_cfg.pin7.pin[0..6] = IO_PORTB_00 … IO_PORTB_06,
LED7_PLATFORM_DATA_END();                    // 展开成 };
void *hd = led7_init(&led7_test_data);       // 返回 LED7_HW (LCD_API*)
```
`led7_init()`（`:664`）做四件事：memset 环境 → **malloc 拷贝一份入参到 `__this->user_data`** →
把全部 IO 置高阻 → `app_timer_led_scan(led7_scan)`。

**⚠ 重复调用 `led7_init` 会漏一次 malloc**（`:672` 不 free 前一份），并且会覆盖板级 init 的结果 ——
本工程把 `users_seg_config()` 放在 `app_bt_task` 里，每次进 BT 模式都重跑一遍 `led7_init`，就是这个代价
（还多一次无效的 `UI_INIT`）。

### 扫描原理（为什么必须 `led7_show_lock`）
`led7_scan()`（`:536`）由 **TIMER2 每 2ms** 调一次：先 `__ui_led7_clear_all()` 全脚高阻消隐（`:493`），
再按 `bShowBuff1[cnt]` 把第 cnt 脚 `hd/hd0=1` **推高作为源**，其余脚 `hd=0` **推低作为漏**，cnt 0..6 轮转。
→ 显示缓冲区是**每 2ms 被重算的**，所以"清空 → 定位 → 显示"这一串动作必须用
`led7_show_lock(1) … led7_show_lock(0)` 包住（`:632` 置 `lock` 位后 `led7_scan` 不再重算缓冲），
否则肉眼可见闪烁。这是接屏最常见的观感问题根因。

段→脚换算在 `__ui_led7_update_bShowbuf1()`（`:398`），顺带用 `jiffies` 半秒判做 500ms 字符/图标闪烁（`:389`）。

### 显示 API 全清单（`led7_driver.c`）

| 接口 | 行 | 说明 |
|---|---|---|
| `led7_show_icon/flash_icon/clear_icon/clear_all_icon` | :89/103/117/132 | 图标位 |
| `led7_setX(x)` | :148 | 只设横坐标，**0..3** |
| `led7_clear_string` / `led7_show_null` | :161 / :177 | 清字符 / 清全部 |
| `led7_show_char` | :197 | **追加**式，超过 4 个自动回 0 |
| `led7_flash_char_start/stop` | :231/246 | 闪烁 |
| `led7_show_string` | :278 | 追加 |
| `led7_show_string_reset_x` | :262 | 从 X 处覆盖 |
| `led7_show_string_align_left/right` | :293 / :307 | 对齐；right **>4 字符直接报错返回** |
| `led7_show_number` / `_number2` / `_number_add` | :334 / :352 / :374 | 高位补 0 / 高位留空 / 追加 |
| `led7_show_lock(en)` | :632 | 见上 |

### 字形与段表在哪（换屏只改这张表）
- 三张段码表：数字 `:44`、大写 `:60`、小写 `:72`。**没有对应字形时用 0x40（显示成 `-`）**。
- `:` 和 `.` **不是字符，是图标位**（`LED7_2POINT` / `LED7_DOT`）——想显示时间冒号要 show_icon 而不是往字符串里塞 `:`。
- 图标枚举：`apps/soundbox/include/ui/led7/led7_driver.h:14-31`（`LED7_PLAY … LED7_WMA`）。
- **段-脚真值表**：`led7_driver_cfg.h`，当前选 `UI_LED7_PIN7_TRUE_TABLE4`（`:12`），
  `led7_digit_seg2pin[28]`（`:223`）+ `led7_icon_seg2pin[]`（`:259`，8 个图标）。
  换一块屏 → 加一张 TABLE 并切宏，不改驱动。
- 段码表/常量可搬 RAM：`#pragma code_seg(".LED_code")/const_seg(".LED_const")`（`:9-10`），
  `TCFG_LED7_RUN_RAM=1` 时链进 RAM（`sdk_ld.c:155-159` vs `:341`）。
  demo 板在"FM 代码跑 RAM"时会把它 `#undef` 强制打开（cfg `:806-808`）——**这个宏会被别的功能改写**。

## 2. UI 框架（`apps/common/ui/led7/led7_ui_api.c`，仅 `CONFIG_UI_STYLE==STYLE_JL_LED7` 编译）

### 界面注册 = 填一张表
```c
const struct ui_dis_api users_led7_main = {
    .ui      = UI_USERS_LED_MENU,   // 必须在 enum ui_menu_main 里有 ID
    .open    = users_open_seg,      // 返回 private
    .ui_main = users_seg_main_menu, // 主界面（每次刷新被调）
    .ui_user = users_seg_subinterface, // 子界面
    .close   = users_close_seg,
};
```
结构体定义 `apps/soundbox/include/ui/style_led7.h:94`；注册方式是把指针塞进 `ui_dis_main[]`（`led7_ui_api.c:50-78`）
+ 在 `enum ui_menu_main`（`style_led7.h:12-25`）加 ID。子界面菜单 ID 在同文件（`:77-78` 例 `MENU_SHOW_NUM_1/2`）。

### 生命周期与初始化链
`led7_ui_init()`（`:422`）→ `clock_add(DEC_UI_CLK)` → `led7_init(private_data)` 拿 `LCD_API*` →
`task_create(ui_task, "ui")`，并用信号量**等 ui_task 起来**。

### 刷新是定时器驱动的，不是脏标记
- `ui_task`（`:379`）pend `os_taskq`，6 种消息：`REFLASH / OTHER / STRICK / MENU_SW / MENU_CLOSE / EXIT`（`:38`）。
- 起一个 `sys_timer_add(NULL, ui_strick_loop, 100)`（`:385`）；`ui_strick_loop`（`:245`）每 100ms 累加，
  达到 `ui_set_auto_reflash(msec)` 设定的份数（**按 `(ms+99)/100` 向上取整**，`:183`）就投 `ui_menu_reflash(0)`，
  回到本线程调 `ui->ui_main()`。
- **主界面刷新周期只能是 100ms 的整数倍**：设 500 → 5 份；设 1100 → 11 份。
- 子界面 `tmp_menu_ret_cnt` 减到 0 时投 `UI_MSG_STRICK` 自动回主页（`:254/364`）。
- `ui_set_tmp_menu(menu, ret_time_ms, arg, timeout_cb)`（`:133`）：`ret_time` 同样按 100ms 取整；
  `timeout_cb` 在页面被打断/切换/关闭时回调（`:272/294/320`）。
- `ui_get_app_menu(0)` = **当前子菜单 ID**，`(1)` = 主界面 ID（`:231`）—— 用它做"界面是否还在"的兜底判断。

### `ui_user` 返回值语义（最容易写反）
`__ui_user_action`（`:303-308`）：**返回 true = 本界面已处理，不再交给公共逻辑**；
**返回 false = 交给 `ui_common()` 统一处理**（实现在 `apps/soundbox/ui/led7/ui_common.c:101`，按 `MENU_*` 分派）。
所以自定义界面里 `default: ret = false;` 是必须的写法。

### 风格切换
`UI_*` 宏按风格切换见 `apps/soundbox/include/ui/ui_api.h:75-129`；另一套 `STYLE_UI_SIMPLE` 用
`apps/common/ui/lcd_simple/` + `apps/soundbox/ui/lcd_simple/my_demo.c` 的 `MENULIST` 菜单表。

## 3. 断码 LCD（`cpu/br23/ui_driver/lcd_seg/lcd_seg3x9_driver.c`）与 led7 的区别

上层是**同一套** `ui_dis_api` / `LCD_API` 与同名 `show_char/string/icon/setX/number`，底层完全不同：

| 项 | led7 | lcd_seg3x9 |
|---|---|---|
| 硬件 | **纯 GPIO 软件矩阵扫描**，任意 7/12/13 只脚 | 片上 **`JL_LCDC`** 硬件，`CON0` 配 bias/vlcd/COM 数、`SEG_IOEN0/1` |
| 谁扫描 | TIMER2 每 2ms 软件轮询 | 32K `wclk` 硬件帧扫描，软件只写 COM/SEG 位 |
| 脚位 | 任意 GPIO | **不可任选**：SEG 只允许 PA0-PA15/PC0/PC1/PB10/PD7/PC6/PC7（`hw_pin2seg_mapping[22]`，`:85`）；COM 只允许 PC0-PC5（`:112`） |
| 位数 | 4 位 | **只有 3 位**（`bCoordinateX>=3` 归零，`:309`） |
| 闪烁 | 半秒判（`jiffies`） | 另用 `sys_timer_add(...,500)`（`:560`） |
| 使能 | `TCFG_UI_LED7_ENABLE` | `TCFG_UI_LCD_SEG3X9_ENABLE`（demo 板注释掉，cfg `:476`） |
| 入口 | `led7_init()` | `lcd_seg3x9_init()`（`:505`） |

→ **选型结论**：想任意分配 IO、位少图标多 → led7；要真断码 LCD 驱动能力且脚位能落进 LCDC 合法集合 → lcd_seg3x9，
但只有 3 位。

## 4. 彩屏 / 点阵 / 其他显示通路

- 彩屏（SPI LCD）走**另一套 window/layer 框架**：`include_lib/system/ui/ui/*.h` +
  `cpu/br23/ui_driver/interface/ui_platform.c` 的 `br23_platform_api`（其刷新定时器也是 `sys_timer_add`，`:590`），
  入口 `lcd_ui_init()`（`apps/common/ui/lcd/lcd_ui_api.c:622`）。驱动有 `spi_lcd_st7735s/st7789v/st7789vw/spi_oled`。
- 彩屏字库：`include_lib/system/ui/font/*.h`、`res/font_ascii.h`；另有 `apps/soundbox/font/`。
- `cpu/br23/ui_driver/LED_1888/`：另一套 12 脚复用推灯，**`ui_set_led()`（`led7_ui_api.c:204`）只对它有效**。
- `apps/soundbox/ui/color_led/`：RGB 灯效（`TCFG_COLORLED_ENABLE`，`color_led_init()` 在 `color_led_app.c:315`）。
- `oled.h` 只有头文件。

## 5. 接一块自己的断码屏的推荐顺序

1. 数一下屏要几只脚、几位数字、几个图标位 → 选 `LED7_PIN7/12/13`；
2. 用万用表/屏资料做**段-脚真值表**，在 `led7_driver_cfg.h` 加一张新 `UI_LED7_PINx_TRUE_TABLEy`，切宏；
3. 用 `LED7_PLATFORM_DATA_BEGIN` 填引脚（**先和 cfg 里其他功能的脚对一遍**，见 `yjt/README.md → ac695n_soundbox` 的冲突表）；
4. `led7_init()` 一次性初始化，**不要在会重复进入的模式任务里调**；
5. 界面按 `struct ui_dis_api` 注册进 `ui_dis_main[]` + 加 `ui_menu_main` ID；
6. 一组显示动作用 `led7_show_lock(1/0)` 包住；
7. 刷新周期按 100ms 整数倍设 `ui_set_auto_reflash`；子界面 `ui_set_tmp_menu` 的保留时间要**大于**你自己的业务节拍
   （例：1000ms 的定时器要配 1100ms 的 ret_time，否则被取整后贴边、界面会提前弹回主页）。
