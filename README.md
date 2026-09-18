# Support Ticket AI System

An AI-powered system for querying, analyzing, and detecting anomalies in customer support ticket data — built for the DOTMappers AI Engineer technical assessment.

## Features

- **Data ingestion**: loads and cleans `support_tickets.csv` into a queryable table
- **Natural language querying**: ask plain-English questions, answered via a local LLM that generates and safely executes pandas code
- **Anomaly detection**: flags stale high-priority tickets (rule-based) and statistically unusual resolution times (IQR method)
- **REST API** (FastAPI) — 3 endpoints: `/health`, `/query`, `/anomalies`
- **Web UI** (Streamlit) — the same functionality, visually

Both an API and a UI are included: the assessment brief's Section 2 states both are required, while Section 4's deliverables list phrases it as either/or. Both are provided to satisfy either reading.

## Setup

**Prerequisites:**
- Python 3.10, 3.11, or 3.12
- [Ollama](https://ollama.com/download) installed and running (see below)
- Windows/Mac/Linux, 8GB+ RAM recommended (16GB+ for smooth performance)

**1. Clone this repository and create a virtual environment:**
```bash
git clone https://github.com/Abin4464/AI_Assessment
cd AI_Assessment
python -m venv venv
# or: conda create -p venv python==3.11 -y

# Activate it:
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Install Ollama and pull the model (one-time setup):**
```bash
# Download Ollama from https://ollama.com/download and install it, then:
ollama pull llama3.1:8b
```
Ollama runs as a background service once installed — no need to start it manually.

**4. Place the dataset:**
Put `support_tickets.csv` in the `data/` folder.

**5. Run everything with a single command:**
```bash
python run.py
```
This starts both the API (http://127.0.0.1:8000/docs) and the UI (http://127.0.0.1:8501) together.

## Architecture

```
                    ┌─────────────────┐
                    │ support_tickets  │
                    │      .csv        │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  data_loader.py   │  (cleans, parses dates,
                    │                   │   handles nulls)
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │                             │
    ┌─────────▼─────────┐        ┌─────────▼──────────┐
    │   nlq_engine.py    │        │ anomaly_detector.py │
    │  (LLM generates &  │        │  (rule-based +      │
    │  safely executes   │        │   IQR statistical   │
    │  pandas code)       │        │   detection)         │
    └─────────┬─────────┘        └─────────┬──────────┘
              │                             │
              └──────────────┬──────────────┘
                             │
                ┌─────────────┴─────────────┐
                │                            │
        ┌───────▼────────┐         ┌────────▼───────┐
        │    main.py      │         │     app.py      │
        │  (FastAPI:      │         │  (Streamlit:    │
        │  REST endpoints)│         │  Web UI)        │
        └────────────────┘         └────────────────┘
```

**Key design decisions:**

- **Ollama over cloud APIs**: initially explored HuggingFace's free Inference Providers, but their free tier grants only $0.10/month in credits with no genuinely free models remaining on the router — incompatible with the "zero cost to evaluator" constraint. Ollama runs entirely locally: no cost, no internet dependency at runtime, no rate limits.
- **Text-to-pandas-code over fixed query templates**: the sample questions vary widely in structure, and the evaluator will run their own queries live. A fixed set of pre-built operations would inevitably miss some. Generating a single line of pandas code per question handles arbitrary questions naturally.
- **Sandboxed code execution**: since the LLM's output is executed, it runs in a restricted namespace with only `df`, `pandas`, and a small allow-list of safe built-ins (`len`, `sum`, `min`, etc.) — no file, network, or system access, and no `import`/`eval`/`exec`/`open` are reachable even if the LLM tried to generate them (blocked both by pattern-matching before execution and by the restricted namespace itself).
- **IQR method for statistical outliers**: a standard, explainable technique (the same one box plots use) rather than a black-box anomaly score — easier to justify and reason about in the walkthrough.
- **Single shared logic layer**: both `main.py` (API) and `app.py` (UI) call the exact same `data_loader`, `nlq_engine`, and `anomaly_detector` functions — no duplicated business logic between the two interfaces.

## Model & Tools Used

| Component        | Choice                          |
|-------------------|----------------------------------|
| LLM               | Llama 3.1 8B, via Ollama (local) |
| Data processing   | Pandas                          |
| REST API          | FastAPI + Uvicorn               |
| UI                | Streamlit                       |

## Example Queries & Outputs

**Q: "How many tickets are currently open?"**
```python
result = len(df[df['status'] == 'Open'])
```
→ **111**

**Q: "What is the average customer rating for Technical category tickets?"**
```python
result = df[df['category'] == 'Technical']['customer_rating'].mean()
```
→ **3.74**

**Q: "Show me all Critical tickets not resolved within 12 hours."**
```python
result = df[(df['priority'] == 'Critical') & (df['resolution_time_hrs'].isnull() | (df['resolution_time_hrs'] > 12))][['ticket_id','issue_summary']]
```
→ 34 matching tickets (see Known Limitations — this interpretation can vary between runs)

**Anomaly detection output:**
- 40 stale High/Critical tickets open longer than 24 hours
- 21 resolution-time outliers (IQR method, threshold: 48.1 hours)

## Known Limitations

- **LLM interpretation can vary for ambiguous phrasing.** For example, "not resolved within 12 hours" was interpreted differently across two runs of the same question — once including tickets that eventually resolved late, once only counting still-open tickets. `temperature=0` reduces but doesn't eliminate this variability. With more time, this would be addressed with a more constrained output format (e.g., forcing the LLM to pick from an explicit operation schema) or few-shot examples covering ambiguous phrasing patterns.
- **"This month" / relative time references** are ambiguous to the LLM without additional context, since the dataset is historical (Jan–Mar 2024) rather than live.
- **Anomaly "current time" reference**: the 24-hour staleness check uses the latest timestamp *in the dataset* as "now," rather than the real current date — appropriate for a static historical file, but would need to switch to `datetime.now()` for a live production data feed.
- **8B local model quality ceiling**: a locally-run 8B model is less capable at code generation than larger cloud models (GPT-4-class, 70B+ local models). Given more compute budget, a larger model would likely reduce the interpretation variability noted above.
- **Single-file CSV, not a database**: fine for 500 rows; would need to move to a proper database with indexing for a larger, production-scale ticket volume.

## What I'd Improve With More Time

- Add a lightweight caching layer for repeated identical questions
- Expand the safe-execution sandbox to support slightly more complex multi-step analyses
- Add automated tests (currently manually verified — see Testing section below)
- LLM-generated natural-language summaries of anomalies, not just raw tables

## Troubleshooting

**Ollama crashes with a CUDA / "stack-based buffer" error on startup:**
This is a GPU driver compatibility issue between Ollama's bundled CUDA version and your NVIDIA driver, not an issue with this codebase. Fix:
1. Update your NVIDIA driver from [nvidia.com/drivers](https://www.nvidia.com/drivers) and restart.
2. If it still crashes, force CPU-only mode instead: quit Ollama from the system tray (or End Task in Task Manager), then in a fresh terminal run:
   ```
   set OLLAMA_LLM_LIBRARY=cpu
   ollama serve
   ```
   Leave that terminal open, then run `python run.py` as usual in a separate terminal. Responses will be slower than GPU mode but fully functional.

**First `/query` request times out or fails right after starting:**
The model needs time to load into memory on its very first call after Ollama starts (up to ~60-90 seconds on CPU-only mode). Run `ollama run llama3.1:8b` once in a separate terminal and wait for a response before using the API/UI, or simply retry the query after a short wait.

## Testing

Manually tested:
- All 4 sample queries from Section 9 of the assessment brief
- Edge case: empty/ambiguous questions
- Both anomaly detection methods verified against manually-computed expected counts
- All 3 API endpoints via FastAPI's `/docs` interface
- Both UI tabs (question box, anomalies view)
