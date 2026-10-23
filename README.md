# TraceCase

[Open the live investigation workbench](https://tracecase-aml-workbench.streamlit.app/) | [First investigation guide](FIRST_SESSION.md)

An independent AML investigation workbench using entirely synthetic customer records, documents and transactions. Milestone 1.1 demonstrates an investigation flow: understand the customer, investigate unusual activity, challenge an assisted brief and document an evidence-backed decision.

Built as an AI-assisted learning project. The workbench is a portfolio demonstration, not a bank production deployment or a claim of professional AML experience. Its value is the investigation reasoning and work product, not a claim of automated crime detection.

## Review the project in five minutes

1. Read the [recruiter guide](docs/RECRUITER_GUIDE.md) for the AML skills and review criteria.
2. Open the live demo or run the app locally and select C001. Compare the customer profile, documents and calculated findings.
3. In AI assistance, load the clearly labelled author-written example or import a response to the exported case prompt. No API key is required for this flow.
4. Inspect the cited evidence, write your own decision and download the investigation report.
5. Compare C002: a similar transaction ratio has a different evidential context.

The first milestone intentionally has two contrasting cases. CDD and screening-match review are planned additions, not features claimed as implemented.

## Start on Windows

1. Install Python 3.11 or 3.12 from https://www.python.org/downloads/ if it is not already installed.
2. Extract the ZIP into a normal folder. Open the extracted `tracecase` folder.
3. Double-click `start_windows.bat`. The first run installs the pinned dependencies into a local virtual environment.
4. Your browser opens the Streamlit app, normally at http://localhost:8501.
5. Select the first investigation, review the evidence and open AI assistance.

The launcher requires internet access for the first dependency installation. Close the terminal to stop the application. By default, decisions are kept only in the current browser session; download reports before leaving. Different visitors do not share decision history. For a trusted single-user local installation only, set `TRACECASE_STORAGE=local` to retain SQLite history under `runtime/decisions.sqlite3`. Never enable that shared local mode on an anonymous public deployment.

Mac/Linux: run `bash start_mac_linux.sh` using Python 3.11 or 3.12.

## First exercise

Open `FIRST_SESSION.md`. Use the AI-assisted workflow immediately; you do not need to manually copy transactions or calculate totals. Your job is to verify the explanation and decide what should happen next.

## AI assistance

### Use your existing ChatGPT session

Download the selected case's prepared prompt from the app, paste it into ChatGPT and request JSON only. Paste the response into the app and click **Validate and load response**. This route does not require an API key. It is a deliberate export/import workflow, not an automatic ChatGPT integration.

The bundle also includes prompts under `exercises/` so you can start reviewing a case before installing the application.

### Optional live API

Live AI is disabled by default. On your own trusted installation, enable it with `TRACECASE_ENABLE_LIVE_AI=1`, enter your own OpenAI API key and a model identifier supported by your account in the application, select the consent checkbox and click **Generate live AI brief**. The chosen model must support Responses API structured outputs. Model access and billing depend on your API account; ChatGPT subscription access is separate. No request happens automatically. Server environment API keys are never copied into browser widgets. Do not commit credentials or paste them into case notes.

Only the included fictional packet is sent. `store=False` is used; this is not a guarantee of zero provider retention. No live provider request was made during verification because no API credential was configured. The provider adapter was tested with mocked complete/incomplete responses.

All AI factual claims require evidence identifiers. Unknown identifiers are rejected. This checks reference existence and response shape, not the truth or relevance of the claim. Inspect each cited record and acknowledge the factual claims before recording that you relied on AI. AI suggestions cannot save decisions or take account/regulatory actions.

## Included cases

- C001: salary-only profile, ten non-routine payers, closely following onward transfers and an unverified collection explanation.
- C002: non-routine property sale receipts and an onward mortgage redemption, with matching fictional verification records.

Both cases deliberately share a high income multiple and a 95% same-day/next-day debit-to-non-salary-credit ratio. Context and corroboration change the investigation. The ratio does not trace fungible funds or establish criminal conduct. Some documents are explicitly unverified; others include verification assertions solely within the fictional scenario.

No real identities, account numbers, government identifiers, live screening records or confidential banking data are included. All INR amounts are positive integers. Review-period computations exclude earlier history. The alert rule is an illustrative exercise assumption, not a statutory reporting threshold.

## What is implemented

- Two reproducible fixtures with customer, transaction and document identifiers.
- Review-period totals, income multiples, distinct payers and temporal movement calculations.
- Customer/document register, transaction filtering and CSV export.
- AI prompt export, JSON import validation and optional live API adapter.
- Analyst decision with evidence selection and four quality acknowledgments.
- Case-scoped session decision history with the complete evidence snapshot and SHA-256 fingerprint; optional SQLite storage for trusted local use.
- Downloadable Markdown investigation reports, JSON history and assistance outputs.
- A labelled author-written example for trying claim review without an API connection.
- Author-written coaching, revealed after a decision.

## Boundaries of milestone one

There is no live screening feed, no registry integration, no trained ML classifier, no money-laundering probability score, no independent AML expert validation, and no authenticated reviewer approval. History is append-only through the UI but can be changed by a person with filesystem access. No claim of tamper-proof auditing is made. The app is a training tool with session-separated history and an optional single-user local storage mode. Identical repeated saves create additional history records.

The coaching is author-written exercise guidance, not legal advice or an independently assessed answer key. An employer's policy and jurisdiction-specific rules would determine actual escalation/reporting processes. The application is not authenticated; session separation is not an enterprise access control or durable storage system.

## Hosting

GitHub hosts the source code; GitHub Pages cannot execute this Python application. To run a public demonstration, create an app in Streamlit Community Cloud using this repository, branch `main` and entry point `app.py`. Use Python 3.12, default session storage and disabled live AI. Do not publish runtime history or secrets. Session state is temporary, including on cloud hosting; visitors must export their own work. Add authentication and a durable external datastore before offering retained user accounts or production workflows. Public demonstrations should contain only the provided synthetic fixtures. The public demo was deployed and checked on 23 October 2026 at https://tracecase-aml-workbench.streamlit.app/. Live browser checks covered evidence display, calculated findings, example-brief review, an explicitly assistant-labelled QA decision, report download and case separation. QA records are not candidate-authored work.

## Verification

Run `python -m unittest discover -s tests -v` from the project directory after installing requirements. The suite covers calculation correctness, date boundaries, bad fixture rejection, fabricated evidence references, hidden coaching exclusion, optional API contract handling, decision validation, persistent case separation and Streamlit headless application interactions. These checks do not constitute a live API test, browser visual QA, security certification or production acceptance.

## File map

`app.py`: interface. `engine.py`: calculations and evidence checks. `ai_assistant.py`: prompt/schema/API adapter and labelled worked example. `storage.py`: session history or optional local SQLite history. `reporting.py`: readable investigation export. `data/cases.json`: fixtures. `data/coach.json`: learning guidance kept out of the AI packet. `data/build_cases.py`: fixture generation. `tests/`: verification.

## Workflow references

- Oracle Investigation Hub: https://docs.oracle.com/en/industries/financial-services/financial-crime-compliance/investigation-hub-cloud/
- LSEG screening concepts: https://developers.lseg.com/en/api-catalog/customer-and-third-party-screening/world-check-one-api/quick-start
- Google AML model evaluation concepts: https://docs.cloud.google.com/financial-services/anti-money-laundering/docs/evaluate-model
- OpenAI structured outputs: https://developers.openai.com/api/docs/guides/structured-outputs
- Streamlit application testing: https://docs.streamlit.io/develop/api-reference/app-testing
- Streamlit hosting: https://docs.streamlit.io/deploy/streamlit-community-cloud

These references informed the workflow. This project does not integrate with or replicate the licensed enterprise products, and is not endorsed by their vendors.

## Next milestone

Use the first two investigations to identify missing functionality. Then add screening-match review and customer due-diligence exercises, a documented quality rubric, an independently reviewed case set, and measured AI claim accuracy before considering ML prioritization. The application should follow AML needs rather than accumulate features to showcase programming tools.
