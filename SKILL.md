---
name: usecase-reconstruction
description: 从只有源代码（可能含文档）的既有系统重建 use case model 与场景规格，按 UML 2.5.1 §18 的用例模型结构与 ISO/IEC/IEEE 29148:2018 Annex A.2.7 / §9.6.12 的场景与功能细节组织产出，每条用例目标与 actor 附证据与置信度，代码里推不出的目标显式声明为缺口而不是编造。当用户问「这个项目到底给谁用、能干什么」「这个系统对外提供什么能力」「有哪些用户场景」「帮我把需求文档补出来」「梳理一下业务流程」「这个系统的用户故事是什么」「重写/迁移前要先搞清楚行为契约」「做测试覆盖分析前先搞清楚有哪些场景」「接手一个没文档的系统要先弄清楚它能做什么」，或要产出用例模型、用例清单、场景规格、用例↔测试追溯矩阵时，都应当使用本 skill——即使用户没有说出「用例重建」「use case」「29148」这些词。不适用于为尚不存在的新系统做正向需求分析（那是需求工程，不是逆向重建）。
---

# 用例重建（Use Case Reconstruction）

## 这件事的本质

代码里没有「用例」，只有**入口点与执行路径**。用例的定义性要素是"对 Actor 有价值的可观察结果"（UML 2.5.1 §18.1.3.1）：

> …yields an observable result that is of **value** for Actors or other stakeholders of the subject.

而**价值与目标都不在代码里**——只能从证据推断，永远不能从代码里"读出来"。这是本 skill 全部纪律的出发点：不是内容不够多，是要让每条目标性断言的认知地位可见。

与 `architecture-reconstruction` 是独立 skill，不互相依赖：那个关注结构（白盒），本 skill 关注行为契约（黑盒）。证据源部分重叠，取证脚本的思路可借鉴，但不共享代码。

## 头号失败模式：粒度失控

**双向的**，且有实证。UCRBench（arXiv:2512.13360）在 Xpipe 项目（Remote Infrastructure Management，66,609 行）上，人工标注了 37 个子功能（subfunction）用例；同一项目上 GPT-5 生成了 2103 个（约 57 倍），产出「Check GPU」「Show loading」这类界面动作——脱离上下文没有独立价值。反方向同样失控：在 Rouyi 项目的 user-goal 级重建中，GPT-5 把 19 个应分立的子功能操作合并成 1 个用例，差异化行为被压扁。

**此处引用的是失败模式的结构性描述，不是分数基线**——论文评测的模型（GPT-5、DeepSeek-V3.2 等）已非当前最新一代，具体准确率不作为本 skill 的目标。真正可移植的结论是论文原句：「current models lack explicit mechanisms for regulating abstraction levels or reasoning hierarchies」——这是**机制缺失**，不会随模型升级自动消失，所以判据必须由本 skill 显式提供。

**对治工具**（唯一可判定的一句，UML §18.1.3.1）：

> 执行完毕后，subject 是否处于"无待续输入或动作、用例可被重新发起"的状态，或错误态？

是 → 候选用例；否 → 它是某个用例的片段，不是用例。

**对照例**：`DELETE /orders/{id}` 处理函数校验权限、查订单、存在则取消并释放库存、不存在则返回 404，两条分支都在处理函数返回时结束——通过判据，`Cancel Order` 是候选用例。函数内部单独抽出的"校验权限"一步，脱离这次取消请求没有独立价值，不通过判据，不是独立用例。完整流程、辅助判据（两个都通过判据的候选是否其实必须合并）与正反例各 5 组（覆盖 getter 类、UI 动作类、内部步骤类、过度合并类、CRUD 未合并类五种典型失控），见 `references/granularity.md`。

对治不是"提醒模型注意粒度"，是**改变生成顺序**：先机械列出全部对外操作（事实层），再用上面的判据聚合成用例（假说层），不要让模型直接对着代码"想"出一份用例清单。这正是工作流里 **Step 3 必须先于 Step 4** 的结构性理由，不是顺序偏好——见下文工作流。

