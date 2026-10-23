# P-0181 · 图标位图红蓝通道反了 + 全仓库共用一个 main.exe，两个"看起来通过"的假象

- **工程**：EEz_stidio_examples\watch-app-list-rxroller_no_flow_2
- **日期**：2026-10-23
- **工具**：Qoder
- **状态**：fixed
- **标签**：ARGB8888,字节序,PIL,通道互换,共享构建产物,exe覆盖,身份核对,退出码
- **关联提示词**：PR-0340

## 现象（看到什么）

① 给 `gen_assets.py` 加"反解产物"核对后第一次就报：设计底色 `#C2ED3C`，从生成的 `.c` 里读回来是
`#3CEDC2` —— R 与 B 恰好互换。22 行那版用随机调色板，红蓝互换肉眼看不出来，所以一直没暴露。
② 同一份 `_2` 全量重编后跑 `WATCH_AUTOTEST`，输出 `rows=14 pitch=92 edge=151/255`（本工程是
120/226），再跑一次变成 `rc=2 ASSERT=0`，`shots/` 里混进 23 张 466×466 的别的项目截图。

## 复现（怎么稳定重现）

① `python design/gen_assets.py && python design/decode_icons.py`
② 两个工程各自 `run_sim.bat` 交替构建（它们把 exe 链到同一个
`PC_SIM/lv_port_pc_vscode_v9.5/bin/main.exe`），中间隔一次别人的链接即可复现。

## 根因（真正的原因）

① LVGL 的 `LV_COLOR_FORMAT_ARGB8888` 是小端 `uint32 0xAARRGGBB`，**内存字节序 B,G,R,A**；
PIL `img.tobytes()` 对 RGBA 图给的是 **R,G,B,A**。原代码 `px = img.tobytes()` 上面那行注释
"RGBA -> 内存序 B,G,R,A" 描述的是一个**并没有发生的转换**。
② PC_SIM 的输出路径固定，`SIM_TARGET_PROJ_DIR` 只决定"编进去的是谁的源码"。
构建与运行之间只要隔了别人的一次链接，跑的就是别人的二进制 —— **mtime 看不出来**（只差一两秒）。
而且夹具 `expect()` 不计数、`WATCH_AUTOEXIT` 一律 `exit(0)`，所以"零条断言"和"全部通过"
在退出码上长得一模一样。

## 修复（做了什么）

① `emit_icon()` 先 `Image.merge("RGBA", (b, g, r, a))` 再 `tobytes()`。
② 夹具第一条断言改成**身份核对**（`watch_list_row_pitch()` 必须等于 config 的 `ROW_PITCH`），
身份不对则后面全部作废；`expect()` 统计 FAIL 数，退出码 `exit(s_assert_fails ? 1 : 0)`；
验证时把 `ninja && 运行` 写进同一条命令，不给中间插队留窗口；截图转换加"尺寸不是 410×502 就跳过"。

## 证据（数字 / 命令输出）

修后 `14 个图标反解核对：正圆底 + 底色与设计源一致` PASS，逐行比对 0 处不一致；
身份断言投毒（判据改成 `== CFG(ROW_PITCH) + 1`）→ `FAIL pitch=120 rows=14（config 的 ROW_PITCH=120）`，
还原后 20/20 PASS rc=0；`preflight` rc=0。

## 沉淀（新增断言 / 案例 / 文档）

`preflight` 第 5 组新增 6 条：表长==design_source 且==14、`apps.py` 不许手抄表、
`gen_assets.py` 必须 `from design_view import draw_icon`、R/B 换序必须在位、
`icons/` 不许有孤儿 `.c`、**反解 `.c` 字节**逐行验圆底与底色（真判据，不依赖源码写法）。
纪律一条：**汇报断言要带消息文本**，只报 "N/N PASS" 等于没自证
（本轮就有一条格式串参数不匹配的断言 PASS 着，消息里却是 `-1911482096`）。
