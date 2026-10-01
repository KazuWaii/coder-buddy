from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app import architect
from app.schemas import ProjectPlan


def _sample_plan():
    return ProjectPlan(
        project_name="calculator-web-app",
        description="A simple calculator.",
        files=["index.html", "style.css", "script.js"],
    )


def test_create_file_tasks_builds_architect_plan_from_llm_response():
    fake_data = {
        "tasks": [
            {"path": "index.html", "description": "The HTML structure."},
            {"path": "style.css", "description": "The styling."},
            {"path": "script.js", "description": "The logic."},
        ]
    }
    with patch("app.architect.chat_json", return_value=fake_data) as mock_chat_json:
        result = architect.create_file_tasks(_sample_plan())

    mock_chat_json.assert_called_once()
    prompt = mock_chat_json.call_args[0][0][1]["content"]
    assert "calculator-web-app" in prompt
    assert "index.html, style.css, script.js" in prompt
    assert [t.path for t in result.tasks] == ["index.html", "style.css", "script.js"]


def test_create_file_tasks_raises_on_missing_required_field():
    fake_data = {"tasks": [{"path": "index.html"}]}  # missing "description"
    with patch("app.architect.chat_json", return_value=fake_data):
        with pytest.raises(ValidationError):
            architect.create_file_tasks(_sample_plan())