## 另两个失败模式

**把实现写进用例。** 双重规范依据：UML §18.1.3.1「without reference to its internal structure」+ 29148 §5.2.5 Appropriate（shall）「allowing implementation independence to the extent possible」。可检查判据：产出中出现数据库表名、内部类名、SQL、私有函数名、线程模型 → 违规。

**编造 actor 的目标。** 与 AR 的 rationale 问题同构，但更致命——目标是用例的**定义性要素**，不是附属信息（见下节证据纪律）。这一条无法机械查——`check_usecase_model.py` 能核查 `goal_confidence` 有没有标成 `fact`，查不出一句读起来合理但其实无出处的目标描述，只能靠 Step 8 之后的人工自检与验证环节兜底。

## 证据纪律

正文每条实质断言归入三类之一：

```markdown
【事实】`DELETE /orders/{id}` 已注册路由；处理函数在订单不存在时返回 404，
        存在时标记取消、释放库存、发出取消事件、返回 204
        （`internal/http/orders.go:88-114`）

【推断】该路由对应用户目标「取消订单」。依据：CHANGELOG.md:34「支持取消未
        发货订单」与该路径行为吻合；置信度：inferred_high（A 档，行为契约
        与用户面文档双重印证）

【缺口】发起取消操作是否需要额外审批未知（原因：仓库内无权限矩阵；
        可能获取途径：产品经理访谈、内部工单系统历史 ticket）
```

`file:line` 是【事实】的唯一凭据；【推断】必须写推理链与置信度；【缺口】是一等产出。

**本 skill 特有的硬规则：用例名与 actor 目标恒为推断，不得标为【事实】。** UML §18.1.3.1 讲得很明确——actor 是"a type of role"，一个物理实例可扮演多个角色，一个角色也可能由多个物理实例共同扮演；接口与角色是多对多映射，证据再多也推不出"唯一正确"的划分。合法置信度仅 `inferred_high | inferred_medium | inferred_low | gap`，`fact` 不合法——`scripts/check_usecase_model.py` 会对 `goal_confidence == "fact"` 与 `actor.confidence == "fact"` 直接报错。【事实】只能是可 `file:line` 指认的东西：入口点存在、参数被读取、分支条件、异常被吞、事务边界。

（旁证：29148 §6.3.3.4 称 actor 是"systems and classes of people"，UML §18.1.3.1 强调 actor 是"role"——两处定义措辞有出入，标准正文未展开调和，反推时如实标注这处分歧，不要替标准强行统一。）

## 尖锐发现清单

`architecture-reconstruction` 关注结构问题，本 skill 关注**行为契约的违背**——这是分析材料取向的核心产出，逐类扫，不凭印象：

| # | 发现类型 | 判定方式 | 依据 |
|---|---|---|---|
| 1 | 宣称但不存在 | 文档声称的功能，代码里无实现或不可达 | — |
| 2 | 存在但无人知晓 | 代码里有完整对外行为，任何文档都没提（潜在攻击面） | — |
| 3 | 扩展流缺失 | normal/stress/exception/degraded 四类变体，哪类在代码里没有对应路径 | 29148 A.2.7 |
| 4 | 异常被吞 | catch 后既不上报也不记录，调用方无从得知 | 29148 §9.6.12 c) |
| 5 | 后置条件在失败路径下不成立 | 部分提交、写了一半、无补偿 | UML 前后置条件 |
| 6 | actor 越权 | 某条路径缺权限检查，actor 边界被打破 | UML Actor 语义 |
| 7 | 输入校验缺口 | 哪些入参未做 validity check | 29148 §9.6.12 a) |

第 1、2 条不是凭空列的类型：UCRBench 构造 ground truth 时，研究者在全部 9 个真实项目上都必须手工"removing use case goals that are not supported by the code"与"summarizing use cases from implementation files that are not covered by the documentation"——说明这两类偏离是常态，不是个例。

