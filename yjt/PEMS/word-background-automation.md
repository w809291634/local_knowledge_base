# Word 后台自动化方案（用户不受打扰）

> 状态：2026-11-24 实测定稿，注册人确认“不再出现打开/关闭弹窗”。
> 适用：任何需要用 Word 刷新目录域、导出 PDF、核算页数的文档批处理（PEMS、说明书、注册资料等）。
> 实现：`tools/word_session.py`；项目侧示例：`work/format.py` 的 `word_refresh`／`word_export`。
> 相关坑例：`pitfalls.md` §128（关掉用户 Word）、§130（窗口反复闪现）。

---

## 1. 目标

1. 用户可在生成/收口期间**正常使用 Word 编辑自己的文档**，不被打断；
2. 不出现 Word 窗口、任务栏图标反复出现消失；
3. 不关闭、不接管、不覆盖用户已打开的文档；
4. 自动化异常时能给出明确提示，而不是硬改文件。

---

## 2. 为什么之前会出问题

| 现象 | 根因 |
|---|---|
| 用户 Word 被关闭 | `Application.Quit()` 是**进程级**退出；脚本结束一 Quit，同一 WINWORD 里用户所有窗口一起没了 |
| 用户窗口突然消失 | 脚本设 `app.Visible = False`，复用用户实例时把用户窗口一起隐藏 |
| 窗口/任务栏反复闪 | 每份文档、每次导出都新建一个 Word 进程，一轮几十次启动/退出 |
| 用户文档内容被覆盖 | 对已打开文档执行 `Documents.Open(ReadOnly=False)` 再 `Save`，抢写用户正在编辑的副本 |
| 目录刷新偶发失败 | Word 忙（用户正在输入）时 COM 抛 “Call was rejected by callee” |

关键认知：**Word 是单实例 COM 服务器**，`GetActiveObject("Word.Application")` 拿到的是用户那个可见实例；
而 `DispatchEx("Word.Application")` 会起一个**独立的新进程**（实测：`Visible=False`、`Documents.Count=0`、PID 与用户进程不同）。

---

## 3. 方案（四条硬规则）

1. **只用独立隐藏实例**
   `win32com.client.DispatchEx("Word.Application")` → `Visible=False`、`DisplayAlerts=0`、`ScreenUpdating=False`。
   **禁止** `GetActiveObject` 接管用户实例。
2. **整轮一个会话**
   模块级缓存，首次创建、全程复用；`atexit` 统一收尾。文档处理完只 `doc.Close(False)`，**不退出实例**。
3. **只动自己的文档**
   打开前先在本会话 `Documents` 里按绝对路径查找；已存在则复用（不关、不另存）；只关闭自己 `Open` 的那份。
4. **导出只读 + 写回前查锁**
   PDF 一律 `ReadOnly=True`；需要保存（刷新域）时先看目标目录有没有 `~$xxx.docx` 锁文件，有就提示用户先关闭。

运行方式：**隐藏窗口启动** `python.exe`（不是 pythonw），子步骤继承隐藏控制台，全程无窗口。

---

## 4. 模块 API（`tools/word_session.py`）

| 函数 | 作用 | 说明 |
|---|---|---|
| `get_app()` | 取得本轮唯一隐藏实例 | 首次调用创建；不要在外部自己 Dispatch |
| `open_doc(path, readonly=True)` | 打开文档 | 返回 `(doc, opened_by_us)`；已在会话中的文档直接复用 |
| `close_doc(doc, opened)` | 关闭文档 | 仅 `opened_by_us=True` 时关闭 |
| `has_lock_files(folder)` | 查 `~$` 锁文件 | 返回文件名列表；调用方负责提示 |
| `refresh_fields(path)` | 刷新正文/TOC/页眉页脚域并保存 | 内部先查锁；文档被占用时抛 `RuntimeError` |
| `export_pdf(path, pdf, retries=3)` | 只读导出 PDF 并返回页数 | Word 忙时自动重试 |
| `quit_app()` | 恢复 `ScreenUpdating` 并退出本轮实例 | 不调用也会在进程结束时自动执行 |

代码骨架（照这个写，不要另起一套）：

```python
import word_session as W

pages = W.export_pdf(r"D:\out\RD-001_V1.docx", r"D:\out\RD-001_V1.pdf")
W.refresh_fields(r"D:\out\RD-001_V1.docx")   # 需要写回时才用
W.quit_app()
```

---

## 5. 新项目接入步骤

1. **加路径**：脚本头部
   `sys.path.insert(0, r"C:\Users\yjt54\Desktop\local_knowledge_base\yjt\PEMS\tools")`，
   然后 `import word_session as W`。
2. **替换旧写法**：全局搜索并删除 `win32com.client.DispatchEx`、`GetActiveObject`、`Application.Quit`、
   `Documents.Open` 的直接调用，改为 `W.export_pdf`／`W.refresh_fields`。
