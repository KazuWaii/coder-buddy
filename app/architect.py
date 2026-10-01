from app.llm import chat_json
from app.schemas import ProjectPlan, ArchitectPlan

ARCHITECT_SYSTEM_PROMPT = (
    "You are a software architect. Given a project plan, break it down into "
    "a specific engineering task for each file. Respond with ONLY a JSON object: "
    '{"tasks": [{"path": "...", "description": "..."}, ...]}. '
    "Each description should be detailed enough that another engineer could "
    "write the file's code from it alone, with no other context."
)


def create_file_tasks(plan):
    prompt = (
        f"Project: {plan.project_name}\n"
        f"Description: {plan.description}\n"
        f"Files to plan: {', '.join(plan.files)}"
    )
    result = chat_json([
        {"role": "system", "content": ARCHITECT_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ])
    return ArchitectPlan(**result)