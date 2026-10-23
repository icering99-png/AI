"""Tactile verification tests for skills, STE-100 and subagent isolation."""
import json
from pathlib import Path
from core.ste_guard import SteGuard

def test_ste100_procedural_and_ambiguity_fallback() -> None:
    res_ok = SteGuard.check_step("Limit each procedural step to <= 20 words.")
    assert res_ok["ok"] is True
    assert res_ok["status"] == "PASS"

    res_ambig_dots = SteGuard.check_step("Process item and wait...")
    assert res_ambig_dots["ok"] is False
    assert res_ambig_dots["status"] == "REVIEW"

    res_ambig_paren = SteGuard.check_step("Verify token (unclosed bracket")
    assert res_ambig_paren["ok"] is False
    assert res_ambig_paren["status"] == "REVIEW"

def test_subagents_catalog_configuration_isolation() -> None:
    cat_path = Path(r"C:\Users\Данил\.gemini\config\skills\ai_cad_core_workflows\subagents.json")
    assert cat_path.exists()
    cat = json.loads(cat_path.read_text(encoding="utf-8"))
    
    critics = [s for s in cat["subagents"] if s["name"] in ("cad_critic", "rag_researcher")]
    for role in critics:
        assert role["enable_write_tools"] is False
        assert role["enable_mcp_tools"] is False
        assert role["enable_subagent_tools"] is False
        assert set(role["tools"]) == {"read", "search"}
        assert role["disable_model_invocation"] is True

def test_claim_0011_and_plugin_manifest_presence() -> None:
    claim_p = Path("KnowledgeBase/claims/CLAIM-0011.yaml")
    assert claim_p.exists()
    assert "applyTo" in claim_p.read_text(encoding="utf-8")

    plug_p = Path("TEMPLATE_PORTABLE/plugin.json")
    assert plug_p.exists()
    plug = json.loads(plug_p.read_text(encoding="utf-8"))
    assert plug["name"] == "antigravity-core-standard"
    assert len(plug["skills"]) == 3

def test_prompt_files_and_antipatterns_fail0008() -> None:
    prompt_p = Path("prompts/audit_step.prompt.md")
    assert prompt_p.exists()
    assert "#file:../plans/PLAN-LIVE.md" in prompt_p.read_text(encoding="utf-8")

    fail_p = Path("failure_index.json")
    data = json.loads(fail_p.read_text(encoding="utf-8"))
    f8 = next(f for f in data["failures"] if f["id"] == "FAIL-0008")
    assert f8["status"] == "RESOLVED"
    assert "excludeAgent" in f8["prohibition"]


