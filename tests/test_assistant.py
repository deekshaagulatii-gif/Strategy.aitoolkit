from toolkit import assistant
from toolkit.retrieval import Library


def make_library():
    lib = Library()
    lib.add_text("plan", "The outcome framework will be developed in year one to monitor progress.")
    lib.add_text("plan", "Staff wellbeing is supported through an engagement strategy.")
    return lib


def test_valid_citations_are_accepted(fake_llm):
    res = assistant.answer("How is progress monitored?", make_library(), fake_llm("An outcome framework is planned [P1]."))
    assert res["citations"] == ["P1"] and res["invalid_citations"] == []


def test_citation_to_unretrieved_passage_is_flagged(fake_llm):
    res = assistant.answer("How is progress monitored?", make_library(), fake_llm("Framework [P1]. Also something [P9]."))
    assert res["invalid_citations"] == ["P9"]


def test_model_only_sees_retrieved_passages(fake_llm):
    llm = fake_llm("ok [P1]")
    assistant.answer("outcome framework progress", make_library(), llm)
    assert "framework" in llm.prompts[0]


def test_no_match_skips_the_model(fake_llm):
    llm = fake_llm("should not be called")
    res = assistant.answer("quantum chromodynamics", make_library(), llm)
    assert res["passages"] == [] and llm.prompts == []