**每条发现必须写明"谁会因此做出错误判断"**，否则它只是代码观察，不是用例发现。**位置放在读者最先看到的地方**（速览档 §2、标准档 UC-00 §3）——自检：只读前两屏能否看到最可能踩的坑？

## 产出什么

三层锚定，不是自己发明的结构：

| 层 | 依据 | 地位 |
|---|---|---|
| 用例模型（subject / actor / 用例 / include / extend） | UML 2.5.1 §18 | 一手，含 4 条 OCL 约束 |
| 场景步骤与四类变体 | 29148:2018 Annex A.2.7、§9.4.17 | 一手，规范性附录 |
| 功能细节（校验 / 序列 / 异常 / 参数 / IO） | 29148 §9.6.12 a)–e) | 一手 |

**一致性声明的诚实形态**：对 UML 不能声明"conformance"（它没有这种表述，四条 OCL 约束能机械核查的只是结构合规，不等于"忠实反映了系统"）；对 29148 连裁剪一致性（Annex C）都做不到——C.2.3 要求"obtain input from all parties affected by the tailoring decisions"，逆向重建没有这些"各方"。诚实的处理方式：把内容项清单当完备性检查表用，在文档头**一次性**声明这个局限，不逐节重复。

**还有一处结构性冲突躲不开**：29148 §5.2.6 Complete（shall）要求需求集合"不含 TBD/TBS/TBR"，而本 skill 的证据纪律要求把拿不到的内容显式标为【缺口】——重建产出必然含 TBD 类占位，两者无法同时满足。选择满足缺口纪律，即对 §5.2.6 不满足，这个取舍同样只在文档头声明一次，不要在正文悄悄抹平。

**用例文本的排版格式不是规范要求。** UML §18.1.3.2 明确用例可以用"natural language, tables, trees, etc."表达，不规定格式；"前置条件 / 主成功场景 / 扩展"这套结构出自 Cockburn《Applying UML and Patterns》【二手】，用不用是排版选择。条款逐条要求、shall/should 区分、§5.2.6 冲突的完整论述，见 `references/content-items.md`。

## 产出规模分级

先估规模再决定形态，内容项不减，只改承载：

| 档位 | 触发条件 | 产出 |
|---|---|---|
| 速览 | 源文件 < 约 150，或只想摸清对外能力 | 单文件，复制 `assets/uc-skeleton/USE-CASES.md` |
| 标准 | 源文件约 150–1500 | 复制 `assets/uc-skeleton/UC-00-overview.md`，每个用例一份 `UC-1x-usecase-TEMPLATE.md`，加 `UC-90-traceability.md`、`UC-99-gaps.md`；字段契约见 `assets/uc-skeleton/uc-manifest.yaml` |
| 完整 | 源文件 > 约 1500，或多模块 | 标准档 + 用例↔代码追溯矩阵 + CI 一致性检查（把 `check_usecase_model.py` 接入 CI） |

**规模警戒（硬规则）**：大型多模块项目上用例遗漏是系统性的，不是偶发。标准档以上**必须分模块推进，并强制声明覆盖率与未覆盖区域**——不允许对大仓库笼统宣称"重建了用例模型"。`scripts/inventory_entrypoints.sh` 在源文件数 ≥ 1500 时会主动打印这条警戒。

各骨架文件的职责不是任意分工，直接复制填写：

| 文件 | 职责 |
|---|---|
| `uc-manifest.yaml` | 机器可读字段契约，`check_usecase_model.py` 校验的对象 |
| `USE-CASES.md` | 速览档：单页产出，内容项不减、每项从简 |
| `UC-00-overview.md` | 标准档：范围目的、取证路径理由、最危险发现、规模与覆盖率声明 |
| `UC-1x-usecase-TEMPLATE.md` | 标准档：单用例模板，复制为 `UC-XX-<slug>.md`，一个用例一份 |
| `UC-90-traceability.md` | 标准档：用例↔入口点↔代码追溯矩阵——应由 manifest 生成，手工誊抄的矩阵会在 manifest 改动后脱节 |
| `UC-99-gaps.md` | 标准档：缺口与七类尖锐发现，逐类占一节，无发现的类别写"本次未发现" |

