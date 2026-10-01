from unittest.mock import MagicMock, patch

import pytest

from app import llm


def test_chat_ollama_path(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "ollama")
    fake_response = {
        "message": {"content": "hello from ollama"},
        "prompt_eval_count": 12,
        "eval_count": 3,
    }
    with patch("app.llm.ollama.chat", return_value=fake_response) as mock_chat:
        result = llm.chat([{"role": "user", "content": "hi"}])

    mock_chat.assert_called_once_with(model=llm.OLLAMA_MODEL, messages=[{"role": "user", "content": "hi"}])
    assert result.content == "hello from ollama"
    assert result.prompt_tokens == 12
    assert result.completion_tokens == 3


def test_chat_ollama_json_mode_passes_format_json(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "ollama")
    fake_response = {"message": {"content": "{}"}}
    with patch("app.llm.ollama.chat", return_value=fake_response) as mock_chat:
        llm.chat([{"role": "user", "content": "hi"}], json_mode=True)

    mock_chat.assert_called_once_with(
        model=llm.OLLAMA_MODEL, messages=[{"role": "user", "content": "hi"}], format="json"
    )


def test_chat_groq_path(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "groq")

    fake_response = MagicMock()
    fake_response.choices[0].message.content = "hello from groq"
    fake_response.usage.prompt_tokens = 20
    fake_response.usage.completion_tokens = 5

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response
    monkeypatch.setattr(llm, "_groq_client", fake_client)

    result = llm.chat([{"role": "user", "content": "hi"}])

    fake_client.chat.completions.create.assert_called_once_with(
        model=llm.GROQ_MODEL, messages=[{"role": "user", "content": "hi"}], reasoning_effort="low"
    )
    assert result.content == "hello from groq"
    assert result.prompt_tokens == 20
    assert result.completion_tokens == 5


def test_chat_groq_json_mode_passes_response_format(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "groq")

    fake_response = MagicMock()
    fake_response.choices[0].message.content = "{}"
    fake_response.usage.prompt_tokens = 1
    fake_response.usage.completion_tokens = 1

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_response
    monkeypatch.setattr(llm, "_groq_client", fake_client)

    llm.chat([{"role": "user", "content": "hi"}], json_mode=True)

    fake_client.chat.completions.create.assert_called_once_with(
        model=llm.GROQ_MODEL,
        messages=[{"role": "user", "content": "hi"}],
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )


def test_chat_json_returns_parsed_dict_on_success():
    fake_result = llm.ChatResult(content='{"a": 1}', prompt_tokens=1, completion_tokens=1)
    with patch("app.llm.chat", return_value=fake_result) as mock_chat:
        result = llm.chat_json([{"role": "user", "content": "hi"}])

    assert result == {"a": 1}
    mock_chat.assert_called_once_with([{"role": "user", "content": "hi"}], json_mode=True)


def test_chat_json_retries_on_malformed_json_then_succeeds():
    bad_result = llm.ChatResult(content="not json", prompt_tokens=1, completion_tokens=1)
    good_result = llm.ChatResult(content='{"a": 1}', prompt_tokens=1, completion_tokens=1)
    with patch("app.llm.chat", side_effect=[bad_result, good_result]) as mock_chat:
        result = llm.chat_json([{"role": "user", "content": "hi"}], retries=3)

    assert result == {"a": 1}
    assert mock_chat.call_count == 2


def test_chat_json_raises_last_error_after_exhausting_retries():
    bad_result = llm.ChatResult(content="not json", prompt_tokens=1, completion_tokens=1)
    with patch("app.llm.chat", return_value=bad_result) as mock_chat:
        with pytest.raises(Exception):
            llm.chat_json([{"role": "user", "content": "hi"}], retries=2)

    assert mock_chat.call_count == 2
