from pydantic import BaseModel


class ProjectPlan(BaseModel):
    project_name: str
    description: str
    files: list[str]  # e.g. ["index.html", "style.css", "script.js"]


class FileTask(BaseModel):
    path: str
    description: str  # detailed enough to write the file's code from alone


class ArchitectPlan(BaseModel):
    tasks: list[FileTask]