## 工作流

### Step 0 — 定目的

目的不同，该恢复的层次完全不同：

| 目的 | 侧重 |
|---|---|
| 接手维护无文档系统 | 用例全集 + actor 边界 + 偏离清单 |
| 补需求文档（交接） | 用例模型 + 关键用例场景规格 |
| 测试覆盖分析 | 用例 ↔ 测试对照，缺失的变体 |
| 重写 / 迁移 | 行为契约全集 + §9.6.12 五项细节 |
| 安全审计 | actor 边界、越权路径、输入校验缺口 |

用户没说清就先问——目的错了后面全部白做。若用户明确要求不打断，默认按"接手维护"取，并在文档头声明这个假设。

目的也决定尖锐发现该优先扫哪几类：测试覆盖分析优先看扩展流缺失，安全审计优先看 actor 越权与输入校验缺口——七类都要扫，但优先级不是均等的。

### Step 1 — 文档清点与取证路径确认【交互确认点】

这是本 skill 最容易被跳过、也最不能跳过的一步：文档不只是参考资料，它是**目标层的唯一证据来源**。先跑：

```bash
bash scripts/inventory_docs.sh <repo-root>
```

它清点用户面文档、需求/用例痕迹、行为契约、变更叙述四类证据，给出类似下面的判定：

```
建议取证路径: 路径 A（有文档，强证据）
  → 从文档提取用户目标候选，再逐条用代码校验
  → 强证据来自 section [3] 行为契约
```

**跑完之后，必须向用户明示清点结果，并请其补充仓库外材料**（内部 wiki、设计评审记录、产品文档）——用户往往知道脚本看不到的东西。这个确认点不能省：路径判错，目标层就全是编的。不要在没有用户回应的情况下径直进入 Step 2。

### Step 2 — 按档取证（三档，不是两条路径）

档位由**证据强度**决定，不由文档有无决定——一个裸 README 加空 `docs/` 目录在多数仓库都存在，若按"有无文档"二分会把绝大多数项目错判为强证据：

| 档 | 触发条件（`inventory_docs.sh` 的 section） | manifest `evidence_path` | 目标层置信度上限 |
|---|---|---|---|
| A 强证据 | [2] 需求与用例痕迹 **或** [3] 行为契约 命中 | `strong` | `inferred_high` |
| A− 弱证据 | 上述均未命中，但 [1] 用户面文档 **或** [4] 变更叙述 命中 | `weak` | `inferred_medium` |
| B 无文档 | 四类全无命中 | `none` | `inferred_low` / `gap` |

- **A 档**：从文档与行为契约提取用户目标候选，逐条用代码校验——代码不支持的剔除（记入尖锐发现 #1）；代码里有但文档没记的补充（记入尖锐发现 #2）；目标层标 `inferred_high`，注明出处。
- **A− 档**：仍按 A 档流程提取候选，但目标层只能标 `inferred_medium`，并在产出中写明"本项目无需求文档与行为契约"；优先去找 e2e/BDD 测试与 API 契约以升档。
- **B 档**：主证据换成公开 API 契约 + 测试用例（29148 A.2.7 自陈场景"can serve as the basis for developing acceptance test plans"，此处反向使用）；目标层只能标 `inferred_low` 或 `gap`，**不要伪造目标层**。

三档判据、升档路径、七类证据源的性价比与陷阱检出方式，见 `references/evidence-discipline.md`。

**仓库级判定不是逐条断言的免检许可。** 仓库判为 A 档，不代表其中每一个用例的目标都自动是 `inferred_high`——某个候选如果只在代码里有对外行为、文档与行为契约都没提到它，仍应按实际拿到的证据核定置信度，可能只是 A 档仓库里的一条 `inferred_medium`。反过来，B 档仓库里若某条测试恰好是完整的 BDD feature，这一条目标仍可以标 `inferred_high`。仓库级判定只定默认策略与预期基线，逐条置信度必须回到"这一条具体拿到了什么证据"上核定。

