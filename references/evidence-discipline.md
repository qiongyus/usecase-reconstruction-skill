# evidence-discipline.md — 证据纪律、取证路径、置信度判据

本文覆盖四件事：三级标记在用例场景下的用法、本 skill 特有的目标层推断硬规则、按证据强度分三档的取证路径与升档路径、证据源清单及其陷阱，末尾给出置信度判据表。与 `content-items.md`（内容项逐条）、`granularity.md`（粒度判据）配套，三者合起来是 `SKILL.md` 引用的完整参考层，本文不重复它们已讲透的内容（UML/29148 条款原文见 `content-items.md`；完整性判据与粒度失控见 `granularity.md`）。

## 一、三级标记

正文每条实质断言归入【事实】【推断】【缺口】之一，格式沿用 `architecture-reconstruction/SKILL.md` 的约定，例子换成用例重建场景：

```markdown
【事实】`DELETE /orders/{id}` 已注册路由；处理函数在订单不存在时返回 404，
        存在时标记取消、释放库存、发出取消事件、返回 204
        （`internal/http/orders.go:88-114`）

【推断】该路由对应用户目标「取消订单」。依据：CHANGELOG.md:34「支持取消未
        发货订单」与该路径行为吻合，`docs/api.md#cancel-order` 有同名小节
        描述参数与返回码；置信度：inferred_high（A 档，行为契约与用户面
        文档双重印证）

【缺口】发起取消操作是否需要额外审批未知（原因：仓库内无权限矩阵或角色
        文档；可能获取途径：产品经理访谈、内部工单系统的历史 ticket）
