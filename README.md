# Strategy AI Toolkit

AI-assisted **bid review, research and reporting** for outcomes-based strategy work: the kind of strategy projects carried out for public bodies, health and social care organisations, and charities.

**Try it live:** [Strategy AI Toolkit (hosted demo)](https://claude.ai/artifact/4qnuaZiebVm4hx2ZM33Gkh) · [Outcome Lens](https://claude.ai/artifact/77zqZACCNJVcuQ9wfU4gAr)

Built by [Deeksha Gulati](https://deekshagulati.netlify.app). Uses only public documents and illustrative sample data.

---

## What it does

| Tool | Stage of a strategy project | What AI does | What the code checks |
| --- | --- | --- | --- |
| **Tender Fit Checker** | Winning work | Lists a tender's mandatory requirements and weighted award criteria, then rates how well a draft response addresses each one (addressed well / mentioned briefly / missing) with evidence from the draft | Every evidence quote must appear word for word in the draft or the rating is not trusted; every weight must appear in the tender; weights must total 100%; gaps are ordered by marks at risk, mandatory gaps first |
| **Consultation Analyser** | Research | Groups free-text stakeholder responses into themes, counts them, picks an example quote | Every quote is matched word for word against the response it is attributed to; responses left out of every theme are listed; less common points are flagged for a person to read |
| **Document Assistant** | Research | Answers questions from a library of documents, citing a passage for each point | The model only sees the passages the search found, and any citation to a passage it was not given is flagged |
| **Strategy Starter** | Strategy | Turns a short intake form into a draft outcome strategy outline with indicators and a first 90 days | Outcomes capped at three; required fields enforced; the draft lists the points needing expert input |
| **Outcome Lens** ([demo](https://claude.ai/artifact/77zqZACCNJVcuQ9wfU4gAr)) | Reporting | Sorts a plan's actions into outputs and outcomes, suggests indicators, drafts progress updates | Statuses are illustrative and labelled as such |

**The principle throughout:** AI does the first draft, the consultant checks it, and every result can be traced back to its source.

## Why the design choices

- **No free public chatbots.** The Irish Government's *Guidelines for the Responsible Use of AI in the Public Service* (May 2025) advise against free generative AI tools because information entered could be used to train the model. This toolkit calls an AI model through a business API, and can be pointed at a private **Azure OpenAI deployment in an EU region** instead (see `toolkit/llm.py`).
- **Checks in code, not just in the prompt.** Asking a model "don't make up quotes" is not enough. The code tests each quote and citation and shows the result.
- **Simple, explainable search.** The Document Assistant uses keyword search (BM25) rather than a vector database. For a firm's few hundred reports this works well, costs nothing to run, and is easy to audit. It can be swapped for Azure AI Search later.

## Data in this repository

- `data/sample_responses.csv`: 22 **illustrative** consultation responses written for this demo. They are not real submissions.
- `data/library/hiqa_corporate_plan_notes.md`: plain-English notes summarising the public [HIQA Corporate Plan 2025–2027](https://www.hiqa.ie/sites/default/files/2025-05/HIQA-Corporate-Plan-25-27.pdf), passage by passage with page numbers.
- `data/sample_intake.json`: a **fictional** small charity used to demonstrate the Strategy Starter.
- `data/sample_tender.txt` and `data/sample_draft.txt`: a **fictional** request for tender and a deliberately incomplete draft response, used to demonstrate the Tender Fit Checker.
- `scripts/download_public_docs.py` downloads the full public PDFs (HIQA, Skillnet Ireland) to your own machine. They are not stored in the repository.

## Run it yourself

You need Python 3.10+ and an API key for Anthropic or Azure OpenAI.

```bash
git clone https://github.com/deekshaagulatii-gif/Strategy.aitoolkit.git
cd strategy-ai-toolkit
pip install -r requirements.txt
cp .env.example .env          # then add your API key to .env

# Command line
python cli.py consult data/sample_responses.csv
python cli.py ask "How will HIQA measure whether its plan is working?"
python cli.py starter data/sample_intake.json
python cli.py tender  data/sample_tender.txt data/sample_draft.txt

# Optional: add the full public PDFs to the document library
python scripts/download_public_docs.py

# Web app
streamlit run app.py
```

Results from the command line are also saved as Markdown in `output/`.

## Host the web app for free

1. Push this repository to GitHub.
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with GitHub and choose **New app**, pointing at `app.py`.
3. Under **Settings → Secrets**, add `ANTHROPIC_API_KEY = "..."` (and optionally `APP_PASSWORD = "..."`).

Every AI call uses the key owner's credits, so set a spending limit with your provider and consider the password.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests use a fake model, so they run free and offline. They check the safeguards: invented or misattributed quotes are flagged, tender ratings without real evidence from the draft are downgraded, invented weights are caught, citations to unretrieved passages are caught, out-of-range response IDs are dropped, and the model never sees passages the search did not return. GitHub Actions runs them on every push (`.github/workflows/tests.yml`).

## Taking it into a firm (private deployment)

| Step | What happens | Example tools |
| --- | --- | --- |
| Document library | Past reports stored securely, access limited to staff | SharePoint or Azure storage, EU region |
| Preparation | Documents labelled by client, sector and year; personal data removed where not needed | Python (this repo's `retrieval.py` as a start) |
| Search | Passages indexed for retrieval | BM25 here; Azure AI Search at scale |
| Model | Private enterprise deployment that does not train on your data | Azure OpenAI in an EU data zone (`LLM_PROVIDER=azure_openai`) |
| Saved tasks | Repeatable instructions for each job | The prompts in `toolkit/` |
| Controls | Logins, usage logs, regular quality checks, a Data Protection Impact Assessment before client data is used | Built around the above |

## Project structure

```
toolkit/llm.py            model wrapper (Anthropic or private Azure OpenAI)
toolkit/consultation.py   Consultation Analyser + quote verification
toolkit/retrieval.py      document library, chunking and BM25 search
toolkit/assistant.py      Document Assistant + citation checks
toolkit/starter.py        Strategy Starter
toolkit/tender.py         Tender Fit Checker
cli.py                    command line
app.py                    Streamlit web app
tests/                    pytest suite (fake model, no API key needed)
```

## Licence

MIT. See `LICENSE`.
