# Local Conversation Processing and Compression — Sem-EL Task 1

A beginner-friendly, local Python prototype that prepares conversations for downstream LLM tasks. It does **not** call an LLM, send data to an API, or claim to fact-check statements.

## Included features

1. Input cleanup (whitespace, line endings, invisible characters).
2. Statement splitting.
3. Exact duplicate removal while preserving first occurrence and order.
4. Rule-based topic grouping (plans, tasks, corrections, people, reference facts, other).
5. Important-context extraction using transparent rules (dates, numbers, deadlines, constraints, and keywords).
6. Heuristic correction-candidate detection with an explicit `pending_review` status and earlier/newer statement ledger.
7. Duplicate correction display prevention: correction statements are shown in the correction ledger rather than repeated in the topic summary.
8. Chunking with a configurable word limit.
9. Evaluation metrics: word counts, word reduction, estimated token counts/reduction, duplicates, topics, chunks, important statements, corrections, and processing time.
10. JSON-compatible output for integration with teammates' modules, plus JSON and text downloads.
11. Unit tests for core processing behaviour.

## Setup on Windows / VS Code

Open the VS Code terminal and run these commands from the folder where you want the project:

```powershell
mkdir W:\el_project
cd W:\el_project
```

Copy all files from this project folder into `W:\el_project`, then run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m unittest -v
streamlit run app.py
```

If PowerShell blocks activation, you can skip activation and use the virtual environment directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m unittest -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit prints a local URL, usually `http://localhost:8501`. Open it in your browser.

## Main files

- `app.py`: Streamlit UI, metrics, correction review, chunk display, and downloads.
- `conversation_processor.py`: core processing pipeline and JSON result schema.
- `correction_detector.py`: correction detector interface used by the app.
- `test_processor.py`: automated tests.
- `sample_conversation.txt`: sample input.

## Output / teammate integration

The downloadable `conversation_processing_result.json` includes `schema_version`, `task`, `compressed_text`, `summary_text`, `topics`, `important_statements`, `correction_history`, `chunks`, and metrics. A downstream module can consume this JSON instead of parsing the UI output.

## Important limitations to mention in the evaluation

- Topic grouping and important-context extraction use keywords/rules, so they can misclassify sentences.
- Correction detection is heuristic. `pending_review` means a person must check whether the statements really conflict and which one should be used. This module does not establish truth.
- Duplicate removal is exact/normalized duplicate removal, not semantic deduplication.
- Token counts are estimates, not exact token counts for a particular model. Word counts and token counts are different.
- Chunking is based on word count. A production integration should use the downstream model's tokenizer and context-window limits.
- This is Task 1 only. Internal factual verification, external fact-checking, and document generation belong to separate pipeline stages/modules.
