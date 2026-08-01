# <动词开头的用例名>（UC-XX）

> **manifest 对应条目**：`use_cases[id=UC-XX]`
> **level**：`user_goal` | `subfunction`（选择依据见 `references/granularity.md` 五）
> **actors**：`[<actor-id>, ...]`
> **依据版本**：`<短 sha>`（`file:line` 以此提交为准）
> 复制本文件为 `UC-XX-<slug>.md`，一个用例一份；`subfunction` 级用例可省略 §4 场景（见 `granularity.md` 五）。

## 1. 用例要素（UML §18）

| 字段 | 内容 |
|---|---|
| id | `UC-XX` |
| name | `<动词开头的用例名，如 Cancel Order 而非 Order Cancellation>` |
| level | `user_goal` \| `subfunction` |
| actors | `[<actor-id>, ...]`（§18.2.5.6 `binary_associations`：至少关联一个 actor） |
| goal_confidence | `<inferred_high\|inferred_medium\|inferred_low\|gap>`（恒为推断，不得为 `fact`；判据见 `references/evidence-discipline.md` 五） |
| 目标出处 | `<README.md:12 / docs/xxx.md#section / file:line，strong·weak 两档必填>` |
| entrypoints | `["<HTTP 路由 / CLI 子命令 / 导出符号>"]` |
| includes | `[<被包含用例 id>]`（§18.1.3.3；空列表须写「未发现」而非留空不提） |
| extends | `[<被扩展用例 id>]`（§18.1.3.2） |
| associations | `[]`（恒为空列表——§18.2.5.6 `no_association_to_use_case`；若代码显示两用例间存在依赖，应拆分/合并而非在此登记，见 `granularity.md` 四） |
| evidence | `["<file:line>", ...]` |

## 2. 完整性判定（UML §18.1.3.1）

**判定问题**：执行完毕后，subject 是否处于「无待续输入、可重新发起」的状态，或错误态？

**判定理由**：<按 `references/granularity.md` 一的流程走一遍——入口点是什么、追踪到哪个稳定点、为什么在那里状态已完整。`user_goal` 级用例本字段为必填，`check_uml` 会核查。>

`completeness_check`: "<填入与上方判定理由一致的简要陈述，供 manifest 使用>"

## 3. 前置条件 / 后置条件

**前置条件**（`preconditions`）：

- <执行本用例前 subject 须处于的状态；无则写「未发现前置条件」>

**后置条件**（`postconditions`）：

- <正常完成后 subject 的状态；若某条后置条件在失败路径下不成立，不要略过——记入本文件 §7 并链接 [UC-99](UC-99-gaps.md)>

## 4. 场景与四类变体（29148 A.2.7、§9.4.17）

> 四类变体每类各占一节。**缺失的变体不要删除本节**——写明「代码中无对应路径」并链接到 [UC-99](UC-99-gaps.md)（这是一条尖锐发现：扩展流缺失，见 `evidence-discipline.md` 四末段）。场景 id 须唯一命名与编号（§9.4.17）。

### 4.1 normal（正常操作）

- **id**：`SC-XX-normal`
- **steps**（含 events / actions / stimuli / information / interactions）：
  1. <step-by-step 描述>

### 4.2 stress（压力负载）

- **id**：`SC-XX-stress`
- **steps**：
  1. <step-by-step 描述，或：「代码中无对应路径——未见限流/背压/批量边界处理，见 [UC-99 §扩展流缺失](UC-99-gaps.md)」>

### 4.3 exception（异常处理）

- **id**：`SC-XX-exception`
- **steps**：
  1. <step-by-step 描述，或对应缺失说明>

### 4.4 degraded（降级模式）

- **id**：`SC-XX-degraded`
- **steps**：
  1. <step-by-step 描述，或对应缺失说明>

## 5. 功能细节（29148 §9.6.12 a–e）

> 五项逐条填写或显式写「未发现」，不要跳过未发现的项——跳过与「已核实无此机制」在读者眼里无法区分。

| 子项 | 内容 |
|---|---|
| a) 输入有效性校验（`input_validation`） | <校验了哪些字段、规则是什么，或「未发现」> |
| b) 精确的操作序列（`operation_sequence`） | <按顺序列出关键步骤> |
| c) 异常响应（`abnormal_responses`） | <溢出 / 通信故障 / 硬件故障 / 错误处理与恢复，逐项或写「未发现对应处理」> |
| d) 参数的作用（`parameter_effects`） | <各输入参数如何影响行为> |
| e) 输出与输入的关系（`io_relationship`） | <输入输出序列关系、转换公式，或引用点> |

## 6. 证据与出处

| 断言 | 标记 | 证据 |
|---|---|---|
| <用例存在（入口点已注册）> | 【事实】 | `<file:line>` |
| <用例目标 / actor 目标> | 【推断】 | `<推理链 + 置信度 + 出处>` |
| <未知项> | 【缺口】 | `<原因 + 可能获取途径>` |

## 7. 本用例的已知问题

<链接到 [UC-99](UC-99-gaps.md) 中与本用例相关的条目：宣称但不存在 / 存在但无人知晓 / 扩展流缺失 / 异常被吞 / 后置条件在失败路径下不成立 / actor 越权 / 输入校验缺口。无相关问题则写「本用例未发现七类尖锐发现，已逐类自检」。>
