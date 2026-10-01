# 电脑无规律黑屏重启：从 Event 41 定位到 DDR5 EXPO 内存不稳

> 适用：Windows PC 无预警黑屏重启，无蓝屏、无任何报错提示
> 案例机器：ASUS B650M-AYW WIFI (BIOS 3222) + AMD Ryzen 7 9700X + 金百达 16G DDR5 (EXPO 6000) + 核显（无独显）
> 结论：**DDR5 EXPO 6000 内存不稳**，已用 TestMem5 稳定复现；电源为次要嫌疑
> 日期：2026-10-01

## 结论先行

"黑屏 + 无报错 + 直接重启" = **硬件级瞬间掉电**，不是蓝屏、也不是软件崩溃。
判断依据：Event 41 的 `BugcheckCode=0`、无任何内存转储文件、无 WHEA 事件。软件崩溃必然留下蓝屏或转储，三样全无就只能是供电被瞬间切断。
本案最终定位到**内存超频不稳**——因为纯内存压力测试（TestMem5）一跑必崩，这是可稳定复现的负载触发型掉电。

## 1. 判据表：区分"硬件掉电"与"软件崩溃"

| 检查项 | 本案结果 | 判读 |
|---|---|---|
| Event 41 `BugcheckCode` / `BugcheckParameter1-4` | 全为 0 | 根本没产生蓝屏代码 |
| Event 41 `PowerButtonTimestamp` | 0 | 不是电源键被按 |
| Event 41 `SleepInProgress` | 0 | 不是睡眠唤醒失败 |
| `C:\Windows\MEMORY.DMP` | 不存在 | 来不及写转储 |
| `C:\Windows\Minidump` | 目录不存在 | 同上 |
| WHEA-Logger 事件 | 一条都没有 | CPU / PCIe 硬件报错后自杀也能排除 |
| Display 4101 / 4102 (TDR) | 无 | 不是显卡驱动挂掉 |

> 经验规则：**只要 `BugcheckCode=0` + 无转储 + 无 WHEA，就不要再花时间查驱动和软件**，直接按硬件供电方向走。

## 2. 可复用的查询命令（PowerShell）

```powershell
# 1) Event 41 and all parameters (BugcheckCode / PowerButtonTimestamp included)
Get-WinEvent -FilterHashtable @{LogName='System'; Id=41} -MaxEvents 15 |
  Select-Object TimeCreated, @{n='Data';e={($_.Properties | ForEach-Object {$_.Value}) -join ' | '}}

# 2) 6008 = previous shutdown was unexpected (the time inside Message is the real crash time)
Get-WinEvent -FilterHashtable @{LogName='System'; Id=6008} -MaxEvents 10 |
  Select-Object TimeCreated, Message

# 3) Check for kernel dumps
Test-Path C:\Windows\MEMORY.DMP ; Test-Path C:\Windows\Minidump

# 4) Check for CPU / PCIe hardware errors
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-WHEA-Logger'} -MaxEvents 10

# 5) Sleep / resume records (42 = sleep, 107 = resume, 109 = entering sleep)
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Kernel-Power'} |
  Where-Object {$_.Id -in @(42,107,109)} | Select-Object TimeCreated, Id

# 6) Total restart count within 30 days
(Get-WinEvent -FilterHashtable @{LogName='System'; Id=41; StartTime=(Get-Date).AddDays(-30)}).Count
```

> 注意：Event 41 是**下次开机时**才写入的，所以"41 的时间 - 6008 里的关机时间"= 机器多久才重新点亮，这个差值很有诊断价值。

## 3. 本案时间线（30 天 8 次，频率在恶化）

```
9/21 09:59  →  9/30 21:11  →  9/30 21:42  →  10/1 06:52
→  10/1 07:14  →  10/1 07:15  →  10/1 08:16  →  10/1 10:08
```

- 10/1 一个早上就崩了 5 次，明显在升级 → 不是偶发老化，是**确定性硬件缺陷**。

