# Langchain-Data-Agent
Intelligent text-to-SQL agent for SQL Server: auto-discovers your schema, generates and executes T-SQL from natural language, and presents insights through an interactive Streamlit UI.

# SQL Data Agent

An AI agent that answers questions about a **Microsoft SQL Server** database in plain English. You ask something like *"Give me the top 5 products by sales"*, and the agent reads the database schema, writes a T-SQL query, runs it, and explains the result.

Built with **LangChain**, **OpenAI**, **SQLAlchemy / pyodbc** and **Streamlit**.

---

## Features

- Natural language to T-SQL (SQL Server syntax, e.g. `TOP` instead of `LIMIT`)
- Agent with two tools: it discovers the schema, then runs queries
- Read-only behavior: the agent is instructed to run only `SELECT` queries
- Streamlit chat UI with:
  - Chat history in the left panel (switch between conversations)
  - A **Show tool calls** toggle that displays each tool call with its arguments and result
  - Conversation memory, so follow-up questions work
- Three ways to run it: a simple prompt-to-SQL script, a terminal agent, and a web app

---

## Project structure

```
AI_Data_Agents/
├── streamlit_app.py     # Web UI (chat, history sidebar, tool-call toggle)
├── data_agent.py        # Terminal version of the agent
├── agent_tools.py       # LangChain @tool functions: execute_query, get_schema
├── main.py              # Simple version: LLM writes SQL, the script runs it
├── tools.py             # Plain (non-agent) helper functions used by main.py
├── requirements.txt     # Python dependencies
├── .env                 # Your API key (never commit this)
└── .gitignore
```

### What each file does

| File | Purpose |
|------|---------|
| `agent_tools.py` | Connects to SQL Server and defines two LangChain tools: `get_schema` (lists all tables, columns and data types in a schema) and `execute_query` (runs a SQL query and returns the result as text). |
| `data_agent.py` | Creates an agent with those tools and runs a question-and-answer loop in the terminal. Type `exit` to quit. |
| `streamlit_app.py` | The same agent behind a Streamlit chat interface, with saved chats and a tool-call viewer. |
| `tools.py` + `main.py` | A simpler, non-agent approach. `main.py` fetches the schema once, asks the model to write SQL, checks that it starts with `SELECT`/`WITH`, then runs it with `execute_query`. |

---

## How it works

```
User question
     │
     ▼
   Agent (LLM)
     ├── calls get_schema      → learns table and column names
     ├── writes a T-SQL query
     ├── calls execute_query   → runs it on SQL Server
     ▼
Plain-English answer
```

1. The user asks a question.
2. The agent calls `get_schema` to see which tables and columns exist.
3. It writes a T-SQL query and calls `execute_query`.
4. It reads the result and answers in natural language.

---

## Prerequisites

- **Python 3.12** (3.10+ should work)
- **SQL Server** (Express is fine) that you can connect to
- **Microsoft ODBC Driver 18 for SQL Server** (or 17, see Configuration)
- An **OpenAI API key**

---

## Setup

### 1. Create and activate a virtual environment (Windows PowerShell)

```powershell
python -m venv myvenv
.\myvenv\Scripts\Activate.ps1
```

If activation is blocked, run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

> Note: the `requirements.txt` in this project lists `psycopg[binary]` (for Postgres) but not `pyodbc`, which SQL Server needs. Add `pyodbc` to the file, and remove `psycopg[binary]` if you only use SQL Server. The final list should be:
>
> ```
> python-dotenv
> langchain
> langchain-openai
> pandas
> sqlalchemy
> streamlit
> pyodbc
> ```

### 3. Add your API key

Create a `.env` file in the project folder:

```
OPENAI_API_KEY=your_key_here
```

No quotes and no spaces around `=`.

### 4. Check the ODBC driver

```powershell
python -c "import pyodbc; print(pyodbc.drivers())"
```

The list should include `ODBC Driver 18 for SQL Server`. If it shows version 17 instead, change the `DRIVER=` line in `agent_tools.py` (and `tools.py`) to match.

---

## Configuration

The connection settings live at the top of `agent_tools.py` and `tools.py`:

```python
connection_string = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    r"SERVER=Jobs-PC\SQLEXPRESS;"     # your server\instance
    "DATABASE=MY_DATABASE;"           # your database
    "Trusted_Connection=yes;"         # Windows Authentication
    "TrustServerCertificate=yes;"
)
```

Change `SERVER` and `DATABASE` to match your setup.

**Using a SQL login instead of Windows authentication:** replace `Trusted_Connection=yes;` with `UID=your_user;PWD=your_password;`, and store the real credentials in `.env`, not in the code.

The model name (`gpt-6-luna`) is set in each script. Change it to any model your OpenAI account can use.

---

## Usage

### Web app (recommended)

```powershell
streamlit run streamlit_app.py
```

Then open the URL shown in the terminal (usually http://localhost:8501).

- Type a question in the chat box.
- Use **New chat** to start a fresh conversation, and click any past chat in the left panel to reopen it.
- Turn on **Show tool calls** to see every tool call the agent made, with its arguments and result. Turn it off to see only the final answer.

> Chat history is kept in Streamlit's session state, so it is cleared when you refresh the browser page.

### Terminal agent

```powershell
python data_agent.py
```

Type your question at the prompt; type `exit` to quit.

### Simple SQL generator (no agent)

```powershell
python main.py
```

The model returns only a SQL query, which the script then runs and prints.

---

## Example questions

- Give me the top 5 products by sales
- Which region has the highest profit?
- How many orders were shipped in each ship mode?
- Show total sales by category and sub-category

---

## Safety notes

- The agent is **instructed** to run only `SELECT` queries, but a prompt is not a security guarantee. For real use, connect with a **read-only database user** (for example, one with only the `db_datareader` role).
- `main.py` also blocks any generated SQL that doesn't start with `SELECT` or `WITH`.
- **Never commit `.env`.** It contains your API key. Add it to `.gitignore`.

Suggested `.gitignore`:

```
.env
myvenv/
__pycache__/
*.pyc
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python3.14` not recognized on Windows | Use `python` or `py -3.12`; `python3.x` commands don't exist on Windows. |
| `Data source name not found` | The `DRIVER=` name doesn't match an installed driver. Check `pyodbc.drivers()`. |
| `Login failed` | Run VS Code as the same Windows user that logs into SSMS, or switch to a SQL login. |
| SSL / certificate error | Keep `TrustServerCertificate=yes` in the connection string. |
| Blank Streamlit page | Start with `streamlit run streamlit_app.py` (not `python`), press Enter if the terminal asks for an email, and check the terminal for errors. |
| `LIMIT` syntax errors | SQL Server uses `TOP n`, not `LIMIT n`. |
| Agent loop never exits | Make sure you're running the latest saved file; `exit` must be compared as the string `'exit'`. |

---

## Tech stack

- [LangChain](https://www.langchain.com/): agent and tool framework
- [OpenAI](https://platform.openai.com/): language model
- [SQLAlchemy](https://www.sqlalchemy.org/) + [pyodbc](https://github.com/mkleehammer/pyodbc): SQL Server connection
- [pandas](https://pandas.pydata.org/): query results
- [Streamlit](https://streamlit.io/): web interface
