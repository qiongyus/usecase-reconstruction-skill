# content-items.md — UML 2.5.1 §18 与 ISO/IEC/IEEE 29148:2018 内容项逐条

本文是 usecase-reconstruction 产出的内容项清单与依据索引，`SKILL.md` 在需要条款细节时指向这里。用途与 `architecture-reconstruction/references/ad-content-items.md` 一致：**当完备性检查表用，不是模板**。

## 依据地位（一次性声明，后文不逐条重复）

- 用例模型结构 —— UML 2.5.1 §18（【一手】，OMG `formal/17-12-05`，796 页，免费公开）
- 场景与功能细节 —— ISO/IEC/IEEE 29148:2018 §5、§7、§9、Annex A.2.7、Annex C（【一手】）
- 用例文本排版惯例（brief/casual/fully dressed、REQ-N 系列命名与合并规则）—— Cockburn《Applying UML and Patterns》3rd ed.（【二手】，见 `standards/01-requirements/norms.md`）。UML 与 29148 均不规定用例文本的排版格式，见下方「§18.1.3.2 用例文本格式」一节。

**一致性声明的诚实形态**（详见文末第三节）：本文档清单可以当完备性检查表用；对 29148 声明"完全一致"或"裁剪一致"两者都做不到。以下逐条讲解时不再重复此限制，只在此处与文末各声明一次。

## 一、UML 2.5.1 §18 逐条

### §18.1.3.1 用例的语义（定义性）

原文：

> A UseCase … specifies a set of behaviors performed by that subject, which **yields an observable result that is of value for Actors or other stakeholders** of the subject.

> UseCases define the offered Behaviors of the subject **without reference to its internal structure**.

对重建的含义：用例的定义性要素是"对 actor 有价值的可观察结果"——而**价值不在代码里**，只能推断，对应 manifest `use_cases[].goal_confidence` 恒不得取 `fact`（合法取值：`inferred_high` / `inferred_medium` / `inferred_low` / `gap`）。第二句是黑盒描述的规范依据（不是 Cockburn 的实践建议）：产出中出现数据库表名、内部类名、SQL、私有函数名即违规。

原文（完整性判据，唯一可判定的一句）：

> This functionality must always be completed for the UseCase to complete. It is deemed complete if, after its execution, the subject will be in a state in which **no further inputs or actions are expected and the UseCase can be initiated again, or in an error state**.

对应 manifest `use_cases[].completeness_check`——`user_goal` 级用例必须写出判定理由。详细判定流程见 `granularity.md`。

原文（变体属于用例本身）：

> A UseCase can include possible variations of its basic behavior, including **exceptional behavior and error handling**.

对应 manifest `use_cases[].scenarios` 列表；四类变体的规范依据在 29148 Annex A.2.7（见下）。

### §18.1.3.1 Actor 的语义

原文：

> An Actor models **a type of role** played by an entity that interacts with the subjects of its associated UseCases … a single physical instance may play the role of several different Actors and, conversely, a given Actor may be played by multiple different instances.

对重建的含义：actor 是角色而非物理实体；代码里只有物理接口（HTTP 客户端、CLI 调用者、定时器），接口↔角色是多对多映射，恒为推断。对应 manifest `actors[].confidence`，同样不得取 `fact`。

### §18.1.3.2 Extend

原文：

> The extended UseCase is defined independently of the extending UseCase and is **meaningful independently** of the extending UseCase. On the other hand, the extending UseCase typically defines behavior that **may not necessarily be meaningful by itself**.

对重建的含义：判断一段行为是"独立用例"还是"某用例的 extend"，看它脱离基用例是否仍有意义。对应 manifest `use_cases[].extends`（被扩展用例的 id 列表）。

### §18.1.3.3 Include

原文：

> … what is left in a base UseCase is **usually not complete in itself** but dependent on the included parts to be meaningful.

对应 manifest `use_cases[].includes`。§18.2.5.6 的 `cannot_include_self` 约束禁止直接或间接自包含。

### §18.1.3.2 用例文本格式：UML 不规定

原文：

> The specific manner in which the location of an ExtensionPoint is defined is **intentionally unspecified**. This is because UseCases may be specified in **various formats such as natural language, tables, trees, etc.**

字面讨论的是 extension point 的定位方式，但随附的一般性说明确认了一个更宽的事实：**UML 不规定用例文本的排版格式**。"前置条件 / 主成功场景 / 扩展 / 成功保证"这套模板出自 Cockburn (2001)【二手】（对应 `standards/01-requirements/norms.md` 的 REQ-N02、REQ-N08、REQ-N09），不是 UML 的规范要求——本 skill 采用与否是排版选择，不是合规要求。

### §18.2.5.6 四条 OCL 约束

