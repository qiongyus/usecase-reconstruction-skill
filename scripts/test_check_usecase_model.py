import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from check_usecase_model import Report, check_uml, load_manifest


def base():
    """一份最小的合规 manifest。"""
    return {
        "subject": {"name": "S", "boundary": "b", "evidence": "m.go:1"},
        "evidence_path": "doc",
        "actors": [{"id": "a1", "name": "A1", "kind": "human",
                    "goal": "g", "confidence": "inferred_high",
                    "evidence": ["m.go:2"]}],
        "use_cases": [{"id": "UC-01", "name": "Ingest Data",
                       "level": "user_goal", "actors": ["a1"],
                       "completeness_check": "返回后可再次发起",
                       "goal_confidence": "inferred_high",
                       "evidence": ["m.go:3"], "includes": [], "extends": []}],
        "operational_modes": ["normal"],
        "user_classes": ["a1"],
    }


def run(data):
    rep = Report()
    check_uml(data, rep)
    return rep


def test_clean_manifest_has_no_errors():
    assert run(base()).errors == []


def test_must_have_name():
    d = base()
    d["use_cases"][0]["name"] = ""
    assert any("must_have_name" in e for e in run(d).errors)


def test_cannot_include_self_direct():
    d = base()
    d["use_cases"][0]["includes"] = ["UC-01"]
    assert any("cannot_include_self" in e for e in run(d).errors)


def test_cannot_include_self_indirect():
    d = base()
    d["use_cases"][0]["includes"] = ["UC-02"]
    d["use_cases"].append({"id": "UC-02", "name": "Sub Step",
                           "level": "subfunction", "actors": ["a1"],
                           "goal_confidence": "inferred_low",
                           "evidence": ["m.go:4"], "includes": ["UC-01"],
                           "extends": []})
    assert any("cannot_include_self" in e for e in run(d).errors)


def test_no_association_to_use_case():
    """UML §18.2.5.6：同一 subject 的用例之间不得有关联。"""
    d = base()
    d["use_cases"][0]["associations"] = ["UC-02"]
    d["use_cases"].append({"id": "UC-02", "name": "Query Data",
                           "level": "user_goal", "actors": ["a1"],
                           "completeness_check": "同上",
                           "goal_confidence": "inferred_high",
                           "evidence": ["m.go:5"], "includes": [], "extends": []})
    assert any("no_association_to_use_case" in e for e in run(d).errors)


def test_goal_confidence_must_not_be_fact():
    """核心纪律：用例目标恒为推断。"""
    d = base()
    d["use_cases"][0]["goal_confidence"] = "fact"
    assert any("goal_confidence" in e and "fact" in e for e in run(d).errors)


def test_actor_confidence_must_not_be_fact():
    d = base()
    d["actors"][0]["confidence"] = "fact"
    assert any("confidence" in e and "fact" in e for e in run(d).errors)


def test_user_goal_requires_completeness_check():
    """粒度判据：user_goal 级用例必须写出完整性判定理由。"""
    d = base()
    del d["use_cases"][0]["completeness_check"]
    assert any("completeness_check" in e for e in run(d).errors)


def test_unknown_actor_reference():
    d = base()
    d["use_cases"][0]["actors"] = ["ghost"]
    assert any("ghost" in e for e in run(d).errors)


def test_use_case_without_actor():
    d = base()
    d["use_cases"][0]["actors"] = []
    assert any("UC-01" in e and "actor" in e for e in run(d).errors)


def test_verb_first_naming_warns():
    """REQ-N03：用例名应动词开头。启发式只看首词后缀，故给警告而非错误。"""
    d = base()
    d["use_cases"][0]["name"] = "Ingestion Of Data"
    assert any("动词" in w for w in run(d).warnings)


def test_verb_first_naming_accepts_verb():
    d = base()
    d["use_cases"][0]["name"] = "Ingest Data"
    assert not any("动词" in w for w in run(d).warnings)


