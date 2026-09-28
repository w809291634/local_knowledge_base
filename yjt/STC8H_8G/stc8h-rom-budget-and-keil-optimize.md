# STC8H 8 KB 容量预算：ROM 到底怎么看、Keil 编译/链接选项怎么选（含实测）

> 适用：STC8H1K08 等 8 KB Flash 的 Keil C51 工程（容量告急、"差一点装不下"反复出现的场合）
> 来源工程：STC8G_8H_SDK 下游工程 `STC8H1K08_template`（红蓝光治疗仪固件，2026-09-28 实测）
> 目标：把"还剩多少 ROM / 怎么省 / 省下来的代价是什么"固化成可复现的流程，不再靠感觉

## 结论先行

四条铁律：① **判容量只看 hex 末地址**——`code=` 会骗人，**超容量也不报 L107**；② 省空间的正确顺序是先"**配置**"（关调试打印、编译选项）后"源码"，最后才动公共库；③ 编译选项里 `Optimize=9`、`SizeSpeed=favor size` 属于**省空间换一点执行时间**，`ACallAJmp=1`（`OBJECTADVANCED`）省得更多但官方明确降速、且引入链接器生成的公共块，风险面更大；④ 改完必须做 **段集合对比** 证明"没丢函数"，只看总大小变小不算验证。

## 1. 容量怎么看（唯一可信的判据）

| 指标 | 是否可信 | 说明 |
|---|---|---|
| `Program Size: code= const=` | 参考 | ROM 合计 = code + const；`const` 是 code 空间里的常量表 |
| **hex 末地址** | ✅ **唯一判据** | 真正烧进 flash 的最后一个字节；`8192 - (末地址 + 1)` = 真实余量 |
| Keil 报错 | ❌ **完全不可信** | STC 器件库 IROM 定义偏松，**超出 8 KB 不报 L107**，工程照样"0 Error" |

```python
img_max = total = 0
for line in open('Objects/xxx.hex'):
    line = line.strip()
    if not line.startswith(':'): continue
    b = bytes.fromhex(line[1:]); n, a = b[0], (b[1] << 8) | b[2]
    if b[3] == 0:                       # 数据记录
        total += n
        img_max = max(img_max, a + n - 1)
print('hexmax=0x%X bytes=%d 8K余量=%d' % (img_max, total, 8192 - (img_max + 1)))
```

定位"谁在吃空间"用 `m51_size.py`（按模块汇总 ROM/CODE/CONST/DATA/XDATA）。

## 2. 省空间的优先级（实测收益排序）

| 顺序 | 手段 | 实测收益 | 代价 / 前提 |
|---|---|---|---|
| 1 | **关调试打印** `BOARD_CONFIG_DBG_NODBG=1` | **≈ −1.1 KB**（kprintf ~480 B + UART 代码 ~280 B + XDATA 128 B，另有 const） | 失去串口调试能力；**仅当"发布版不需要打印"时才成立** |
| 2 | `<Optimize>` 8 → 9 | 本工程 **−444 B**（单独） | 官方口径："省空间、略增执行时间" |
| 3 | `<SizeSpeed>` → favor size | 本工程 **−97 B**（单独） | 以速度换体积 |
| 4 | `<ACallAJmp>` 0 → 1 | 本工程再 **−434 B** | 官方原文 "shrink program size and **decrease execution speed**"；引入链接器公共块；**仅 LX51 支持** |
| 5 | 砍公共库功能（如"极简版 printf"） | 数百 B | 伤可维护性、牵动其它工程，**最不该先动** |
| 6 | 删掉关调试后残留的格式串 | ~60 B（逐文件不同，需实测） | 只回收 const；见 §6 |

**最重要的顺序经验**：容量告急时先问一句"**这个版本的调试打印要不要留**"。量产/发布版答案通常是"不要"，而**这一步的收益顶得上后面所有编译选项之和，且零风险**（不改一行代码、不改变 codegen）。

## 3. Keil 选项的真实含义（官方口径 + 怎么反查确认）

- `<Optimize>` 0~9 级。
  - **8 级** = "Re-use Common Entry Code"（C51 v6.20 起的**默认**值）；
  - **9 级** = **"Common Block Subroutines"**：检测并把重复出现的指令序列合并成子程序，对"大而集中"的模块收益最大。
  - 实测指纹：等级 9 生效后，map 里会多出 **`?PR?<模块名>`** 段（模块级公共块，如 `?PR?APP_STATE` 84 B、`?PR?DRV_INPUTSCAN_LITE` 73 B）。
- `<SizeSpeed>`：**0 → favor size（`OPTIMIZE(n,SIZE)`）、1 → favor speed**（**0 才是尺寸优先**，凭直觉很容易记反）。
- `<ACallAJmp>` = uVision 的「C51 → Code Optimization → **Linker Code Packing (max. AJMP / ACALL)**」= C51 指令 **`OBJECTADVANCED`**（**仅 LX51 支持，BL51 不支持**）：
  - 等级 0~7 重排代码段以最大化 2 字节 AJMP/ACALL；8 复用公共入口代码；9 公共块子程序；10 重排；11 复用公共出口代码；
  - 生效后 map 里出现 **`?L?COMxxxx`**（链接器生成的公共块）；同时 C51 会**去掉 `OMF2`** 指令（object 文件格式变化）；
  - 官方 KB 原话："used in conjunction with the OPTIMIZE directive to **shrink program size and decrease execution speed**"。
  - 注意：AJMP/ACALL 的 **2 KB 页寻址范围是"能力上限"（决定能省多少），不是正确性风险**——页边界由链接器自己算，配错会报错而不是生成错误跳转。只有**目标 MCU 不支持这两条指令**时才必须关（少数 8051 派生核）。

