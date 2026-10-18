# P-0146 · EEZ Studio「Checks」面板遇到带 customInputs 的 SwitchActionComponent 会死循环永不结束（编辑器 bug，不影响构建/运行）

- **工程**：watch (Design Watch)
- **日期**：2026-10-18
- **工具**：Qoder
- **状态**：known-limitation
- **标签**：eez-studio,checks,死循环,switch,custominputs,手势,编辑器bug,git二分
- **关联提示词**：PR-0244

## 现象（看到什么）

工程打开后 EEZ Studio 底部「Checks」页签图标**无限转圈**（用户观察到持续 2 小时不结束）。
对照工程 eez-test 秒出 ✓。构建(CLI 0错0警)、运行(gesturetest 14 PASS)、导航(nav_audit PASS)全部正常——纯编辑器侧 Checks 卡死。

## 根因（真正的原因）

git 版本二分（watch/.git 是仓库）定位：首个坏提交 = 2aad4d9（§35 手势导航引入）。
内容二分逐层剥离（脚本 tmp39 + spin_test.sh 用像素差分判 spinner）：
时钟链/图标动画链/条件表达式/GESTURE 连线/dataType(any→integer)/eventHandlers 全保留仍转；
**删手势 SwitchActionComponent → 停；只删 Switch 的 customInputs:[{name:evt,dataType:any}] → 停**。
⇒ 触发点是「SwitchActionComponent 带 customInputs」。滚轮链的 Switch 无 customInputs 故从不卡；
手势链为接事件对象给 Switch 加了 evt 自定义输入，正好命中 EEZ 检查器的死循环。

## 修复（做了什么）

未改实现（手势运行时是对的，删 customInputs 会断 Event.getGestureDir(evt) 取事件）。
定性为编辑器 Checks 的已知 bug：可安全忽略（不 block 任何产物）。
候选规避（需再验运行时才做）：改用不带 customInputs 的决策构造接事件，或事件走 SetVariable 中继到普通变量再判。

## 证据（数字 / 命令输出）

spin_test 差分：cfe4b4e/62f349c/75c78ee=0(停)；2aad4d9/工作树≈2.9万(转)；
tI(删手势链)=0、tN(删 Switch customInputs)=0；tF/tH/tJ/tK/tL/tM≈2.8万(仍转)。

## 沉淀（新增断言 / 案例 / 文档）

§11.41 手势配方补注：该写法会触发编辑器 Checks 死循环（运行时正常），验收 Checks 转圈别误判工程坏；
git 内容二分法（导出历史版本+像素差分）作为定位编辑器行为回归的标准手段。报告 §46。