### Step 3 — 系统操作清单（事实层）

```bash
bash scripts/inventory_entrypoints.sh <repo-root>
```

机械列出 HTTP 路由、CLI 子命令、消息消费者、定时任务、RPC 方法；库类项目退化为导出符号列表（噪音大，需按 §18.1.3.1 完整性判据筛）。**此步只产出可 `file:line` 指认的对外入口，不做任何用例判断**。脚本同时给出规模分级建议，对应上一节的三档。

需要按语言更精确的入口点/导出符号提取手段（如 `go doc`、`javap -public`、`cargo public-api`）与调用图工具，见 `references/tooling.md`——先 `--version` 跑通再依赖它，不保证每个工具在你读到时仍活跃维护。**动态分析默认不在本步流程内**：设计一个"只触发目标 feature"的执行场景，本身要求先知道 feature 是什么，而这正是本 skill 待产出的东西，构成循环依赖；只有系统可运行且用户明确要求深度验证时才作为补充手段（见 Step 8 之后的验证一节），不是默认流程的一步。

库类项目的导出符号总数与最终候选用例数的比值过大，是筛选没做够的信号——这是 B 档的主要难点，也是产出评审时该重点核对的地方，别把清点噪音直接当候选清单交出去。

### Step 4 — 聚合成用例（假说层）

**必须在 Step 3 之后进行，顺序不能颠倒。** 先机械列出操作，再用完整性判据把操作聚合成用例，而不是让模型直接对着代码"想"出一份用例清单——这正是 UCRBench 论文点名但未实现的"code-guided decomposition"。颠倒顺序是粒度失控的直接原因：先想用例名再找证据，判据就沦为事后合理化；Xpipe 案例的 2103 个「Check GPU」类条目，本质是把操作清单本身当成了用例清单，跳过了这一步聚合。

用完整性判据（第二节）给出 actor（推断）与用例名（动词开头）；两个都通过判据的候选是否要合并，用 `no_association_to_use_case` 的辅助判据核对（`references/granularity.md` 四）。CRUD 类目标按惯例合并为 `Manage <X>`（若项目存在 `standards/01-requirements/`，对应 REQ-N04，见文末）。

未通过完整性判据的候选不必自动升格为独立条目——只有当它被两个以上 `user_goal` 用例共同依赖、值得作为可复用部分单独命名时，才登记为 `level: subfunction` 并用 `includes` 关联（UML §18.1.3.3）；某段行为脱离基用例仍有独立意义则登记为 `extends`（§18.1.3.2）。只在一个用例内部出现一次的步骤，直接写进该用例的 `function_details` 或场景 `steps` 即可，不必单独建条目。

### Step 5 — 场景与变体

按 29148 A.2.7：每个场景 step-by-step 描述，含 events/actions/stimuli/information/interactions；对每个 `user_goal` 用例考察 normal/stress/exception/degraded 四类变体，缺哪类记入尖锐发现 #3（`subfunction` 级不强制场景，见 `granularity.md` 五）。覆盖要求：所有 operational_modes × 所有 user_classes。场景须唯一命名与编号（§9.4.17，Step 8 的脚本会核查场景 id 重复与 variant 取值合法性）。

### Step 6 — 功能细节逐条盘问

对每个 `user_goal` 用例过 29148 §9.6.12 五项：a) 输入有效性校验、b) 精确的操作序列、c) 异常响应（溢出/通信故障/硬件故障/错误处理与恢复）、d) 参数的作用、e) 输出与输入的关系。逐条填写或显式写"未发现"——跳过与"已核实无此机制"在读者眼里无法区分。这一步与 `architecture-reconstruction` 的路径逐条盘问共享同一批证据（入参提取器、错误处理分支、上限与默认值），取证方式可复用。

### Step 7 — 偏离、缺口与契约违背

