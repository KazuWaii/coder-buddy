# Coder Buddy

A multi-agent coding assistant: describe an app in plain English, and a **Planner → Architect → Coder** pipeline built with [LangGraph](https://www.langchain.com/langgraph) generates it, file by file, ready to download and run.

This is Project 3 from the codebasics "5 AI Projects That Will Matter in 2026" challenge, inspired by the open-source [Coder Buddy](https://github.com/codebasics/coder-buddy) project. Standalone repo, independent from [ds-rpc-01](https://github.com/KazuWaii/ds-rpc-01) and [finsolve-voice-agent](https://github.com/KazuWaii/finsolve-voice-agent).

## Architecture

```
User request ("Build a calculator web app with +, -, *, / buttons")
  -> Planner   : turns the request into a ProjectPlan (name, description, file list)
  -> Architect : breaks the plan into a FileTask per file (a detailed engineering brief)
  -> Coder     : writes each file's code, in order (HTML first), feeding already-written
                 files into later prompts so e.g. script.js reuses index.html's real
                 element IDs instead of inventing its own
  -> output_dir/ on disk, zipped for download in the Streamlit UI
```

No vector database and no RAG here -- unlike the other two projects, this one is pure LLM planning and generation, no retrieval step.

| File | Role |
|---|---|
| `streamlit_app.py` | UI: request box, Generate button, per-file code viewer, .zip download |
| `app/agent.py` | LangGraph `StateGraph` wiring the three agents together, `run_agent()` entry point |
| `app/planner.py` | Request -> `ProjectPlan` (project name, description, file list) |
| `app/architect.py` | `ProjectPlan` -> `ArchitectPlan` (a detailed task per file) |
| `app/coder.py` | `FileTask` -> actual file contents, written to disk |
| `app/schemas.py` | Pydantic models (`ProjectPlan`, `FileTask`, `ArchitectPlan`) the LLM's JSON output is validated against |
| `app/llm.py` | Pluggable LLM backend: Ollama (local dev) or Groq (cloud); `chat_json()` wraps `chat()` with Groq's strict JSON mode + retries |

### A real bug this project surfaced

Early testing generated a calculator where clicking buttons did nothing. Each file (`index.html`, `style.css`, `script.js`) was generated independently and each invented its own naming convention -- `id="btn7"` in the HTML, `document.querySelectorAll("button[data-value]")` in the JS, `.button-row` + `data-type="digit"` in the CSS. None of them matched. Fixed by having `coder.py` pass already-generated files into later prompts (`previous_files`), so later files reuse real IDs instead of guessing -- and by generating structural files (HTML) before the files that reference them.

### LLM reliability notes

`openai/gpt-oss-20b` (Groq) is a reasoning model: its hidden chain-of-thought shares the same output-token budget as the visible answer, which occasionally left no room for the actual JSON. Fixed with `reasoning_effort="low"` plus Groq's `response_format={"type": "json_object"}` strict JSON mode, plus a small retry loop (`chat_json()`, up to 3 attempts) -- even with both fixes, a single malformed response still happens occasionally.

## Local setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
```

Pick an LLM backend via `LLM_PROVIDER` (defaults to `ollama`):

- **Ollama**: install [Ollama](https://ollama.com/download), `ollama pull llama3.2`.
- **Groq**: get a key at [console.groq.com](https://console.groq.com/), put it in a `.env` file:
  ```
  GROQ_API_KEY=your_key_here
  LLM_PROVIDER=groq
  ```

Run the app:

```bash
uv run streamlit run streamlit_app.py
```

Or drive the pipeline directly, without the UI:

```python
from app.agent import run_agent

result = run_agent("Build a calculator web app with add, subtract, multiply and divide buttons.", "output/calculator")
print(result["files_written"])
```
