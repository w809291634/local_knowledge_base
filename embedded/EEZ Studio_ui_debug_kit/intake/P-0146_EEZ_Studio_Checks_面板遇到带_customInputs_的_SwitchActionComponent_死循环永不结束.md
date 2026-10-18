# P-0146 · EEZ Studio「Checks」面板遇到带 customInputs 的 SwitchActionComponent 会死循环永不结束（编辑器 bug，不影响构建/运行）

- **工程**：watch (Design Watch)
- **日期**：2026-10-18
- **工具**：Qoder
- **状态**：fixed
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

内容二分进一步证明：好版本加一个未连接 customInput（any 或 integer 皆）即转圈
⇒ 触发点是「组件带非空 customInputs」本身，非 any 专属、非连线。SetVariable 中继也带 customInput 故无效。
最终修复：本工程每页手势只有唯一目标，方向无关不影响导航 ⇒ 删「Switch+evt 判 getGestureDir」，
改 host[GESTURE] 直连 changeScreen(固定目标)，全工程 customInputs 归零 → Checks 正常结束，
gesturetest 15 断言仍全过（见报告 §46）。

## 证据（数字 / 命令输出）

spin_test 差分：cfe4b4e/62f349c/75c78ee=0(停)；2aad4d9/工作树≈2.9万(转)；
tI(删手势链)=0、tN(删 Switch customInputs)=0；tF/tH/tJ/tK/tL/tM≈2.8万(仍转)。

## 沉淀（新增断言 / 案例 / 文档）

§11.41 手势配方补注：该写法会触发编辑器 Checks 死循环（运行时正常），验收 Checks 转圈别误判工程坏；
git 内容二分法（导出历史版本+像素差分）作为定位编辑器行为回归的标准手段。报告 §46。


---
【更正 2026-10-18（用户引说明书 P4 节后复核）】说明书原文：「Checks：项目编辑器会在后台**不断**寻找工程错误（如错误表达式），找到的错误列在面板中」
⇒ 转圈图标是**常驻后台检查器的工作指示**，不是一次性任务；"卡死"措辞不准。
准确表述：customInputs 存在时后台检查器**永不空闲**（图标持续转）；删除后同一工程立即空闲（图标静止）——
双向对照（tI/tN 停、tQ/tR 起）+ 对照工程 flowSupport=true 且 0 customInputs 时静止，三组证据不变。
CLI 无头 Check（同一检查器批模式）新旧工程均 0 错 0 警 ⇒ 面板大概率无错误条目可列，症状只剩图标。
疑点定位到 A1.2.21（输入 type 用于校验所连数据线类型）：事件数据线类型无法在 customInput 上合法声明
（'event' 直接崩编辑器 P-0141，'any'/'integer' 令后台检查永不收敛）——EEZ 1.22 事件输入类型体系不成熟。
修复结论不受影响：能用「直连 changeScreen」就别用 customInputs。


---
【终版裁决 2026-10-18 晚（最小复现工程定案）】**根因=我们自己的字段名笔误，不是 EEZ bug**。
- 手册 A1.2.21 + asar CustomInput{name,type}：自定义输入的类型字段叫 **`type`**（编辑器
  "Convert to input" 写 `type:"any"`）；我们 §35 起一直写 **`dataType:"any"`** → 未知字段被
  编辑器静默丢弃 → 输入**无类型** → 后台 Checks（按类型校验连线）永不收敛 → 图标永转。
- 最小复现（design/make_gesture_repro.py 生成 gesture-repro/repro_ok|repro_bad，两页手势互切）：
  repro_ok（evt 带 type:"any"）→ 静止；repro_bad（缺 type）→ 转圈。单变量闭环。
- 真实工程 35 处补 type:"any" 后 → 静止（5/5 采样）；生成器已改，dataType 全工程清零。
- 连带作废：§46"删 customInputs 保静止"的取舍**不再需要**——方向判定手势与 Checks 静止兼得；
  §46 直连方案已从生成器回滚；P-0145 单实例抢占仍是独立真实问题（构建链与手工会话互斥）。