单列一节：七类尖锐发现、未覆盖区域及原因、目标层缺口声明、as-documented vs as-built 差异（例如 README 说"支持批量导入"，代码里只有单条导入接口——这类差异逐条列出，附两边证据，不要含糊过去）。复制 `assets/uc-skeleton/UC-99-gaps.md` 作为骨架，无发现的类别不要删除该节，写"本次未发现，已逐类自检"。

### Step 8 — 机械校验与自检

```bash
python3 scripts/check_usecase_model.py <uc-dir-or-manifest>
```

核对 UML 四条 OCL 约束（`must_have_name`/`cannot_include_self`/`no_association_to_use_case`/`binary_associations`）、粒度纪律（`user_goal` 级须有 `completeness_check`）、证据纪律（`goal_confidence`/`actor.confidence` 不得为 `fact`），以及 29148 场景变体覆盖与 §9.6.12 五项完整性——脚本自带 25 项 pytest 测试锁定这些判定逻辑。违规退出码非零，可接入 CI（完整档）。再过下一节的自检清单。

## 自检清单

交付前逐条核对（与 `references/content-items.md` 末尾的清单一致，便于脱离本文件单独核对）：

- [ ] 每条实质断言归入【事实】/【推断】/【缺口】之一
- [ ] 所有【事实】有 `file:line` 与依据 commit
- [ ] 用例名与 actor 目标没有被标为事实
- [ ] 每个用例通过完整性判据（执行后可重新发起 / 错误态）
- [ ] 产出中无数据库表名、内部类名、SQL、私有函数名
- [ ] 每个用例考察过四类变体，缺失的已记录
- [ ] §9.6.12 五项对每个用例逐条过过
- [ ] 场景唯一命名与编号
- [ ] 七类尖锐发现逐类扫过，每条写明"谁会做出错误判断"
- [ ] 最危险的发现出现在前两屏
- [ ] 一致性局限在文档头一次性声明
- [ ] 无文档项目未伪造目标层
- [ ] 大项目已声明覆盖率与未覆盖区域
- [ ] §5.2.6 Complete 冲突已声明（重建产出必然含 TBD）

## 验证：不要停在纸上

重建结果需要验证，两个可行手段：

1. **找维护者 review**：把置信度最低、影响最大的几条用例假说整理成具体问题（"这个操作是给谁用的"而不是笼统的"对不对"），去项目 issue/discussion 里问维护者，比反复推敲证据链更快，也是把【缺口】变成【推断】甚至【事实】的最直接路径。
2. **跑一遍对应的 E2E 测试**：按重建的用例找到覆盖它的既有 E2E/集成测试，实际跑一遍，看行为是否与场景描述一致——不一致要么是重建错了，要么是本身就是一条尖锐发现，两种情况都要更新产出，不要视为噪音略过。

## 参考资料

需要更深内容时按需读取，不要一次性全读：

- `references/content-items.md` — UML §18 与 29148 A.2.7 / §9.4.17 / §9.6.12 / §5.2.5–5.2.6 的逐条要求、shall/should 区分、完整自检清单
- `references/granularity.md` — 完整性判据的详细判定流程、双向粒度失控的识别、正反例各 5 组
- `references/evidence-discipline.md` — 三级标记、三档取证路径的取舍、证据源清单及陷阱、置信度判据表
- `references/tooling.md` — 按语言（Go/Java/Python/TS-JS/Rust/Ruby）的入口点与导出符号提取工具、动态分析为何不在默认流程内

四份互不重复彼此的细节：条款原文查 `content-items.md`，粒度判据查 `granularity.md`，取证与置信度查 `evidence-discipline.md`，语言专属工具查 `tooling.md`——交叉引用点见各自开头。

若项目存在 `standards/01-requirements/`（或 CLAUDE.md 中声明的 `$STD`），一并检索并在产出中标注其条目 ID（如 `REQ-N03` 用例命名动词开头、`REQ-N04` CRUD 合并、`REQ-N06` 黑盒用例），使结论可回溯到项目自己的规范依据。不存在则静默跳过——本 skill 自身完备，不依赖它。