| 约束 | 原文（节录） | manifest 对应字段 |
|---|---|---|
| `must_have_name` | "A UseCase must have a name." | `use_cases[].name` |
| `cannot_include_self` | "A UseCase cannot include UseCases that directly or indirectly include it." | `use_cases[].includes` |
| `no_association_to_use_case` | "UseCases cannot have Associations to UseCases specifying the same subject." | `use_cases[].associations`（恒为空列表，见下） |
| `binary_associations` | "UseCases can only be involved in binary Associations." | `use_cases[].actors`（用例须关联至少一个 actor） |

`no_association_to_use_case` 的语义根据——每个用例各自 "describes a complete usage of the subject"（§18.1.3.1）——是 `granularity.md` 辅助判据的直接出处：manifest 把 `associations` 恒设为空列表；若代码证据显示两个候选用例之间存在关联，应视为建模错误并拆分/合并，而不是把用例 id 填进该字段。

这四条是规范性 OCL 不变式（`inv:`），本身即为强制，无 shall/should 之分。

## 二、ISO/IEC/IEEE 29148:2018 逐条

### use case 在 29148 中是边缘概念

全文仅 4 处提及 "use case"：

| 位置 | 原文 |
|---|---|
| §5.2.4 需求构造 | "Condition-action tables and **use cases are other means of capturing requirements**." |
| §6.3.3.4（制定运行概念） | "Use case approaches can also be used to define concept documents. Under this approach, a set of actors (systems and classes of people that interact with the system) is identified, along with their **goals, purposes and needs** for the system. The use cases are analyzed to identify stakeholder requirements." |
| §9.6.5 产品功能 | "Use cases, user stories and scenarios are also used to describe product functions." |

即 29148 把用例当作**手段之一**，不规定其内容结构——真正的规范性内容在 **scenario**（Annex A.2.7、§9.4.17）与 **function**（§9.6.12）名下，不在"use case"名下。这正是本 skill 把场景层锚定在 A.2.7 而非某个"用例条款"上的原因。

（旁证：§6.3.3.4 称 actor 是 "systems and classes of people"，UML §18.1.3.1 强调 actor 是 "role"——两处定义措辞有出入，29148 未展开说明，此处如实标注差异，不强行调和。）

### §4 一致性

§4.1：

> This document also provides **normative definition of the content** and recommendations for the format of the information items…

内容是规范性的，格式只是建议——与 UML §18.1.3.2 的"不规定格式"互补。

§4.2 full conformance 要求同时满足四项：

1. §5.2.4、5.2.5、5.2.6、5.2.7 的条款；
2. §6.1 引用的 ISO/IEC/IEEE 15288、12207 相关过程；
3. §7 规定的信息项；
4. §9 与 Annex A 规定的信息项内容。

§7（shall）：

> The project **shall** produce the following information items … The information items **shall** contain the content as defined in Clause 9.

§4.5.2 指向 Annex C：不满足 full conformance 时，"the clauses of this document **shall** be selected or modified in accordance with the tailoring process prescribed in Annex C"。

**Annex C 的 tailored conformance 在重建场景不可达**：C.1 "If a claim of 'tailored conformance' is made, then the following process **shall** be applied"；C.2.3 的活动清单 b) 要求 "**Obtain input from all parties affected** by the tailoring decisions"。逆向重建没有这些"各方"（原始干系人已不可寻），所以连裁剪一致性也声明不了。

### Annex A.1 与 A.2.7：一条 shall，内部全是 should / may / can

Annex A.1（shall，Annex A 范围内唯一的强制措辞）：

> The information item content in A.2.7 **shall** be produced in the course of producing the Stakeholder Requirements Specification…

A.2.7 内部（组织方式，全部 should / may / can，不是 shall）：

- 定义："A scenario is a **step-by-step description** of how the proposed system should operate and interact with its users and its external interfaces under a given set of circumstances."
- "Scenarios **should** be organized into sections and subsections…"
- 覆盖要求："Operational scenarios **should** be described for **all operational modes and all classes of users** identified for the proposed system." —— 对应 manifest 顶层 `operational_modes` × `user_classes` 的覆盖矩阵。
- "Each scenario **should** include **events, actions, stimuli, information and interactions**…"
- 四类变体（"may be necessary"，非 shall/should）："it may be necessary to develop several variations of each scenario, including one for **normal operation**, one for **stress load handling**, one for **exception handling**, one for **degraded mode operation**." —— manifest `scenarios[].variant` 的四个合法取值 `normal / stress / exception / degraded` 由此而来。
- "Scenarios may also be used to describe **what the system should not do**."
- "Scenarios … can serve as the basis for … developing **acceptance test plans**."（"can"，比 should 更弱）—— 标准自己建立的场景↔验收测试关联，反向支撑"E2E/BDD 测试是场景的最硬证据"这一取证策略。

