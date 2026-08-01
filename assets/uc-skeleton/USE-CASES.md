# <系统名> 用例模型（速览档）

> **依据版本**：`<branch>` `<短 sha>`（YYYY-MM-DD）｜**分析日期**：YYYY-MM-DD｜路径相对 `<repo-root>`
> **组织依据**：UML 2.5.1 §18 + ISO/IEC/IEEE 29148:2018 Annex A.2.7 / §9.6.12（速览档：内容项不减，每项从简；逐条索引见 `references/content-items.md`）。
> **证据等级**：【事实】附 `file:line`；【推断】附推理链与置信度；【缺口】说明原因。
> **取证路径**：`evidence_path: <strong|weak|none>`（判定理由写在 §1 或本行之后；本档不单列该小节，升到标准档时对应 `UC-00-overview.md` §2）。
> **置信度取值**：`inferred_high | inferred_medium | inferred_low | gap`（`fact` 不合法——用例名与 actor 目标恒为推断，见 `references/evidence-discipline.md` 二）。

## 1. 系统对外提供什么

<一句话说清这个系统对外（对 actor）提供什么可观察的价值。不描述内部实现，只描述黑盒行为——UML §18.1.3.1 要求用例"without reference to its internal structure"。>

## 2. 最危险的发现

> 放在这里而不是文末——读者只读前两屏也必须看到。逐类自检过一遍（七类判据同标准档 `UC-99-gaps.md`，本档不单列该文件）：
> 宣称但不存在 ／ 存在但无人知晓 ／ 扩展流缺失 ／ 异常被吞 ／ 后置条件在失败路径下不成立 ／ actor 越权 ／ 输入校验缺口。

| # | 发现 | 类型 | 谁会因此做出错误判断 | 详情 |
|---|---|---|---|---|
| F1 | 【事实】<例：`POST /orders` 的库存校验只在成功分支执行，异常分支直接吞掉校验错误并返回 200>（`path:line`） | <异常被吞> | <集成方以为下单一定成功，实际库存未扣减> | 标准档见 `UC-99-gaps.md` §<n> |

<无发现时不要删除本节——显式写「本次未发现尖锐发现，已逐类自检」，并说明自检覆盖了哪些用例。>

## 3. Actor 清单

<全为反推；来自代码里的物理接口（HTTP 客户端、CLI 调用者、消息生产者、定时器）与文档线索的映射。恒不得标为【事实】。>

| id | 角色名 | kind | 目标（goal） | 置信度 | 出处 / 证据 |
|---|---|---|---|---|---|
| `<actor-id>` | <角色名> | human / external_system / timer | <该 actor 想达成什么> | `<inferred_high\|inferred_medium\|inferred_low\|gap>` | `<file:line>` 或 `<README.md:12>` |

## 4. 用例清单

| id | 名称 | actor | 入口点 | 完整性判定 | 目标置信度 |
|---|---|---|---|---|---|
| UC-01 | <动词开头的用例名> | `<actor-id>` | `<HTTP 路由 / CLI 子命令 / 导出符号>` | <执行后 subject 是否处于「无待续输入、可重新发起」或错误态——一句话判定理由，详细判据见 `references/granularity.md` 一> | `<inferred_high\|inferred_medium\|inferred_low\|gap>` |

<规模声明：user_goal 级 <N> 个 / subfunction 级 <M> 个。若表格过长，只列 user_goal 级，subfunction 级列表放标准档 UC-90。>

## 5. 关键用例的场景与四类变体

<挑 1–3 个对读者最要紧的用例展开；其余用例本档不逐一展开完整场景——升级到标准档后，每个用例复制标准档模板 `UC-1x-usecase-TEMPLATE.md` 得到各自独立的 `UC-1x-*.md`。>

### UC-01 <用例名>

- **normal**：<正常路径一句话概述，或链接到 UC-1x §4.1>
- **stress**：<压力路径概述，或「代码中无对应路径」——记入本档 §6 缺口与偏离>
- **exception**：<异常路径概述，或对应缺失说明>
- **degraded**：<降级路径概述，或「代码中无对应路径」——记入本档 §6 缺口与偏离>

## 6. 缺口与偏离

<汇总，不重复标准档全文。>

| 类型 | 内容 | 详情 |
|---|---|---|
| 未覆盖区域 | <哪部分代码/哪些用例没看> | 标准档见 `UC-99-gaps.md` §1 |
| 宣称但不存在 | <README/文档提到但代码里找不到> | 标准档见 `UC-99-gaps.md` §2 |
| 目标层缺口 | <哪些用例目标标了 gap，为什么> | 标准档见 `UC-99-gaps.md` §<n> |

## 7. 一致性局限声明（一次性）

本产出对 UML 2.5.1 §18 与 ISO/IEC/IEEE 29148:2018 均不能声明"一致"：UML §18 没有"conformance"这种表述，四条 OCL 约束（`scripts/check_usecase_model.py` 的 `check_uml`）核对的是结构合规，不等于"忠实反映了系统"；29148 的 full conformance 与 tailored conformance（Annex C）在逆向重建场景都不可达——原始干系人、需求过程、Annex C.2.3 要求的"各方输入"均不存在。§5.2.6 Complete 要求"不含 TBD"与本 skill 的缺口纪律（显式标注【缺口】）结构性冲突，本产出选择满足缺口纪律，即对 §5.2.6 不满足，理由见标准档 `UC-99-gaps.md` 末节（本档不单列该文件）。本清单只当完备性检查表用，详见 `references/content-items.md` 第三节。本声明只在本节出现一次，正文不重复。
