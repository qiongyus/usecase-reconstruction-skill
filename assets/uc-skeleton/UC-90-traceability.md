# 用例 ↔ 入口点 ↔ 代码追溯矩阵

> **本节应由 `uc-manifest.yaml` 生成，而非手工维护。** 手工誊抄的矩阵在 manifest 改动后必然与正文脱节——改了 `use_cases[].entrypoints` 或 `evidence`，忘了同步这张表，矩阵就开始撒谎，且没有任何机制会提醒你。矩阵的每一行都能从 manifest 的 `use_cases[]`（`id` / `entrypoints` / `evidence` / `includes` / `extends`）机械派生，正确做法是写一个从 manifest 读取并渲染 Markdown 表格的小脚本（十几行，不引入新依赖），把下表当作该脚本的输出，而不是当作手写起点。

## 1. 追溯矩阵

| 用例 id | 用例名 | actor | 入口点 | 证据（file:line） | includes | extends |
|---|---|---|---|---|---|---|
| UC-01 | `<用例名>` | `<actor-id>` | `<HTTP 路由 / CLI 子命令 / 导出符号>` | `<file:line>` | `[<uc-id>, ...]` | `[<uc-id>, ...]` |

<本表由 manifest 派生；若暂时手工填写，须在文件头注明「本次为手工快照，生成脚本尚未落地」，避免读者误以为已自动化。>

## 2. 生成方式（占位）

```bash
# 从 uc-manifest.yaml 生成本矩阵的命令占位——本 skill 当前未提供该脚本，
# scripts/check_usecase_model.py 只做机械约束校验，不产出 Markdown。
# 使用者可自行实现，例如：
python3 <生成脚本路径> assets/uc-skeleton/uc-manifest.yaml > UC-90-traceability.md
```

`scripts/check_usecase_model.py` 目前的职责边界只到校验（退出码 + 违规清单），不生成人类可读文档；若需要自动生成本矩阵，应新增一个独立脚本读取 manifest 并渲染，而不是扩展校验脚本的职责。

## 3. 覆盖检查

对照 manifest 顶层 `operational_modes` × `user_classes`（29148 A.2.7 覆盖要求：所有操作模式 × 所有用户类别）：

| 用户类别 \ 操作模式 | `<mode-1>` | `<mode-2>` |
|---|---|---|
| `<actor-id>` | `<已覆盖的场景 id 列表，或「未覆盖」>` | `<...>` |

未覆盖的组合记入 [UC-99 §1 未覆盖区域](UC-99-gaps.md)，不要在本表中静默留空而不解释。

## 4. 已知不一致

<若发现矩阵与正文（各 `UC-1x-*.md`）存在出入——例如某用例的 entrypoints 在代码里已变化但 manifest 未同步——逐条记录，或写「本次未发现不一致」。>

| # | 不一致 | 涉及用例 | 为何未解决 |
|---|---|---|---|
| I1 | `<例：UC-03 的 entrypoints 列了 /v1/orders，代码里已迁移到 /v2/orders>` | `<UC-03>` | `<待下次同步 manifest>` |
