#!/usr/bin/env python3
"""核对用例模型的机械约束，分 UML 组与 29148 组。

用法:
    python3 check_usecase_model.py <uc-dir-or-manifest>

读取 <uc-dir>/uc-manifest.yaml（或 .json），核对下列可机械判定的约束：

UML 2.5.1 §18 组（规范性 OCL 约束，§18.2.5.6）：
  1. must_have_name              —— 用例必须有名字
  2. cannot_include_self         —— include 不得直接或间接成环
  3. no_association_to_use_case  —— 同一 subject 的用例之间不得有关联
  4. binary_associations         —— 用例只参与二元关联（须关联至少一个 actor）
  5. 粒度纪律                     —— user_goal 级用例必须写出完整性判定理由（§18.1.3.1）
  6. 证据纪律                     —— 用例目标与 actor 目标不得标为 fact

29148:2018 组（见 check_29148 组，Task 3 实现）。

违规时退出码非零，可直接用于 CI。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 用例目标与 actor 目标恒为推断，fact 不在合法取值内
VALID_CONFIDENCE = {"inferred_high", "inferred_medium", "inferred_low", "gap"}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def note(self, msg: str) -> None:
        self.notes.append(msg)

    def emit(self) -> int:
        for m in self.notes:
            print(f"  \033[36m·\033[0m {m}")
        for m in self.warnings:
            print(f"  \033[33m⚠\033[0m {m}")
        for m in self.errors:
            print(f"  \033[31m✗\033[0m {m}")
        print()
        if self.errors:
            print(f"\033[31m不合规：{len(self.errors)} 项违规，"
                  f"{len(self.warnings)} 项警告\033[0m")
            return 1
        if self.warnings:
            print(f"\033[33m基本合规：0 项违规，{len(self.warnings)} 项警告\033[0m")
            return 0
        print("\033[32m✓ 合规：全部约束通过\033[0m")
        return 0


def load_manifest(target: Path) -> dict:
    if target.is_dir():
        candidates = [target / "uc-manifest.yaml", target / "uc-manifest.yml",
                      target / "uc-manifest.json"]
        found = [c for c in candidates if c.exists()]
        if not found:
            sys.exit(f"在 {target} 下未找到 uc-manifest.yaml / .json\n"
                     f"可从 assets/uc-skeleton/uc-manifest.yaml 复制一份作为起点。")
        path = found[0]
    else:
        path = target
        if not path.exists():
            sys.exit(f"文件不存在: {path}")

    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        data = json.loads(text)
        if not isinstance(data, dict):
            sys.exit(f"{path} 顶层应是映射（mapping），实际是 {type(data).__name__}")
        return data
    try:
        import yaml
    except ImportError:
        sys.exit("读取 YAML 需要 pyyaml（pip install pyyaml），"
                 "或把 manifest 改写为 uc-manifest.json。")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        sys.exit(f"{path} 顶层应是映射（mapping），实际是 {type(data).__name__}")
    return data


def ids(items: list, kind: str, rep: Report) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for i, item in enumerate(items or []):
        if not isinstance(item, dict):
            rep.error(f"{kind}[{i}] 应是映射，实际是 {type(item).__name__}")
            continue
        _id = item.get("id")
        if not _id:
            rep.error(f"{kind}[{i}] 缺少 id 字段")
            continue
        if _id in out:
            rep.error(f"{kind} id 重复: {_id}")
        out[_id] = item
    return out


def _reaches(start: str, graph: dict[str, list[str]]) -> set[str]:
    """从 start 出发经 include 边可达的全部用例（不含 start 自身除非成环）。"""
    seen: set[str] = set()
    stack = list(graph.get(start, []))
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        stack.extend(graph.get(n, []))
    return seen


def check_uml(data: dict, rep: Report) -> dict:
    actors = ids(data.get("actors"), "actors", rep)
    use_cases = ids(data.get("use_cases"), "use_cases", rep)

    if not use_cases:
        rep.error("未声明任何 use case —— 用例模型为空")
    rep.note(f"规模：{len(actors)} actor / {len(use_cases)} 用例 "
             f"（user_goal {sum(1 for u in use_cases.values() if u.get('level') == 'user_goal')} / "
             f"subfunction {sum(1 for u in use_cases.values() if u.get('level') == 'subfunction')}）")

    include_graph = {u: (item.get("includes") or []) for u, item in use_cases.items()}

    for uc_id, uc in use_cases.items():
        # 约束 1：must_have_name（UML §18.2.5.6）
        if not (uc.get("name") or "").strip():
            rep.error(f"用例 '{uc_id}' 缺少 name —— 违反 UML must_have_name")
        else:
            # REQ-N03：用例名应动词开头。词性无法可靠判定，这里只用名词后缀做
            # 启发式——只能抓住 "Ingestion Of Data" 这类首词即名词的情况，
            # 抓不住 "Data Ingestion"（首词 Data 不带名词后缀）。故只给警告。
            first = uc["name"].strip().split()[0].lower()
            if first.endswith(("tion", "sion", "ment", "ance", "ence", "ity", "ness")):
                rep.warn(f"用例 '{uc_id}' 名称 '{uc['name']}' 疑似名词开头 —— "
                         f"用例名应动词开头（如 Ingest Data 而非 Ingestion Of Data）")

        # 约束 2：cannot_include_self
        for inc in include_graph[uc_id]:
            if inc not in use_cases:
                rep.error(f"用例 '{uc_id}' include 了未声明的用例 '{inc}'")
        if uc_id in _reaches(uc_id, include_graph):
            rep.error(f"用例 '{uc_id}' 直接或间接 include 了自身 —— "
                      f"违反 UML cannot_include_self")

        # 约束 3：no_association_to_use_case
        for assoc in uc.get("associations") or []:
            if assoc in use_cases:
                rep.error(f"用例 '{uc_id}' 与同一 subject 的用例 '{assoc}' 建立了关联 —— "
                          f"违反 UML no_association_to_use_case（每个用例各自描述对 "
                          f"subject 的一次完整使用）")

        # 约束 4：binary_associations —— 用例须关联 actor
        uc_actors = uc.get("actors") or []
        if not uc_actors:
            rep.error(f"用例 '{uc_id}' 未关联任何 actor")
        for a in uc_actors:
            if a not in actors:
                rep.error(f"用例 '{uc_id}' 关联了未声明的 actor '{a}'")

        # 约束 5：粒度纪律（UML §18.1.3.1 完整性判据）
        if uc.get("level") == "user_goal" and not (uc.get("completeness_check") or "").strip():
            rep.error(f"用例 '{uc_id}' 是 user_goal 级但缺少 completeness_check —— "
                      f"须写出「执行后 subject 是否可重新发起」的判定理由")

        # 约束 6：证据纪律
        gc = uc.get("goal_confidence")
        if gc == "fact":
            rep.error(f"用例 '{uc_id}' 的 goal_confidence 为 fact —— "
                      f"用例目标恒为推断，代码里只有入口点与执行路径")
        elif gc and gc not in VALID_CONFIDENCE:
            rep.error(f"用例 '{uc_id}' 的 goal_confidence '{gc}' 非法"
                      f"（取值：{'/'.join(sorted(VALID_CONFIDENCE))}）")
        elif not gc:
            rep.warn(f"用例 '{uc_id}' 未标注 goal_confidence")

        # 事实断言须有 file:line
        for ev in uc.get("evidence") or []:
            if not re.search(r"[^\s:]+:\d+", str(ev)):
                rep.warn(f"用例 '{uc_id}' 的证据 '{ev}' 不是 file:line 形式")

    for a_id, a in actors.items():
        conf = a.get("confidence")
        if conf == "fact":
            rep.error(f"actor '{a_id}' 的 confidence 为 fact —— "
                      f"UML §18.1.3.1：actor 是 role 而非实体，"
                      f"代码里只有物理接口，角色映射恒为推断")
        elif conf and conf not in VALID_CONFIDENCE:
            rep.error(f"actor '{a_id}' 的 confidence '{conf}' 非法")
        elif not conf:
            rep.warn(f"actor '{a_id}' 未标注 confidence")

    return {"actors": actors, "use_cases": use_cases}


# 29148:2018 Annex A.2.7 规定的四类场景变体
VARIANTS = ("normal", "stress", "exception", "degraded")

# 29148:2018 §9.6.12 a)–e)
FUNCTION_DETAIL_KEYS = {
    "input_validation": "a) 输入有效性校验",
    "operation_sequence": "b) 精确的操作序列",
    "abnormal_responses": "c) 异常响应",
    "parameter_effects": "d) 参数的作用",
    "io_relationship": "e) 输出与输入的关系",
}


def check_29148(data: dict, model: dict, rep: Report) -> None:
    use_cases = model["use_cases"]
    seen_scenario_ids: dict[str, str] = {}
    covered_classes: set[str] = set()

    for uc_id, uc in use_cases.items():
        scenarios = uc.get("scenarios") or []

        for sc in scenarios:
            if not isinstance(sc, dict):
                rep.error(f"用例 '{uc_id}' 的场景应是映射，实际是 {type(sc).__name__}")
                continue
            sc_id = sc.get("id")
            if not sc_id:
                rep.error(f"用例 '{uc_id}' 有场景缺少 id —— "
                          f"29148 §9.4.17 要求场景唯一命名与编号")
                continue
            if sc_id in seen_scenario_ids:
                rep.error(f"场景 id 重复: '{sc_id}'（已用于用例 "
                          f"'{seen_scenario_ids[sc_id]}'）—— 违反 29148 §9.4.17")
            else:
                seen_scenario_ids[sc_id] = uc_id
            variant = sc.get("variant")
            if variant not in VARIANTS:
                rep.error(f"场景 '{sc_id}' 的 variant '{variant}' 非法 —— "
                          f"29148 A.2.7 规定四类：{' / '.join(VARIANTS)}")
            if not (sc.get("steps") or []):
                rep.error(f"场景 '{sc_id}' 缺少 steps —— A.2.7 要求 "
                          f"step-by-step 描述，含 events/actions/stimuli/"
                          f"information/interactions")

        # 仅 user_goal 级强制要求场景
        if uc.get("level") != "user_goal":
            continue

        covered_classes.update(uc.get("actors") or [])
        present = {sc.get("variant") for sc in scenarios if isinstance(sc, dict)}

        if "normal" not in present:
            rep.error(f"用例 '{uc_id}' 缺少 normal 变体 —— "
                      f"29148 A.2.7 要求描述正常运行场景")
        for v in ("exception", "stress", "degraded"):
            if v not in present:
                rep.warn(f"用例 '{uc_id}' 缺少 {v} 变体 —— A.2.7 要求考察四类变体；"
                         f"若代码中确无对应路径，这是一条尖锐发现（扩展流缺失），"
                         f"应记入缺口章节而非静默略过")

        fd = uc.get("function_details") or {}
        if not isinstance(fd, dict):
            rep.error(f"用例 '{uc_id}' 的 function_details 应是映射，实际是 {type(fd).__name__}")
            fd = {}
        if not fd:
            rep.warn(f"用例 '{uc_id}' 缺少 function_details —— "
                     f"29148 §9.6.12 a)–e) 五项应逐条填写或显式写「未发现」")
        else:
            for k, desc in FUNCTION_DETAIL_KEYS.items():
                if not (fd.get(k) or "").strip():
                    rep.warn(f"用例 '{uc_id}' 的 function_details 缺 {k}（{desc}）")

    # A.2.7：所有用户类别都应被覆盖
    for cls in data.get("user_classes") or []:
        if cls not in covered_classes:
            rep.warn(f"用户类别 '{cls}' 未被任何 user_goal 用例覆盖 —— "
                     f"A.2.7 要求场景覆盖所有用户类别")

    modes = data.get("operational_modes") or []
    if not modes:
        rep.warn("未声明 operational_modes —— A.2.7 要求覆盖所有操作模式")
    else:
        rep.note(f"操作模式 {len(modes)} 种 × 用户类别 "
                 f"{len(data.get('user_classes') or [])} 类，"
                 f"共 {len(seen_scenario_ids)} 个场景")


def main() -> int:
    ap = argparse.ArgumentParser(description="核对用例模型的机械约束")
    ap.add_argument("target", type=Path, help="用例产出目录或 manifest 文件路径")
    args = ap.parse_args()

    data = load_manifest(args.target)
    rep = Report()
    print(f"核对用例模型: {args.target}\n")
    print("\033[1m[UML 2.5.1 §18 约束]\033[0m")
    model = check_uml(data, rep)
    print("\033[1m[ISO/IEC/IEEE 29148:2018 场景与功能约束]\033[0m")
    check_29148(data, model, rep)
    return rep.emit()


if __name__ == "__main__":
    sys.exit(main())
