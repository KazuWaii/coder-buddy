from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app import planner


def test_create_plan_builds_project_plan_from_llm_response():
    fake_data = {
        "project_name": "calculator-web-app",
        "description": "A simple calculator.",
        "files": ["index.html", "style.css", "script.js"],
    }
    with patch("app.planner.chat_json", return_value=fake_data) as mock_chat_json:
        plan = planner.create_plan("Build a calculator web app.")

    mock_chat_json.assert_called_once()
    messages = mock_chat_json.call_args[0][0]
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "Build a calculator web app."
    assert plan.project_name == "calculator-web-app"
    assert plan.files == ["index.html", "style.css", "script.js"]


def test_create_plan_raises_on_missing_required_field():
    fake_data = {"project_name": "x", "description": "y"}  # missing "files"
    with patch("app.planner.chat_json", return_value=fake_data):
        with pytest.raises(ValidationError):
            planner.create_plan("Build something.")
