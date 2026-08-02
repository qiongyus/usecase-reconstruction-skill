# usecase-reconstruction

从只有源代码（可能含文档）的既有系统**重建用例模型与场景规格**，按 UML 2.5.1 §18 的用例模型结构与 ISO/IEC/IEEE 29148:2018 Annex A.2.7 / §9.6.12 的场景与功能细节组织产出。

这是一个中文个人 skill。给 agent 读的正文在 `SKILL.md`；本 README 面向浏览仓库的人，介绍定位、内容与安装方式。

## 定位

代码里没有「用例」，只有**入口点与执行路径**。用例的定义性要素是「对 Actor 有价值的可观察结果」（UML 2.5.1 §18.1.3.1），而**价值与目标都不在代码里**——只能从证据推断，永远不能从代码里读出来。本 skill 全部纪律的出发点，是让每条目标性断言的认知地位可见：

- **粒度判据可判定**：把 UML §18.1.3.1 唯一可判定的一句（执行后是否处于「无待续输入、可被重新发起」或错误态）转成候选用例的准入测试，取代「提醒模型注意粒度」
- **先事实后假说**：Step 3 机械列出全部对外入口（只产出可 `file:line` 指认的东西），Step 4 才用判据聚合成用例——顺序是结构性的，颠倒就是粒度失控的直接原因
- **三级证据纪律**：【事实】/【推断】/【缺口】；**用例名与 actor 目标恒为推断**，`fact` 不是合法置信度，脚本直接拦截
- **三档取证路径**：档位由证据强度而非文档有无决定（A 强证据 / A− 弱证据 / B 无文档），无文档项目主证据换成公开 API 契约 + 测试用例，目标层封顶 `inferred_low`
- **七类尖锐发现**：宣称但不存在 / 存在但无人知晓 / 扩展流缺失 / 异常被吞 / 后置条件在失败路径不成立 / actor 越权 / 输入校验缺口，逐类扫，每条写明「谁会因此做出错误判断」
- **机械校验**：`check_usecase_model.py` 核查 UML 四条 OCL 约束、粒度纪律、证据纪律与 29148 场景变体覆盖，违规退出码非零，可接入 CI

**产出取向是分析材料，不是合规文档。** 内容项完备只是及格线，价值在尖锐发现。

与相邻方法的分工：

| 要做的事 | 用什么 |
|---|---|
| 重建架构描述（AD，结构 / 白盒） | `architecture-reconstruction` |
| 重建结构化需求、做对等重写的 parity 分析 | `requirements-reconstruction` |
| 为尚不存在的系统做正向需求分析 | 需求工程，不是本 skill |
| **重建用例模型与场景规格（行为契约 / 黑盒）** | **本 skill** |

三个重建型 skill 相互独立，只共享证据层，不共享代码。

## 依据地基

三层锚定，全部一手：

| 层 | 依据 |
|---|---|
| 用例模型（subject / actor / include / extend） | UML 2.5.1 §18，含 §18.2.5.6 的四条 OCL 约束 |
| 场景步骤与四类变体（normal/stress/exception/degraded） | 29148:2018 Annex A.2.7（产出为 shall，内部组织为 should）、§9.4.17 |
| 功能细节（校验 / 序列 / 异常 / 参数 / IO） | 29148:2018 §9.6.12 a)–e) |
| 产出质量自检 | 29148:2018 §5.2.5 / §5.2.6（均 shall） |

用例文本模板（Cockburn 2001）降为**可选排版约定**——UML §18.1.3.2 明确用例文本格式 intentionally unspecified，29148 全文仅 4 处提及 use case 且均作为手段之一，真正的规范性内容在 **scenario** 与 **function** 名下。

一致性声明按诚实形态处理：对 UML 不声明 conformance，对 29148 连裁剪一致性（Annex C）都做不到（C.2.3 要求各方输入，逆向重建没有这些「各方」）；§5.2.6 Complete 要求不含 TBD，与缺口纪律直接冲突，选择满足缺口纪律并在文档头一次性声明。

## 工作流一览

