import json

import pytest

from toolkit import starter

INTAKE = json.load(open("data/sample_intake.json"))
REPLY = json.dumps({
    "summary": "s",
    "outcomes": [{"outcome": f"o{i}", "why": "w", "actions": ["a"], "indicators": [{"indicator": "i", "source": "s", "frequency": "f"}]} for i in range(5)],
    "first_90_days": ["step"], "consultant_review": ["check"], "assumptions": ["assume"],
})


def test_caps_outcomes_at_three(fake_llm):
    assert len(starter.draft(INTAKE, fake_llm(REPLY))["outcomes"]) == 3


def test_prompt_includes_intake(fake_llm):
    llm = fake_llm(REPLY)
    starter.draft(INTAKE, llm)
    assert "family carers" in llm.prompts[0]


def test_missing_required_fields_rejected(fake_llm):
    with pytest.raises(ValueError):
        starter.draft({"purpose": ""}, fake_llm(REPLY))


def test_markdown_has_indicator_table(fake_llm):
    md = starter.to_markdown(starter.draft(INTAKE, fake_llm(REPLY)))
    assert "| How we'll know it's working |" in md and "first draft" in md.lower()
