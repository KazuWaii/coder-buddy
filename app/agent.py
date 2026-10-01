from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, END

from app.planner import create_plan
from app.architect import create_file_tasks
from app.coder import generate_file_code, write_file


class AgentState(TypedDict):
    request: str
    output_dir: str
    plan: object
    architect_plan: object
    files_written: list[str]


def plan_node(state):
    plan = create_plan(state["request"])
    return {"plan": plan}


def architect_node(state):
    architect_plan = create_file_tasks(state["plan"])
    return {"architect_plan": architect_plan}


def _sort_key(task):
    return 0 if Path(task.path).suffix in (".html", ".htm") else 1


def coder_node(state):
    generated = {}
    files_written = []
    tasks = sorted(state["architect_plan"].tasks, key=_sort_key)
    for task in tasks:
        code = generate_file_code(task, state["plan"], previous_files=generated)
        write_file(state["output_dir"], task, code)
        generated[task.path] = code
        files_written.append(task.path)
    return {"files_written": files_written}


graph = StateGraph(AgentState)
graph.add_node("plan", plan_node)
graph.add_node("architect", architect_node)
graph.add_node("code", coder_node)

graph.set_entry_point("plan")
graph.add_edge("plan", "architect")
graph.add_edge("architect", "code")
graph.add_edge("code", END)

compiled_agent = graph.compile()


def run_agent(request, output_dir):
    result = compiled_agent.invoke({
        "request": request,
        "output_dir": str(output_dir),
        "plan": None,
        "architect_plan": None,
        "files_written": [],
    })
    return result