## 4. 两个关键信号，直接把方向锁定

| 信号 | 现象 | 推理 |
|---|---|---|
| A | 7:14:09 崩溃 → 7:14:59 重新开机 → **7:15:06 又崩了**（开机仅约 7 秒） | 开机时内存要重新训练 + 大量读写，正好踩中同一个雷 |
| B | 多数崩溃后要 **20–40 分钟**才能重新点亮 | 内存训练失败导致黑屏，或电源过流保护锁死需放电恢复 |
| C | 跑 TM5 内存测试**立即重启** | 负载型可稳定复现，且 TM5 功耗远低于烤机 → 不是"功率不够" |

注：本案机器**只有核显、没有独显**，整机功耗不高，所以"电源功率不足"的可能性低于"内存超频不稳 / 电源老化 / 接触不良"。

## 5. 定位工具：TestMem5 (TM5)

- 路径：`D:\0-电脑相关\系统测试工具\TM5`，配置目录 `bin\*.cfg`
- 常用配置：`anta777-extreme.cfg`、`anta777-Heavy5opt.cfg`、`1usmus V3.cfg`、`3-1500专业败家高压力版.cfg`（Config Name = Superpc OC v3.1）
- 日志中的 `x16` = 16 线程，对应 8C/16T 的 9700X；`x24/x32` 说明该日志还混有别的机器记录
- 判读要点：
  - `Log.txt` 里出现任意 `Error in test #N` → 内存**已经**不稳定，不必等整轮跑完
  - `crash.log` 里 `Exception code: C0000005h` → 测试线程读到错误数据后访问违例，是**内存出错**的典型特征
  - 整机直接重启（连日志都来不及写）→ 错误严重到 CPU 直接复位

> 注意：这个 TM5 目录是从别人机器整体拷来的（`bin\Cfg.link` 指向 `C:\Users\Arui\Downloads\稳定性测试软件\TM5\...`），`Log.txt` 里的历史报错**不一定属于本机**，只能作参考。

## 6. 排查动作（二分法，先做这一步）

进 BIOS：

1. **关闭 EXPO / DOCP**，内存跑 **4800 JEDEC 默认频率**
2. **关闭 Memory Context Restore / 快速内存训练**（让每次开机真正重新训练内存）
3. 保存重启后再跑 TM5

结果判断：

- **能跑过（无 Error、不重启）** → 就是内存超频问题。解法：降到 5600 / 5200，或手动抬 **VSOC / VDDIO / VDDQ**，同时更新 BIOS 拿新 AGESA。
- **仍然一跑就重启** → 排除超频，问题在硬件本身：坏条 / 坏插槽 / 主板内存供电 (VRM) / 电源。

若属于后者，按顺序排查：

1. **只插一条内存，插在 A2（第 2 槽）**，两条轮流测 → 区分"某条坏"还是"整机问题"
2. 内存拔下重插，橡皮擦金手指，吹插槽；双条必须插 **A2 + B2**（2、4 槽）
3. 用 **MemTest86**（U 盘启动版）跑，它能报出**具体出错地址**，比 TM5 更能定位到哪条/哪个槽
4. 借一个电源换上测（或重插 24pin / CPU 8pin 到卡扣到位）
5. 更新 BIOS（AGESA 对 DDR5 兼容性和稳定性修复基本都在这里）

## 7. 安全提醒

每次硬断电都可能在损坏文件系统或正在写入的 SSD，等于在反复做"带电拔电"实验。
**排查期间先备份重要数据，并尽量少跑 TM5。**

## 8. 附带发现（顺带排除项）

- `QuarkUpdaterService` 在每次崩溃前几分钟都报 7024 错误（夸克网盘更新服务）。用户态服务不可能直接切断电源，属待排除项而非元凶。
- `AndrowsSvr` / `luafv` 启动失败是掉电后的**连带现象**，不是原因。
- 系统启用了频繁自动睡眠 + 快速启动 + 混合睡眠，排查期间建议临时关闭以减少变量。
