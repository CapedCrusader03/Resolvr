# 🧾 Resolvr — Stateful Financial Auditor

Resolvr is a production-grade, agentic financial auditing application designed to ingest, parse, and reconcile complex, unstructured, and messy financial documents (invoices, CSV spreadsheets, multi-page bank statements, and blurry receipts). 

Built as a complete full-stack RAG (Retrieval-Augmented Generation) system, Resolvr utilizes a **three-tier memory architecture** and an autonomous **ReAct reasoning loop** powered by **Gemini 3.5 Flash** to identify mathematical anomalies, flag duplicate transactions, and resolve OCR/parsing discrepancies automatically.

[![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tech Stack](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20LangGraph-orange.svg)](#tech-stack)
[![Accuracy Score](https://img.shields.io/badge/chaos--dataset--eval-100%25-brightgreen.svg)](eval/eval_report.md)

---

## 🚀 Live Demo & Visuals

* **Unified Audit Chat Panel**: A chat interface where users query the auditor in plain English (e.g. *"What is my Q3 burn rate?"* or *"Sum all software subscriptions"*).
* **Clickable Source Citations**: Every computed total or retrieved transaction includes clickable references pointing directly to the source file name, page number, and parsing confidence score.
* **Agentic Debugger Panel**: A real-time timeline visualizing the agent's internal ReAct loop:
  `Classifier (Intent) ➔ Retriever (SQL + Vector) ➔ Calculator (Decimal Math) ➔ Anomaly Detector ➔ Solver (ReAct Loop) ➔ Reporter (Cited Response)`

---

## 🏗️ System Architecture

The following Mermaid diagram represents the complete data ingestion and agent execution pipeline of Resolvr:

```mermaid
graph TB
    subgraph "Frontend — React + Vite (Vercel)"
        UI_CHAT["Chat Panel<br/>(SSE streaming)"]
        UI_UPLOAD["File Uploader<br/>(drag & drop)"]
        UI_DEBUG["Agent Debugger Panel<br/>(ReAct thought log)"]
        UI_DOCS["Document List<br/>+ Citations"]
    end

    subgraph "Backend — FastAPI (Render)"
        API_INGEST["POST /api/ingest<br/>(multipart upload)"]
        API_CHAT["POST /api/chat<br/>(SSE stream)"]
        API_DOCS["GET /api/documents"]
        API_SESS["GET/POST /api/sessions"]
        RATE["Rate Limiter<br/>(protect Gemini quota)"]
    end

    subgraph "Ingestion Pipeline"
        PR["Parser Router<br/>(MIME inspection)"]
        TP["Text Parser"]
        PP["PDF Parser<br/>(PyPDF2)"]
        VP["Vision Parser<br/>(Gemini Vision)"]
        EP["Excel Parser<br/>(pandas)"]
        NM["Normalizer<br/>(→ ExtractedTransaction)"]
    end

    subgraph "Three-Tier Memory"
        SQ["Structured Store<br/>SQLite + SQLAlchemy"]
        VS["Semantic Store<br/>ChromaDB + Nomic Embed v2"]
        SS["Session Store<br/>LangGraph SqliteSaver"]
    end

    subgraph "Agentic Brain — LangGraph"
        N1["Node 1: Classifier<br/>SUM / FILTER / RECONCILE / ANOMALY"]
        N2["Node 2: Retriever<br/>SQL + Vector hybrid + dedup"]
        N3["Node 3: Calculator<br/>Decimal arithmetic"]
        N4["Node 4: Anomaly Detector<br/>Math check + duplicate detection"]
        N5["Node 5: Solver<br/>ReAct Loop (max 3 iters)"]
        N6["Node 6: Reporter<br/>Source-cited answer"]
    end

    UI_UPLOAD -->|"multipart"| API_INGEST
    UI_CHAT -->|"query + session_id"| API_CHAT
    API_INGEST --> RATE --> PR
    API_CHAT --> RATE --> N1

    PR --> TP & PP & VP & EP --> NM
    NM -->|"upsert"| SQ & VS

    N1 --> N2
    N2 -->|"SQL"| SQ
    N2 -->|"semantic search"| VS
    N2 --> N3
    N3 --> N4
    N4 -->|"anomaly"| N5
    N4 -->|"clean"| N6
    N5 -->|"re-parse"| VP
    N5 --> N6
    N6 -->|"SSE chunks"| API_CHAT -->|"stream"| UI_CHAT

    N1 & N2 & N3 & N4 & N5 & N6 -.->|"thought events"| UI_DEBUG
    SS -.->|"persist state"| N1
```

---

## 💾 Core Technologies & Decisions

### 1. Three-Tier Memory Model
* **Structured Store (SQLite + SQLAlchemy)**: Saves normalized transactions, merchants, and dates. This allows the LLM to run precise, algebraic filter queries (e.g. `SELECT * FROM transactions WHERE date >= '2025-01-01'`) instead of relying on unreliable vector lookups for numbers.
* **Semantic Store (ChromaDB + Nomic Embed Text v2)**: Stores document chunks for semantic search. This handles fuzzy, conceptual queries (e.g. *"Find where we discussed hiring a woodworker"*).
* **Session Store (LangGraph SqliteSaver)**: Maintains persistent conversation states, enabling full multi-turn auditing context.

### 2. Autonomous Anomaly Resolution (ReAct Loop)
When documents contain mismatched values (e.g., invoice line items do not sum to the stated total, or scanning OCR yields characters like `1O5.OO` instead of `105.00`), the **Anomaly Detector** flags them. The **ReAct Solver** then initiates a targeted crop-and-reparse tool, feeding the document region back into Gemini Vision, updating the records programmatically upon resolution.

### 3. Floating-Point Safety (Decimal Arithmetic)
Standard floating-point calculations in JavaScript or Python introduce rounding errors (e.g. `0.1 + 0.2 = 0.30000000000000004`). Resolvr processes all financial values using Python's `Decimal` type to guarantee exact monetary totals.

---

## 📊 Chaos Evaluation Suite

To prove Resolvr's reliability on real-world chaotic files, we built a **Chaos Dataset** containing 15 highly adversarial scenarios:

* OCR character corruptions (letter `O` in total amounts)
* String-formatted numeric cells (e.g., ` $1,200.00 ` with trailing spaces)
* Multi-page bank statements
* Overlapping duplicate transactions (same merchant, same value, 2 mins apart)
* Freeform markdown diary notes
* Spreadsheet cells merged across rows
* Multi-currency transactions
* Headerless CSV logs
* Refund values (represented as negative numbers)

Running the evaluation suite runs the entire parser router, database loader, and agentic reasoning loops end-to-end.

**Current Evaluation Accuracy**: `100.0%` (15/15 Scenarios Passed)
Read the full report at [eval/eval_report.md](eval/eval_report.md).

---

## 🛠️ Quick Start (Local Run)

### Prerequisites
* Python 3.11+ (Python 3.13 recommended)
* Node.js v18+ and `pnpm`
* Google Gemini API Key (obtain for free at [Google AI Studio](https://aistudio.google.com/))

### 1. Backend Setup
```bash
cd backend
# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Create .env file and add your Gemini API Key
echo GOOGLE_API_KEY=your_gemini_api_key_here > .env

# Start uvicorn server
uvicorn api.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd ../frontend
# Install packages
pnpm install

# Start Vite development server
pnpm dev
```
Open `http://localhost:5173` to interact with the Resolvr Web Interface.

### 3. Running Evaluation Harness
```bash
cd ../backend
# Activates the sandbox SQLite and Chroma DBs and evaluates scenarios
.venv\Scripts\python ../eval/run_eval.py
```

### 4. Running Backend Unit Tests
```bash
cd ../backend
# Runs existing test suite
.venv\Scripts\pytest -v
```

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