**选项记不准时不要猜，去反查编译器实际收到了什么**——`Listings/<模块>.lst` 头部的 `COMPILER INVOKED BY:` 行，例如：

```
COMPILER INVOKED BY: C:\Keil_v5\C51\BIN\C51.EXE ..\..\common\apl\apl_soft_timer\apl_soft_timer.c OMF2 OPTIMIZE(9,SIZE) ... PRINT(.\Listings\apl_soft_timer.lst)
```

## 4. 验证四件套（不能只看"变小了"）

1. **用全量重编 `UV4 -r`，不要用增量 `-b`**：增量只重编改动过的文件，**未重编的文件不产生警告** → 日志里会出现"0 Warning(s)"的**假象**（实测同一份代码 `-b` 报 0 警告、`-r` 报 7 警告）。判"有没有新增警告"必须全量。
2. **段集合对比**（最有价值的静态证据）：分别导出两种配置的 map，取全部 `?PR?` / `?CO?` 段名做差集。**有段消失必须查清**；只多出 `?PR?<模块>` / `?L?COM` 这类公共块属正常。
3. **overlay 脚本**（`check_overlay_safety.py` 退出码 0）——注意它有盲区，见 `keil-c51-overlay-function-pointer.md` §7。
4. **hex 末地址**：确认真的装得下，并把本次数字写进文档当基线。

### 4.1 怀疑"优化改坏了语义"时：单独编一个模块看反汇编

默认 `.lst` 只有源码（`PRINT()`），要看指令必须 `SRC()`。可以**单独编译一个文件**，不用动工程：

```powershell
C:\Keil_v5\C51\BIN\C51.EXE ..\..\common\apl\apl_soft_timer\apl_soft_timer.c ^
  "OPTIMIZE(9,SIZE)" "INCDIR(...)" "SRC(.\_t.lst)" "OBJECT(.\_t.obj)"
```

**实战案例**：`tickCnt_Get()` 靠"连读两次 `volatile` 直到相等"来防 32 位 tick 被 1 ms 中断写一半的**撕裂**。怕 `OPTIMIZE(9)` 把两次读合并 → 反汇编确认仍是两次独立读（`LCALL L?0010` / `LCALL L?0011`），**volatile 语义未被破坏**。
→ **优化等级拉高后最该怀疑的就是 volatile / 时序敏感代码，必须实测，不能凭印象。**

## 5. 实测数据（同一份源码，只改选项）

| 配置 | code | const | ROM 合计 | hex 末地址 | 8 KB 余量 |
|---|---|---|---|---|---|
| Optimize=8 + favor speed（原始） | 7252 | 137 | 7389 | 0x1D62 | +669 |
| **Optimize=9 + favor size（采用）** | **6765** | **137** | **6902** | **0x1B6E** | **+1169** |

- 净收益 **−487 B**；两次构建都是 0 Error / 7 Warning（厂商库 `STC8G_H_NVIC.c` 的 C260，逐条完全相同）。
- 函数完整性：**0 个段丢失**，只新增 12 个 `?PR?<模块>` 公共块。
- 另一套更激进的组合（`Optimize=9 + ACallAJmp=1`）能到 7022 B / 余 799 B，但代价与不确定性更大，最终**未采用**。

## 6. 本次踩到的三个"容量幻觉"（留档）

1. **"看起来只差一点点"其实已经超了**：`Program Size: code=7900 const=259` + `0 Error`，看着像"还剩一点"，实际 hex 末地址 0x2061 已**超 8 KB 共 98 字节**。超容量完全静默。
2. **增量编译的警告数是假象**：`UV4 -b` 报 "0 Warning(s)"，换 `-r` 全量重编，7 条历史警告照旧出现。
3. **关调试后 const 不会自动清零**：关掉 `NODBG` 后 const 从 228 → 137 B，但**仍有约 61 B 死字符串留在 flash**（`app_light`/`app_display` 的 `log_iraw` 格式串，在 hex 里搜 ASCII 可确认；而 `app_state` 的同类字符串却被编译器丢掉了）。
   → **"字符串常量会不会残留"没有通用规律**（取决于写法/上下文，编译器行为不一致），**必须用 hex 搜一遍才能下结论**——这是 `keil-c51-language-pitfalls.md` §4"CONST 段整体合并、没人调的字符串不会自动裁"的延伸：连"关掉调用点后到底还占不占 flash"都得实测。

## 7. 相关文件

- `keil-c51-overlay-function-pointer.md`：函数指针 overlay 规则 + 检查脚本盲区
- `keil-c51-language-pitfalls.md`：变参/`data` 关键字/指针限定符/CONST 段
- `workflow-verification-discipline.md`：改前必读 / 验证三件套 / 提交规范