def test_load_manifest_json_top_level_list_exits_cleanly(tmp_path):
    """畸形 .json（顶层非映射）须干净地 sys.exit，而不是抛未捕获的 AttributeError。"""
    p = tmp_path / "uc-manifest.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        load_manifest(p)
    assert "顶层应是映射" in str(exc.value)


def test_load_manifest_yaml_top_level_list_exits_cleanly(tmp_path):
    """与 .json 分支平行的 .yaml 用例，确认两种格式行为一致。"""
    p = tmp_path / "uc-manifest.yaml"
    p.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        load_manifest(p)
    assert "顶层应是映射" in str(exc.value)


from check_usecase_model import check_29148


def run29148(data):
    rep = Report()
    model = check_uml(data, rep)
    rep2 = Report()
    check_29148(data, model, rep2)
    return rep2


def with_scenarios(variants, **extra):
    d = base()
    d["use_cases"][0]["scenarios"] = [
        {"id": f"SC-01-{v}", "variant": v, "steps": ["s"]} for v in variants
    ]
    d["use_cases"][0].update(extra)
    return d


def test_missing_normal_variant_is_error():
    """29148 A.2.7：每个用例至少要有正常路径场景。"""
    r = run29148(with_scenarios(["exception"]))
    assert any("normal" in e for e in r.errors)


def test_missing_exception_variant_warns():
    r = run29148(with_scenarios(["normal"]))
    assert any("exception" in w for w in r.warnings)


def test_all_four_variants_clean():
    r = run29148(with_scenarios(["normal", "stress", "exception", "degraded"],
                                function_details={
                                    "input_validation": "x", "operation_sequence": "x",
                                    "abnormal_responses": "x", "parameter_effects": "x",
                                    "io_relationship": "x"}))
    assert r.errors == []


def test_duplicate_scenario_id():
    """29148 §9.4.17：场景须唯一命名与编号。"""
    d = base()
    d["use_cases"][0]["scenarios"] = [
        {"id": "SC-dup", "variant": "normal", "steps": ["s"]},
        {"id": "SC-dup", "variant": "exception", "steps": ["s"]},
    ]
    assert any("SC-dup" in e for e in run29148(d).errors)


def test_invalid_variant_name():
    d = with_scenarios(["normal", "weird"])
    assert any("weird" in e for e in run29148(d).errors)


def test_missing_function_details_warns():
    """29148 §9.6.12 a)-e) 五项。"""
    r = run29148(with_scenarios(["normal", "exception"]))
    assert any("function_details" in w or "9.6.12" in w for w in r.warnings)


def test_partial_function_details_names_missing_keys():
    d = with_scenarios(["normal", "exception"],
                       function_details={"input_validation": "x"})
    r = run29148(d)
    assert any("operation_sequence" in w for w in r.warnings)


def test_user_class_not_covered_by_any_use_case():
    """A.2.7：所有用户类别都应被场景覆盖。"""
    d = with_scenarios(["normal", "exception"])
    d["user_classes"] = ["a1", "orphan"]
    assert any("orphan" in w for w in run29148(d).warnings)


def test_scenario_without_steps():
    d = base()
    d["use_cases"][0]["scenarios"] = [{"id": "SC-1", "variant": "normal", "steps": []}]
    assert any("SC-1" in e and "steps" in e for e in run29148(d).errors)


def test_subfunction_not_required_to_have_scenarios():
    """只有 user_goal 级用例强制要求场景。"""
    d = base()
    d["use_cases"][0]["level"] = "subfunction"
    del d["use_cases"][0]["completeness_check"]
    d["use_cases"][0]["scenarios"] = []
    assert run29148(d).errors == []


def test_function_details_non_mapping_is_error_not_crash():
    """function_details 若非映射（如手工写成字符串），须报 error 而非抛异常。"""
    d = with_scenarios(["normal", "exception"],
                       function_details="TBD -- 尚未填写为映射")
    r = run29148(d)
    assert any("应是映射" in e for e in r.errors)
