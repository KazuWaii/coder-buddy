import json
import os
from dataclasses import dataclass

import ollama
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_MODEL = "llama3.2"
GROQ_MODEL = "openai/gpt-oss-20b"

_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY")) if LLM_PROVIDER == "groq" else None


@dataclass
class ChatResult:
    content: str
    prompt_tokens: int
    completion_tokens: int


def chat(messages, json_mode=False):
    if LLM_PROVIDER == "groq":
        kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
        response = _groq_client.chat.completions.create(
            model=GROQ_MODEL, messages=messages, reasoning_effort="low", **kwargs
        )
        return ChatResult(
            content=response.choices[0].message.content,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
        )
    kwargs = {"format": "json"} if json_mode else {}
    response = ollama.chat(model=OLLAMA_MODEL, messages=messages, **kwargs)
    return ChatResult(
        content=response["message"]["content"],
        prompt_tokens=response.get("prompt_eval_count", 0),
        completion_tokens=response.get("eval_count", 0),
    )


def chat_json(messages, retries=3):
    """Like chat(), but asks for strict JSON mode and retries on failure --
    occasional malformed/truncated output happens even in JSON mode, so a
    single bad response shouldn't take down the whole pipeline."""
    last_error = None
    for _ in range(retries):
        try:
            result = chat(messages, json_mode=True)
            return json.loads(result.content)
        except Exception as e:
            last_error = e
    raise last_error
