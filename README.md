# CSV Data Science Agent — LangGraph + FastAPI + MongoDB

Upload any CSV file, ask questions in plain English, and get back:
- A text answer
- The generated Python code
- A chart (as base64 PNG, ready to drop into an `<img>` tag)

## Quick Start

```bash
cp .env.example .env        # add your OPENAI_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload
# → http://localhost:8000/docs
```

## Docker (API + MongoDB)

```bash
# from the project root (csv_agent/)
docker compose -f docker/docker-compose.yml up --build
# → http://localhost:8000/docs
```

## How to Use (3 steps)

```
# 1 — Create a session
POST /sessions
{ "title": "Sales Analysis" }

# 2 — Upload your CSV
POST /sessions/{session_id}/upload
form-data: file=sales.csv

# 3 — Ask questions
POST /sessions/{session_id}/chat
{ "query": "Show me a bar chart of revenue by month" }
{ "query": "What is the average order value?" }
{ "query": "Which product category has the most sales?" }
```

## API Endpoints

| Method | Path | What it does |
|--------|------|-------------|
| POST | `/sessions` | Create a new session |
| POST | `/sessions/{id}/upload` | Upload a CSV file |
| POST | `/sessions/{id}/chat` | Ask a question → get answer + chart |
| GET  | `/sessions/{id}/history` | Full conversation history |
| GET  | `/sessions` | List all sessions |
| DELETE | `/sessions/{id}` | Delete session + messages + CSV |

## Chat Response Fields

```json
{
  "session_id": "...",
  "answer":  "The average order value is $142.50",
  "code":    "print(df['order_value'].mean())",
  "output":  "142.5",
  "chart":   "<base64 PNG string or null>",
  "message_id": "..."
}
```

Render chart in HTML: `<img src="data:image/png;base64,{chart}">`

## LangSmith (see the agent flow)

To see the full LangGraph run (node-by-node + LLM calls) in LangSmith:

1) Create a LangSmith API key.
2) Set these in your `.env` (see `.env.example`):

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=YOUR_LANGSMITH_KEY_HERE
LANGCHAIN_PROJECT=csv-agent
```

3) Restart the API and make a `/sessions/{id}/chat` request.
4) Open LangSmith → Projects → `csv-agent` to view the trace.

## Project Structure

```
csv_agent/
├── main.py
├── requirements.txt
├── .env.example
├── uploads/               ← CSV files saved here (one per session)
├── helpers/
│   ├── config.py          ← pydantic-settings reads .env
│   ├── db.py              ← Motor async MongoDB client
│   └── code_runner.py     ← safe Python sandbox (no os/subprocess)
├── agents/
│   ├── state.py           ← AgentState TypedDict
│   ├── graph.py           ← LangGraph wiring + conditional edge
│   └── nodes/
│       ├── inspect_csv.py     ← Node 1: shape, columns, sample rows
│       ├── analyze_data.py    ← Node 2: LLM plans the approach
│       ├── code_gen.py        ← Node 3: LLM writes pandas/chart code
│       ├── correct_code.py    ← Node 4: LLM fixes errors
│       └── execute_code.py    ← Node 5: runs code, captures chart PNG
├── schemas/
│   └── models.py
└── routers/
    ├── sessions.py
    └── chat.py
```

## Example Questions

- "What is the average salary by department?"
- "Plot a histogram of age distribution"
- "Show me the top 10 products by revenue"
- "Is there a correlation between price and sales volume?"
- "Show monthly trend of orders as a line chart"
