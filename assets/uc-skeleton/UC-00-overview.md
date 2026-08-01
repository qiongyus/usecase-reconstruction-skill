# <系统名> 用例模型 — 概述与阅读指引

> **依据版本**：`<branch>` `<短 sha>`（提交日期 YYYY-MM-DD）｜**分析日期**：YYYY-MM-DD
> 路径均相对于 `<repo-root>`。
> **组织依据**：UML 2.5.1 §18（模型结构）+ ISO/IEC/IEEE 29148:2018 Annex A.2.7、§9.4.17、§9.6.12（场景与功能细节）。逐条索引见 `references/content-items.md`。
> **证据等级**：【事实】附 `file:line`；【推断】附推理链与置信度；【缺口】说明原因与获取途径。

## 1. 范围与目的

| 项 | 内容 |
|---|---|
| subject（被描述的系统） | `<系统名>` |
| 边界 | `<单进程 HTTP 服务 / CLI 工具 / 库 等一句话描述>` |
| 本产出的目的 | `<为何而作——决定了要重建到哪个粒度>` |
| 目标读者 | `<谁会读它，读了要做什么决定>` |
| 产出档位 | `<速览 USE-CASES.md / 标准档全套>` |
| 本次未覆盖 | `<明确列出不在范围内的模块 / 目录 / 功能>` |

## 2. 取证路径及理由

由 `scripts/inventory_docs.sh` 给出建议起点，三档由证据强度决定，不由文档有无决定（判据见 `references/evidence-discipline.md` 三）：

| 取值 | 档 | 触发条件 | 目标层置信度上限 |
|---|---|---|---|
| `strong` | A 强证据 | 有需求/用例文档、BDD feature、e2e 测试或 API 契约 | `inferred_high` |
| `weak` | A− 弱证据 | 仅有 README / docs / CHANGELOG | `inferred_medium` |
| `none` | B 无文档 | 四类文档证据全无 | `inferred_low` / `gap` |

**本产出取值**：`evidence_path: <strong|weak|none>`

**理由**：<贴 `inventory_docs.sh` 的判定输出摘要，或写明命中了哪一 section（[1] 用户面文档 / [2] 需求与用例痕迹 / [3] 行为契约 / [4] 变更叙述）。>

**升档路径**（若当前为 weak 或 none）：<优先去找 e2e/BDD 测试与 API 契约；找到后目标层置信度改标 `inferred_high` 并补上新出处，见 `evidence-discipline.md` 3.2。>

**逐条置信度不等于仓库级档位**：仓库判为某档只是默认取证策略与预期基线，某个用例/actor 具体拿到的证据可能比仓库级判定更强或更弱，须逐条核实，见 `evidence-discipline.md` 三末段。

## 3. 最危险的发现

> 放在这里而不是埋进后面各节——读者只读前两屏也必须看到这些。每条给出证据与影响，并链接详情。

| # | 发现 | 类型 | 谁会因此做出错误判断 | 详情 |
|---|---|---|---|---|
| F1 | 【事实】<例：`DELETE /orders/{id}` 在订单已发货时仍返回 204，取消事件照常发出，但库存未回滚>（`path:line`） | <后置条件在失败路径下不成立> | <下游库存系统以为取消已生效，实际未处理> | [UC-99 §<n>](UC-99-gaps.md) |

逐类自检过一遍：宣称但不存在 ／ 存在但无人知晓 ／ 扩展流缺失 ／ 异常被吞 ／ 后置条件在失败路径下不成立 ／ actor 越权 ／ 输入校验缺口（七类详见 [UC-99](UC-99-gaps.md)）。

## 4. 一致性局限声明（一次性）

本产出对 UML 2.5.1 §18 与 ISO/IEC/IEEE 29148:2018 均不能声明"一致"，本声明只在此处出现一次，后续文件不再重复：

- **对 UML**：§18 是模型结构规范，不是文档一致性条款——UML 没有"conformance to §18"这种表述。§18.2.5.6 的四条 OCL 约束（`must_have_name` / `cannot_include_self` / `no_association_to_use_case` / `binary_associations`）可由 `scripts/check_usecase_model.py` 的 `check_uml` 逐条机械核查，但这只是**结构合规**，不等于"重建的用例模型忠实反映了系统"。
- **对 29148**：full conformance 做不到——§4.2 要求同时满足 §5.2、§6.1 引用的生命周期过程、§7 与 §9/Annex A 的信息项，而原始干系人、需求过程在逆向场景都不存在。tailored conformance（Annex C）也做不到——C.2.3 要求"Obtain input from all parties affected by the tailoring decisions"，逆向重建没有这些"各方"。
- **§5.2.6 Complete 冲突**：29148 §5.2.6 要求需求集合"不含 TBD/TBS/TBR"，而本 skill 的证据纪律要求把拿不到的内容显式标为【缺口】——两者结构性冲突，本产出选择满足缺口纪律，即对 §5.2.6 不满足，详见 [UC-99](UC-99-gaps.md) 末节。

本文档清单只当完备性检查表用，不对外宣称"符合 29148"或"符合 UML"，详见 `references/content-items.md` 第三节。

## 5. 规模与覆盖率声明

| 项 | 数值 |
|---|---|
| actor 数 | `<N>` |
| 用例数（user_goal / subfunction） | `<N>` / `<M>` |
| 已覆盖的 operational_modes | `<列表，对照 manifest 顶层 operational_modes>` |
| 已覆盖的 user_classes | `<列表，对照 manifest 顶层 user_classes；未覆盖的须在 UC-99 §1 说明>` |
| 场景总数（含四类变体） | `<N>` |
| 四类变体覆盖率 | normal `<N/N>`｜stress `<N/N>`｜exception `<N/N>`｜degraded `<N/N>`（缺失的记入 [UC-99](UC-99-gaps.md) §扩展流缺失） |
| 代码规模 vs 已覆盖规模 | `<总文件数/行数> vs <已分析文件数/行数，或用 inventory_entrypoints.sh 的入口点统计>` |

**未覆盖区域**：<列出未分析的模块/目录及原因，或链接 [UC-99 §1](UC-99-gaps.md)。>

## 6. 内容项索引

| 条款 | 内容项 | 位置 |
|---|---|---|
| UML §18.1.3.1 | subject / 用例语义 / 完整性判据 | 本文 §1；各 `UC-1x-*.md` §2 |
| UML §18.1.3.1 | Actor 语义 | 各 `UC-1x-*.md` §1；速览档对应 `USE-CASES.md` §3（标准档不产出该文件） |
| UML §18.1.3.2/.3 | Extend / Include | 各 `UC-1x-*.md` §1 |
| UML §18.2.5.6 | 四条 OCL 约束 | `scripts/check_usecase_model.py` 机械核查 |
| 29148 A.2.7 | 场景与四类变体 | 各 `UC-1x-*.md` §4 |
| 29148 §9.4.17 | 场景唯一命名与编号 | manifest `scenarios[].id`，机械核查 |
| 29148 §9.6.12 a)–e) | 功能细节 | 各 `UC-1x-*.md` §5 |
| — | 用例 ↔ 入口点 ↔ 代码追溯 | [UC-90](UC-90-traceability.md) |
| — | 缺口、尖锐发现、§5.2.6 冲突 | [UC-99](UC-99-gaps.md) |
