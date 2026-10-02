"""Command-line entry point.

  python cli.py consult  data/sample_responses.csv
  python cli.py ask      "How will HIQA measure whether its plan is working?"
  python cli.py starter  data/sample_intake.json
  python cli.py tender   data/sample_tender.txt data/sample_draft.txt

Results are printed and also saved to the output/ folder as Markdown.
"""
import argparse
import json
from pathlib import Path

from dotenv import load_dotenv

from toolkit import assistant, consultation, starter, tender
from toolkit.llm import get_llm
from toolkit.retrieval import Library

DEFAULT_QUESTION = "What should a national health and social care regulator prioritise over the next three years?"
OUT = Path("output")


def save(name: str, text: str) -> None:
    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(text, encoding="utf-8")
    print(f"\nSaved to {OUT / name}")


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="Strategy AI Toolkit")
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("consult", help="Find themes in consultation responses (CSV with a 'response' column)")
    c.add_argument("csv")
    c.add_argument("--question", default=DEFAULT_QUESTION)
    a = sub.add_parser("ask", help="Ask the document library a question")
    a.add_argument("question")
    a.add_argument("--library", default="data/library")
    s = sub.add_parser("starter", help="Draft an outcome strategy outline from an intake JSON file")
    s.add_argument("intake")
    t = sub.add_parser("tender", help="Check a draft tender response against the tender's criteria")
    t.add_argument("tender_file")
    t.add_argument("draft_file")
    args = parser.parse_args()

    llm = get_llm()
    if args.command == "consult":
        result = consultation.analyse(consultation.load_responses(args.csv), llm, args.question)
        md = consultation.to_markdown(result, args.question)
        print(md)
        save("consultation_analysis.md", md)
    elif args.command == "ask":
        lib = Library()
        print(f"Library: {lib.add_folder(args.library)} passages from {args.library}\n")
        result = assistant.answer(args.question, lib, llm)
        print(result["answer"], "\n\nSources:")
        for p in result["passages"]:
            print(f"  [{p.id}] {p.source}, {p.where}")
        if result["invalid_citations"]:
            print("\nWARNING: cited passages that were not retrieved:", ", ".join(result["invalid_citations"]))
    elif args.command == "starter":
        md = starter.to_markdown(starter.draft(json.loads(Path(args.intake).read_text()), llm))
        print(md)
        save("strategy_outline.md", md)
    elif args.command == "tender":
        md = tender.to_markdown(tender.check(Path(args.tender_file).read_text(), Path(args.draft_file).read_text(), llm))
        print(md)
        save("tender_fit_check.md", md)


if __name__ == "__main__":
    main()
