"""Strategy Starter: turns a short intake form into a first-draft outcome strategy outline.

Designed for organisations that cannot fund a full engagement. The draft is reviewed by a consultant in one
workshop before it is handed over.
"""
from __future__ import annotations

from .llm import LLM, parse_json

FIELDS = {
    "organisation_type": "Organisation type",
    "planning_period": "Planning period",
    "purpose": "What it does",
    "challenges": "Challenges",
    "stakeholders": "Stakeholders",
    "desired_change": "Desired change",
    "existing_data": "Data already collected",
}

PROMPT = """You are drafting an outcome strategy OUTLINE for a small organisation that cannot afford a full consulting engagement.
A consultant will review it in one workshop before handover. Use an "outcomes, not outputs" approach: outcomes describe
change for people; actions are outputs that contribute to them.

{intake}

Rules: 3 outcomes maximum. Each outcome must describe a change for people, not an activity. 3 or 4 actions per outcome.
2 or 3 indicators per outcome that this organisation could realistically measure, preferring data it already has.
Do not invent statistics, budgets or facts about the organisation. Plain English, no jargon.

Return ONLY JSON:
{{"summary":"two sentences","outcomes":[{{"outcome":"","why":"","actions":[""],"indicators":[{{"indicator":"","source":"","frequency":""}}]}}],
 "first_90_days":[""],"consultant_review":[""],"assumptions":[""]}}"""


def draft(intake: dict, llm: LLM) -> dict:
    missing = [k for k in ("purpose", "desired_change") if not str(intake.get(k, "")).strip()]
    if missing:
        raise ValueError(f"Intake is missing: {', '.join(missing)}")
    lines = "\n".join(f"{label}: {intake.get(key, '')}" for key, label in FIELDS.items())
    result = parse_json(llm.complete(PROMPT.format(intake=lines), max_tokens=3000))
    result["outcomes"] = result.get("outcomes", [])[:3]
    return result


def to_markdown(result: dict) -> str:
    out = ["# Outcome strategy outline (first draft)", "", result.get("summary", ""), ""]
    for i, o in enumerate(result.get("outcomes", []), start=1):
        out += [f"## Outcome {i}: {o.get('outcome', '')}", o.get("why", ""), "", "**Actions**"]
        out += [f"- {a}" for a in o.get("actions", [])]
        out += ["", "| How we'll know it's working | Data source | How often |", "| --- | --- | --- |"]
        out += [f"| {x.get('indicator', '')} | {x.get('source', '')} | {x.get('frequency', '')} |" for x in o.get("indicators", [])]
        out.append("")
    for title, key in (("First 90 days", "first_90_days"), ("Needs expert input", "consultant_review"), ("Assumptions", "assumptions")):
        if result.get(key):
            out += [f"## {title}", ""] + [f"- {x}" for x in result[key]] + [""]
    out.append("_AI first draft for consultant review._")
    return "\n".join(out)