```

三条硬规则沿用 AR，不重复展开：`file:line` 是【事实】的唯一凭据；【推断】必须写推理链与置信度，不能只写结论；【缺口】是一等产出，不是失败。

## 二、本 skill 特有的硬规则：用例名与 actor 目标恒为推断

> **用例名与 actor 目标恒为推断，不得标为【事实】。**

依据【一手，UML 2.5.1 §18.1.3.1】：

> An Actor models a type of role played by an entity that interacts with the subjects of its associated UseCases … **a single physical instance may play the role of several different Actors and, conversely, a given Actor may be played by multiple different instances.**

代码里能读到的只是物理接口（HTTP 客户端、CLI 调用者、消息生产者、定时器）与它们触发的执行路径；一个物理接口可能扮演多个角色（同一 API token 既服务自动化脚本也服务人工操作），一个角色也可能由多个物理接口共同扮演（Web 前端与移动 App 都在扮演「顾客」）。接口与角色是多对多映射，无法从代码单义推出，这是结构性的，不是证据不够多的问题——证据再多也推不出「唯一正确」的角色划分，恒为推断。

对应 manifest 字段：`actors[].confidence`、`use_cases[].goal_confidence`，合法取值仅 `inferred_high` / `inferred_medium` / `inferred_low` / `gap`，`fact` 不在其中；`scripts/check_usecase_model.py` 的 `check_uml` 会对 `goal_confidence == "fact"` 与 `actor.confidence == "fact"` 直接报错。

## 三、取证路径的取舍：三档，不是两档

### 3.0 为什么是三档

最初的设计只按「有文档 / 无文档」分两条路径，由 `inventory_docs.sh` 命中的文档类别数判定。这个判定被证伪：一个裸 `README.md` 加一个空 `docs/` 目录就足以命中「[1] 用户面文档」这一类别，而这两样在维护中的仓库里近乎普遍存在——二分判定会把绝大多数项目都判成「有文档」，进而把目标层置信度系统性地标成 `inferred_high`。这恰好架空了本节要守的前提：**文档是目标层的唯一证据来源，证据强度不足就不该给高置信度。**

现行判定改为三档，**档位由证据强度决定，不由文档有无决定**：

| 档 | 触发条件（`inventory_docs.sh` 的 section） | 目标层置信度 |
|---|---|---|
| **A 强证据** | [2] 需求与用例痕迹 **或** [3] 行为契约 命中 | `inferred_high` |
| **A− 弱证据** | 上述均未命中，但 [1] 用户面文档 **或** [4] 变更叙述 命中 | `inferred_medium` |
| **B 无文档** | 四类全无命中 | `inferred_low` / `gap` |

### 3.1 A 档（强证据）：需求文档、BDD feature、e2e 测试或 API 契约

流程与 UCRBench 论文人工构造 ground truth 的做法一致（引其**方法**，非其分数；该论文的粒度失控数据已见 `granularity.md` 二，此处不重复）：

1. 从文档与行为契约提取用户目标候选；
2. 逐条用代码校验——代码不支持的剔除（记入尖锐发现 #1）；actor 或命名与代码有出入的以代码为准修正；代码里有但文档没记的补充（记入尖锐发现 #2）；
3. 目标层标 `inferred_high`，**注明出处位置**（文字出处或 file:line，二者都要能指认）。

### 3.2 A− 档（弱证据）：只有 README / docs / CHANGELOG

README 能提供「这个工具是干什么的」这类线索，但支撑不了具体的用例目标——这正是它区别于需求文档与行为契约的地方，也是这一档单独存在的理由。

- 仍按 A 档流程提取并校验目标候选，但**目标层只能标 `inferred_medium`**；
- 产出中须写明：本项目无需求文档与行为契约，目标层的依据仅为用户面描述；
- **优先行动**：去找 e2e/BDD 测试与 API 契约——找到任意一项即可升档到 A（对应字段改标 `inferred_high` 并补上新出处），这是本档的标准升档路径。

产出中的声明示例：

> 本项目仅有 README 与 `docs/`，未见需求文档、BDD feature、e2e 测试或 API 契约；以下 actor 目标与用例目标均标 `inferred_medium`，出处见各条 `evidence`/`source` 字段。若后续找到 e2e/BDD 测试或 API 契约，应重新核验并按情况升档。

### 3.3 B 档（无文档，常见于库类 / 工具类项目）

主证据换成**公开 API 契约 + 测试用例**：

- **API 契约**：导出符号的签名、类型、文档注释；
- **测试用例是场景的最硬证据**——29148 A.2.7 自陈场景「… **can** serve as the basis for developing acceptance test plans」【一手，29148:2018 Annex A.2.7】，措辞是 `can`，比 `should` 更弱，标准本身只承认这是场景的一种可能用途；本 skill 反向使用这条弱关联，把既有验收测试当作场景的硬证据。E2E / 集成测试 / BDD feature 文件优先于单元测试；
- 目标层只能标 `inferred_low` 或 `gap`。**无文档时不要伪造目标层。**

各档产物不同：A 与 A− 产出**目标候选清单**（待与 Step 3 的操作清单对齐）；B 没有目标候选，只能在聚合阶段从操作反向归纳。

## 四、证据源清单（按性价比排序）与陷阱

### 1. BDD feature 文件 —— 几乎是场景的可执行编码

Gherkin 的 `Given/When/Then` 结构本身就是 29148 A.2.7 要求的「events, actions, stimuli, information」的现成对照物，`Scenario:` 标题常常直接可用作场景名候选。

**陷阱**：feature 文件可能早已废弃却未删除。**怎么检出**：`grep -rn '@wip\|@skip\|@ignore\|@pending' features/` 找标签；再确认它是否在 CI 里被实际执行（`grep -rn 'cucumber\|behave' .github/workflows/ Makefile`）。没被跑的 feature 只能降级为草稿性证据，不能当强证据支撑 `inferred_high`。

### 2. E2E / 集成测试

覆盖真实调用链的测试断言，是场景 `steps` 与 `function_details` 的直接原料。

**陷阱**：测试可能已失效或被跳过。**怎么检出**：`grep -rn 't\.Skip(\|@pytest\.mark\.skip\|\.skip(\|xfail' <test-dir>`；命中后用 `git log -1 --format=%ad -- <file>` 看跳过标记加上的时间——跳过的测试只能证明「曾经的意图」，不能当作当前行为仍然成立的证据，需要降级或在缺口中说明。

### 3. OpenAPI / proto / GraphQL 契约

字段类型与错误码是 `function_details` a)/e) 两项的直接来源。

**陷阱**：契约可能是手写的而非从代码生成，因而与实现脱节。**怎么检出**：查构建脚本里有没有生成步骤（`grep -rn 'protoc \|buf generate\|openapi-generator' Makefile .github/workflows/ scripts/`）；找不到生成步骤，契约与实现的同源性就不能默认成立，需抽样核对几个 handler 的入参/返回字段是否真的匹配契约声明再决定信任等级。

### 4. 路由表

HTTP 路由注册表、CLI 子命令列表是 Step 3 的事实层材料（`inventory_entrypoints.sh` 产出），它证明「这个操作存在」，不直接证明「这是为了什么」。路径命名（如 `/orders/{id}/cancel`）可以作为目标候选的弱线索，但单独不足以支撑到 `inferred_high`。

### 5. README

**陷阱**：描述可能滞后于代码。**怎么检出**：把 README 提到的每个功能点与 Step 3 操作清单逐条对照——README 提了但代码里找不到对应入口，记入尖锐发现 #1（宣称但不存在）；代码里有但 README 未提，记入尖锐发现 #2（存在但无人知晓）。

### 6. CHANGELOG / NEWS / RELEASE

**陷阱**：通常只记录「变化」，遗漏项目从一开始就有、从未在 CHANGELOG 出现过的核心能力，不能靠它的覆盖率反推功能覆盖率。措辞也偏向维护者视角（"fix"/"refactor"），填入 `actor.goal` 前需要转译成用户目标表述。

### 7. issue 模板

反映的是「报告问题 / 提需求时该填什么字段」，价值弱于前六项，只能作为 actor 类别（谁在报 bug、谁在提功能请求）的旁证，不单独支撑目标层置信度。

### 陷阱检出与尖锐发现的关系

第 2 条（测试被跳过）与第 3 条（契约手写脱节）不只是降置信度的理由，检出过程本身常常直接产出设计文档 §4 的尖锐发现：一个长期挂着 `@pytest.mark.skip` 的异常路径测试，多半对应「扩展流缺失」（尖锐发现 #3）——不是测试没写，是曾经写过又被静默跳过；一个契约字段在实现里查不到对应校验，往往就是「输入校验缺口」（尖锐发现 #7）。取证时顺手记录这些关联，比事后单独再扫一遍更省力。

## 五、置信度判据表

`use_cases[].goal_confidence` 与 `actors[].confidence` 共用同一套取值与判据，均与三档取证路径一一对应：

| 置信度 | 判定条件 |
|---|---|
| `inferred_high` | A 档：目标候选来自 [2] 需求/用例痕迹 或 [3] 行为契约，经代码逐条校验（剔除 / 修正 / 补充）后仍成立，且已注明出处 |
| `inferred_medium` | A− 档：仅 [1] 用户面文档 或 [4] 变更叙述支持，未见需求文档、BDD、e2e 或 API 契约；或强证据存在但校验后出入较大、需大幅修正，出处的确定性打了折扣 |
| `inferred_low` | B 档：无任何文档类证据，目标从公开 API 契约与测试用例反向归纳得到——有合理依据，但没有某处文字明确陈述过这个目标 |
| `gap` | 操作本身已通过事实层证据成立（有 file:line），但连反向归纳的依据都没有——不知道谁在用、为什么用；如实标缺口，不编造 |

`goal_confidence` 与 `granularity.md` 一 的完整性判据（`completeness_check`）互不替代：前者约束「这条用例对 actor 有什么价值」的证据强度，后者是结构性判据，判断候选是否够格成为独立用例，两条判据服务于不同字段，须分别核对，不能用一个满足另一个。

**三档是 `inventory_docs.sh` 给出的仓库级建议起点，不是逐条断言的免检许可。** 同一个仓库判为 A 档，不代表其中每一个用例的目标都自动是 `inferred_high`——如果某个候选只在代码里有对外行为、文档与行为契约都没提到它，它仍应按第四节的证据源逐条核实，置信度按该条目实际拿到的证据打，可能是 A 档仓库里的一条 `inferred_medium` 甚至 `inferred_low`。反过来，B 档仓库里如果某条测试恰好是完整的 BDD feature，这一条目标仍可以标 `inferred_high`。仓库级判定用于确定默认取证策略与预期基线，逐条置信度必须回到「这一条具体拿到了什么证据」上核定。
