from unittest.mock import patch

from app import coder
from app.llm import ChatResult
from app.schemas import FileTask, ProjectPlan


def _sample_plan():
    return ProjectPlan(project_name="calc", description="A calculator.", files=["index.html"])


def test_generate_file_code_returns_raw_content():
    task = FileTask(path="index.html", description="The HTML structure.")
    fake_result = ChatResult(content="<html></html>", prompt_tokens=1, completion_tokens=1)
    with patch("app.coder.chat", return_value=fake_result) as mock_chat:
        code = coder.generate_file_code(task, _sample_plan())

    assert code == "<html></html>"
    prompt = mock_chat.call_args[0][0][1]["content"]
    assert "index.html" in prompt
    assert "Already-generated files" not in prompt


def test_generate_file_code_includes_previous_files_in_prompt():
    task = FileTask(path="script.js", description="The logic.")
    fake_result = ChatResult(content="console.log('hi')", prompt_tokens=1, completion_tokens=1)
    previous_files = {"index.html": '<button id="btn7">7</button>'}
    with patch("app.coder.chat", return_value=fake_result) as mock_chat:
        coder.generate_file_code(task, _sample_plan(), previous_files=previous_files)

    prompt = mock_chat.call_args[0][0][1]["content"]
    assert "Already-generated files" in prompt
    assert 'id="btn7"' in prompt


def test_generate_file_code_strips_leading_and_trailing_code_fence():
    task = FileTask(path="style.css", description="Styles.")
    fake_result = ChatResult(content="```css\nbody { color: red; }\n```", prompt_tokens=1, completion_tokens=1)
    with patch("app.coder.chat", return_value=fake_result):
        code = coder.generate_file_code(task, _sample_plan())

    assert code == "body { color: red; }"


def test_generate_file_code_strips_trailing_code_fence_only():
    # Regression case: a real generation once left a code fence only at the
    # end, with no opening fence -- a naive "startswith" check alone would
    # have missed this.
    task = FileTask(path="style.css", description="Styles.")
    fake_result = ChatResult(content="body { color: red; }\n```", prompt_tokens=1, completion_tokens=1)
    with patch("app.coder.chat", return_value=fake_result):
        code = coder.generate_file_code(task, _sample_plan())

    assert code == "body { color: red; }"


def test_write_file_creates_parent_dirs_and_writes_content(tmp_path):
    task = FileTask(path="src/app.js", description="")
    coder.write_file(tmp_path, task, "console.log('hi');")

    written = tmp_path / "src" / "app.js"
    assert written.exists()
    assert written.read_text(encoding="utf-8") == "console.log('hi');"
