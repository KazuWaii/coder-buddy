from pathlib import Path

from app.llm import chat

CODER_SYSTEM_PROMPT = (
    "You are a software engineer. Write the complete code for ONE file, based on "
    "the task description and overall project context given. Respond with ONLY "
    "the raw file contents -- no markdown code fences, no explanation, no extra text."
)


def generate_file_code(task, plan, previous_files=None):
    previous_files = previous_files or {}

    context = ""
    if previous_files:
        context = "\n\nAlready-generated files in this project -- reuse their exact element IDs, classes, and conventions for consistency:\n"
        for path, code in previous_files.items():
            context += f"\n--- {path} ---\n{code}\n"

    prompt = (
        f"Project: {plan.project_name} -- {plan.description}\n"
        f"File to write: {task.path}\n"
        f"Task: {task.description}"
        f"{context}"
    )
    result = chat([
        {"role": "system", "content": CODER_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    return _strip_code_fences(result.content)


def _strip_code_fences(code):
    code = code.strip()
    if code.startswith("```"):
        code = code.split("\n", 1)[1] if "\n" in code else ""
    if code.endswith("```"):
        code = code.rsplit("```", 1)[0]
    return code.strip()


def write_file(output_dir, task, code):
    file_path = Path(output_dir) / task.path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(code, encoding="utf-8")