| Step | 内容 |
|---|---|
| 0 | 定目的（接手维护 / 补文档 / 测试覆盖 / 重写迁移 / 安全审计），决定该恢复的层次与发现的优先级 |
| 1 | 文档清点与取证路径确认（`scripts/inventory_docs.sh`）——**交互确认点**，须请用户补充仓库外材料 |
| 2 | 按 A / A− / B 三档取证，定目标层置信度上限 |
| 3 | 系统操作清单（`scripts/inventory_entrypoints.sh`）：只列可 `file:line` 指认的对外入口，不做用例判断 |
| 4 | 用完整性判据聚合成用例（假说层），定 actor 与 include/extend |
| 5 | 场景与四类变体（29148 A.2.7），覆盖 operational_modes × user_classes |
| 6 | 功能细节逐条盘问（§9.6.12 五项） |
| 7 | 偏离、缺口与七类契约违背 |
| 8 | 机械校验（`scripts/check_usecase_model.py`）+ 14 项自检清单 |

产出按规模分三档：速览（单文件 `USE-CASES.md` + manifest）／标准（`UC-00` + 每用例一份 + 追溯 + 缺口）／完整（标准档 + 追溯矩阵 + CI）。内容项不减，只改承载。源文件数 ≥ 1500 时脚本主动打印规模警戒：必须分模块推进并声明覆盖率。

## 内容

```
SKILL.md                                  正文：本质、失败模式、证据纪律、工作流、自检
references/
  content-items.md                        UML §18 与 29148 各条款的逐条要求、shall/should 区分、完整自检清单
  granularity.md                          完整性判据的判定流程、双向粒度失控识别、正反例各 5 组
  evidence-discipline.md                  三级标记、三档取证路径取舍、证据源清单与陷阱、置信度判据表
  tooling.md                              按语言的入口点/导出符号提取工具、动态分析为何不在默认流程内
scripts/
  inventory_docs.sh                       Step 1 文档清点与三档取证路径判定
  inventory_entrypoints.sh                Step 3 入口点提取（HTTP/CLI/消息/定时/RPC/导出符号）与规模分级
  check_usecase_model.py                  Step 8 机械校验：UML OCL 约束组 + 29148 场景与功能约束组
  test_check_usecase_model.py             25 项 pytest，锁定上述判定逻辑
assets/uc-skeleton/
  uc-manifest.yaml                        机器可读字段契约，check_usecase_model.py 的校验对象
  USE-CASES.md                            速览档单页产出
  UC-00-overview.md                       标准档：范围、取证路径理由、最危险发现、覆盖率声明
  UC-1x-usecase-TEMPLATE.md               标准档：单用例模板
  UC-90-traceability.md                   标准档：用例↔入口点↔代码追溯矩阵
  UC-99-gaps.md                           标准档：缺口与七类尖锐发现
```

## 安装

```bash
rsync -a --exclude .git <本仓库>/ ~/.agents/skills/usecase-reconstruction/
ln -s ../../.agents/skills/usecase-reconstruction ~/.claude/skills/usecase-reconstruction
```

依赖：`python3`（校验脚本，仅用标准库）、`bash` + `grep`/`find`（清点脚本）。`pytest` 只在跑测试时需要。

## 验证状态

**v0.1.0 尚未做端到端评测**——不同于 `architecture-reconstruction`（2 轮评测）与 `requirements-reconstruction`（真实项目走通 Step 0–8），本 skill 目前只有构建期验证：

- 25 项 pytest 全绿，覆盖 UML 四条 OCL 约束与 29148 约束组的判定逻辑
- `inventory_docs.sh` 的三档判定在四个真实仓库上实测过（VictoriaTraces 4/4→A、o2-benchmark 1/4→A−、`lib/mergeset` 0/4→B、o2 2629 文件→规模警戒）
- skill-creator `quick_validate` 通过

评测资产（4 个用例 + 评分脚本）已就绪，未运行。

**已知限制**：

- `evidence_path` 与 `goal_confidence` 之间**故意不设一致性校验**——现在就机械封顶会掩盖首轮评测最有说服力的观察：置信度分布是否随证据强度单调变化
- 「目标是否编造」「实现细节泄漏」「粒度判据的内容质量」三项只有文字纪律，无机械强制，靠 Step 8 之后的人工自检与验证环节兜底；SKILL.md 对此有显式交代
- 入口点脚本的 `head -3` 抽样按遍历顺序先到先得，是展示样本而非判定依据
- `references/` 中对 `standards/01-requirements/norms.md` 的 `REQ-N*` 引用，在该文件不存在的项目上无对应免责说明（SKILL.md 正文有「不存在则静默跳过」的保护）
