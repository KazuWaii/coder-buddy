from unittest.mock import patch

from app import agent
from app.schemas import ProjectPlan, FileTask, ArchitectPlan


def _sample_plan():
    return ProjectPlan(
        project_name="calc", description="A calculator.", files=["script.js", "index.html", "style.css"]
    )


def _sample_architect_plan():
    # Deliberately NOT html-first, to prove coder_node reorders it.
    return ArchitectPlan(tasks=[
        FileTask(path="script.js", description="The logic."),
        FileTask(path="index.html", description="The HTML."),
        FileTask(path="style.css", description="The styles."),
    ])


def test_plan_node_calls_create_plan_with_request():
    with patch("app.agent.create_plan", return_value=_sample_plan()) as mock_create_plan:
        result = agent.plan_node({"request": "Build a calculator."})

    mock_create_plan.assert_called_once_with("Build a calculator.")
    assert result["plan"].project_name == "calc"


def test_architect_node_calls_create_file_tasks_with_plan():
    plan = _sample_plan()
    with patch("app.agent.create_file_tasks", return_value=_sample_architect_plan()) as mock_create_tasks:
        result = agent.architect_node({"plan": plan})

    mock_create_tasks.assert_called_once_with(plan)
    assert result["architect_plan"].tasks[0].path == "script.js"


def test_coder_node_generates_html_before_other_files():
    state = {"plan": _sample_plan(), "architect_plan": _sample_architect_plan(), "output_dir": "/fake/output"}
    generated_order = []

    def fake_generate(task, plan, previous_files=None):
        generated_order.append(task.path)
        return f"content of {task.path}"

    with patch("app.agent.generate_file_code", side_effect=fake_generate), \
         patch("app.agent.write_file") as mock_write_file:
        result = agent.coder_node(state)

    # index.html must be generated first despite being 2nd in the architect's list
    assert generated_order[0] == "index.html"
    assert set(generated_order) == {"script.js", "index.html", "style.css"}
    assert mock_write_file.call_count == 3
    assert set(result["files_written"]) == {"script.js", "index.html", "style.css"}


def test_coder_node_passes_previously_generated_files_as_context():
    architect_plan = ArchitectPlan(tasks=[
        FileTask(path="index.html", description="The HTML."),
        FileTask(path="script.js", description="The logic."),
    ])
    state = {"plan": _sample_plan(), "architect_plan": architect_plan, "output_dir": "/fake/output"}
    seen_previous_files = []

    def fake_generate(task, plan, previous_files=None):
        seen_previous_files.append(dict(previous_files or {}))
        return f"content of {task.path}"

    with patch("app.agent.generate_file_code", side_effect=fake_generate), \
         patch("app.agent.write_file"):
        agent.coder_node(state)

    assert seen_previous_files[0] == {}  # first file (index.html) has no prior context
    assert seen_previous_files[1] == {"index.html": "content of index.html"}  # second file sees it


def test_run_agent_end_to_end_with_mocked_agents(tmp_path):
    with patch("app.agent.create_plan", return_value=_sample_plan()) as mock_plan, \
         patch("app.agent.create_file_tasks", return_value=_sample_architect_plan()) as mock_architect, \
         patch("app.agent.generate_file_code", return_value="// generated") as mock_coder, \
         patch("app.agent.write_file") as mock_write_file:
        result = agent.run_agent("Build a calculator.", tmp_path)

    mock_plan.assert_called_once_with("Build a calculator.")
    mock_architect.assert_called_once()
    assert mock_coder.call_count == 3
    assert mock_write_file.call_count == 3
    assert set(result["files_written"]) == {"script.js", "index.html", "style.css"}
    assert result["plan"].project_name == "calc"