3. **收口脚本加锁预检**：开始前扫描目标目录 `~$*`，有则 `SystemExit("请先关闭：…")`，不要硬写。
4. **后台执行收口**：用第 6 节的 PowerShell 命令，日志写文件。
5. **验收**：按第 7 节三项检查各跑一次，正反样本都要过。

---

## 6. 后台运行命令（PowerShell 5）

```powershell
$env:PYTHONIOENCODING = "utf-8"
$py  = (Get-Command python).Source          # 不要用 pythonw
$cwd = (Get-Location).Path
$p = Start-Process -FilePath $py `
      -ArgumentList 'work\closeout.py','--ver','V3','--dir','PEMS_V3' `
      -WorkingDirectory $cwd -WindowStyle Hidden -PassThru -Wait `
      -RedirectStandardOutput "$cwd\work\reports\closeout_V3.log" `
      -RedirectStandardError  "$cwd\work\reports\closeout_V3.err"
"exit=$($p.ExitCode)"
Get-Content "$cwd\work\reports\closeout_V3.log" -Tail 20
```

要点：
- `-WindowStyle Hidden` 隐藏控制台；子步骤用 `sys.executable` 启动，同样隐藏。
- **不要用 `pythonw.exe`**：pythonw 下 `sys.stdout=None`，脚本里的 `print` 直接报错，表现为“退出码 1、日志空白”。
- 退出码非 0 时先看 `.err` 文件，再看 `.log` 最后一个 GATE。

---

## 7. 验收清单（可执行）

| 检查 | 方法 | 通过标准 |
|---|---|---|
| 不接管用户 Word | 用户打开一份可见文档，跑一次 `export_pdf` | 导出成功；用户文档仍在、仍可见 |
| 自动化实例无窗口 | 导出期间 `Get-Process WINWORD \| Select Id,MainWindowTitle` | 自动化进程 `MainWindowTitle` 为空，用户进程标题正常 |
| 无残留进程 | 脚本结束 2 秒后再查 PID | 只剩用户自己的 WINWORD |
| 锁文件保护 | 在目标目录手工造 `~$x.docx` 后跑 `refresh_fields` | 抛“请先关闭文档”，不写文件 |
| 批量不闪 | 跑完整收口（8 份 + 多轮导出） | 全程无窗口/任务栏闪现 |

实测数据（2026-11-24，03GSR2609026 V22）：用户 Word PID 33148 全程保持；自动化进程标题为空、结束后自动退出；
导出 4 页文档耗时正常；整轮 14 项门禁 exit 0。

---

## 8. 常见坑与排查

| 症状 | 原因 | 处理 |
|---|---|---|
| 退出码 1、日志空白 | 用了 `pythonw`，`print` 失败 | 改用 `python.exe` + `-WindowStyle Hidden` |
| 用户 Word 还是被关 | 代码里仍有 `GetActiveObject` 或 `Quit` | 全库搜索这两个词，统一走 `word_session` |
| 刷新域报“文档被占用/只读” | 目标目录有 `~$` 锁，用户正打开 | 提示用户关闭后重跑；不要强制写 |
| `Call was rejected by callee` | Word 正忙（用户输入/其他宏） | 模块自带重试；不要收紧成一次失败就退 |
| 导出的 PDF 页码与 Word 不一致 | 用了非 Word 渲染（LibreOffice 等） | 目录页码必须按 Word 导出结果同步 |
| 目录条目没刷新 | 静态目录（无 TOC 域） | 静态目录走项目自己的 `sync_toc.py`，不要用 `refresh_fields` |
| 会话缓存“没生效” | 每个脚本是独立进程 | 单进程内复用；跨脚本仍是每进程一个隐藏实例（无窗口，可接受） |
| Word 启动慢/首启弹激活 | 系统首次运行 Office | 预热一次；不要把超时调得过短 |

---

## 9. 与版本/流程的关系

- 本方案属于工具层，**不触发文档版本递增**（`iteration-and-versioning.md` §10 第 6 条）。
- 收口流程（`authoring-workflow-and-experience-index.md` S7）已写明：Word 刷新与导出统一走 `tools/word_session.py`，
  收口用隐藏窗口执行；S8 的标题/目录门禁读的是导出后的 PDF，不受运行方式影响。
- 变更本方案时同步更新：本文件、`pitfalls.md` §130、`pems.config.json → word_automation_policy`、`README.md` 工具表。

---

## 10. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-24 | 初版：独立隐藏实例 + 单会话 + 只关自开文档 + 锁预检 + 隐藏窗口运行；实测用户 Word 不受影响 |
| 2026-11-24 | 修正：禁止 `GetActiveObject`（会接管用户实例导致窗口开关）；补充 pythonw 陷阱 |
