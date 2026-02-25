# 🏠 Greater Noida Real Estate AI Agent (MCP-SSE)

An agentic AI assistant for the **Greater Noida** rental market, powered by:

- **[Agno](https://github.com/agno-agi/agno)** — Agent framework with memory
- **Azure OpenAI (GPT-4)** — LLM backend
- **MCP (Model Context Protocol)** — Tool server over SSE
- **Azure Maps API** — Nearby amenity search
- **SQLite + NoBroker data** — Local property database
- **Gradio** — Chat interface

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Gradio Chat UI (app.py)         │
│              http://localhost:7860           │
└──────────────────┬──────────────────────────┘
                   │  arun()
┌──────────────────▼──────────────────────────┐
│            Agno Agent (agent.py)             │
│  • Azure OpenAI (GPT-4)                      │
│  • SQLTools  ──► nobroker.db (SQLite)        │
│  • MCPTools  ──► SSE connection              │
└──────────────────┬──────────────────────────┘
                   │  SSE  http://localhost:8000/sse
┌──────────────────▼──────────────────────────┐
│         MCP Server (mcp_server.py)           │
│  • find_nearby_amenity (Azure Maps API)      │
│  • evaluate_deal      (SQLite median data)   │
└─────────────────────────────────────────────┘
```

---

## Features

| Goal | Trigger Keywords | Tool Used |
|------|-----------------|-----------|
| **Find Housing** | rent, flat, BHK, budget | `SQLTools` → `nobroker.db` |
| **Evaluate a Deal** | overpriced, good deal, fair price | `evaluate_deal` (MCP) |
| **Find Amenities** | school, hospital, mall, metro | `find_nearby_amenity` (MCP + Azure Maps) |

---

## Project Structure

```
Realestate AI_Agent MCP-SSE/
├── main/
│   ├── MCP_Tools/
│   │   └── mcp_server.py     # FastMCP server exposing tools over SSE
│   ├── agent.py              # Agno agent definition
│   ├── app.py                # Gradio chat UI entry point
│   ├── config.py             # Env-var loading & validation
│   ├── database.py           # CSV → SQLite builder
│   └── nobroker.db           # SQLite property database (git-ignored)
├── .env.example              # Template for required secrets
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd "Realestate AI_Agent MCP-SSE"
```

### 2. Create & activate a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env   # or copy on Windows
```

```env
AZURE_OPENAI_API_KEY=<your-azure-openai-key>
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini          # your deployment name
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_MAPS_KEY=<your-azure-maps-key>
DB_PATH=main/nobroker.db                     # optional, defaults to this
```

---

## Running the App

You need **two terminals** running simultaneously.

### Terminal 1 — Start the MCP Server

```bash
cd main/MCP_Tools
python mcp_server.py
# Server starts at http://localhost:8000/sse
```

### Terminal 2 — Start the Gradio UI

```bash
cd main
python app.py
# UI opens at http://localhost:7860
```

---

## Example Queries

```
"Show me 2 BHK flats under ₹15,000 in Chi"
"Is ₹18,000 for 900 sqft in Sector 1 a good deal?"
"Find hospitals near Gaur City 2"
"Are there malls near Godrej Crest?"
```

---

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_API_KEY` | ✅ | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | ✅ | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT` | ✅ | Deployment name (e.g. `gpt-4o-mini`) |
| `AZURE_OPENAI_API_VERSION` | ✅ | API version string |
| `AZURE_MAPS_KEY` | ✅ | Azure Maps subscription key |
| `DB_PATH` | ❌ | Path to SQLite DB (default: `main/nobroker.db`) |
| `CSV_PATH` | ❌ | Path to raw CSV (only needed to rebuild DB) |

---

## License

MIT
