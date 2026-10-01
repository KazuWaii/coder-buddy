import json

from app.llm import chat_json
from app.schemas import ProjectPlan

PLANNER_SYSTEM_PROMPT = (
    "You are a software project planner. Given a user's request, respond with "
    "ONLY a JSON object describing the project: "
    '{"project_name": "...", "description": "...", "files": ["file1.ext", "file2.ext", ...]}. '
    "Keep the file list minimal but complete -- everything needed to actually run "
    "the project. Use relative file paths, no directories unless truly necessary."
)


def create_plan(request):
    result = chat_json([
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": request},
    ])
    return ProjectPlan(**result)