**强制性小结**："必须产出场景内容"是 shall（Annex A.1）；"怎么组织、覆盖到什么程度、写不写反例、能不能拿来做验收测试"全是 should/may/can（A.2.7 内部）。把两者混为一谈是最容易犯的错误。

### §9.4.17 场景的唯一命名与编号

> Describe examples of how users/operators/maintainers will interact with the system in important contexts of use. … The scenario **should be uniquely named and numbered** and should be referenced in the description of the business processes in 9.3.10.

should，非 shall——但可机械检查，manifest `scenarios[].id` 的唯一性由 `check_29148()` 强制。

### §9.6.12 Functions a)–e)

> Define the fundamental actions that have to take place in the software in accepting and processing the inputs and in processing and generating the outputs, including:
> a) validity checks on the inputs;
> b) exact sequence of operations;
> c) responses to abnormal situations, including: 1) overflow; 2) communication facilities; 3) hardware faults and failures; and 4) error handling and recovery;
> d) effect of parameters;
> e) relationship of outputs to inputs, including: 1) input/output sequences; and 2) formulas for input to output conversion.

§9.6 各条目本身用祈使句（"Define…"），强制性来自 §9.6.1 的统领句"The project **shall** produce the following information item content"——条目不重复 shall，但整体是 shall 级。对应 manifest `function_details` 的五个子键 `input_validation` / `operation_sequence` / `abnormal_responses` / `parameter_effects` / `io_relationship`，与 architecture-reconstruction 的路径逐条盘问同构。

### §5.2.5 九项特性（shall）

> Each stakeholder, system and system element requirement **shall** possess the following characteristics.

Necessary、**Appropriate**、Unambiguous、Complete、Singular、Feasible、Verifiable、**Correct**、Conforming。

对重建的特殊含义：

- **Appropriate**："allowing **implementation independence** to the extent possible"——给"不许把实现细节写进用例"一个 shall 级依据，呼应 §18.1.3.1 的"without reference to its internal structure"。
- **Correct**："an accurate representation of the entity need **from which it was transformed**"——重建时原始 need 未知，此项结构上无法保证，须在缺口声明中列出，不能假装满足。

### §5.2.6 Complete 与缺口纪律的冲突

> Each set of requirements … **shall** possess the following characteristics. — Complete. … the set **does not contain any To Be Defined (TBD)**, To Be Specified (TBS), or To Be Resolved (TBR) clauses.

shall 级要求"不含 TBD"，而本 skill 的证据纪律要求把拿不到的内容显式标为【缺口】——重建产出必然含 TBD 类占位。这个冲突结构上无法消除，只能在文档头声明"本产出对 §5.2.6 Complete 不满足，原因是重建纪律要求显式标注缺口"，不要在正文悄悄抹平。

## 三、一致性声明的诚实形态

本 skill 的产出对 UML 2.5.1 §18 与 29148:2018 都不能声明"一致"：

- 对 UML：§18 是模型结构规范，不是文档一致性条款——UML 没有"conformance to §18"这种表述。四条 OCL 约束可以逐条机械核查（`scripts/check_usecase_model.py` 的 `check_uml`），但这只是**结构合规**，不等于"重建的用例模型忠实反映了系统"。
- 对 29148：full conformance 做不到——原始干系人、需求过程、§6.1 引用的生命周期过程都不存在于逆向场景。tailored conformance 也做不到——Annex C.2.3 要求 "Obtain input from all parties affected"，逆向重建没有这些"各方"。

诚实的处理方式：**把本文档的清单当完备性检查表用**——逐条核对产出是否覆盖了 §18 的模型要素与 29148 A.2.7 / §9.6.12 的内容项，但不对外宣称"符合 29148"或"符合 UML"。这条声明只在文档头与本节各出现一次，前文逐条讲解 shall/should 时不再重复。

## 四、完整自检清单

照搬设计文档 `docs/brainstorms/2026-08-01-usecase-reconstruction-design.md` §7，共 14 项：

- [ ] 每条实质断言归入【事实】/【推断】/【缺口】之一
- [ ] 所有【事实】有 `file:line` 与依据 commit
- [ ] **用例名与 actor 目标没有被标为事实**
- [ ] 每个用例通过完整性判据（执行后可重新发起 / 错误态）
- [ ] 产出中无数据库表名、内部类名、SQL、私有函数名（§3.3）
- [ ] 每个用例考察过四类变体，缺失的已记录
- [ ] §9.6.12 五项对每个用例逐条过过
- [ ] 场景唯一命名与编号
- [ ] §4 七类尖锐发现逐类扫过，每条写明"谁会做出错误判断"
- [ ] 最危险的发现出现在前两屏
- [ ] 一致性局限在文档头一次性声明
- [ ] 无文档项目未伪造目标层
- [ ] 大项目已声明覆盖率与未覆盖区域
- [ ] §5.2.6 Complete 冲突已声明（重建产出必然含 TBD）
