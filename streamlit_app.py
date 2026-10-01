import shutil
import tempfile
from pathlib import Path

import streamlit as st

from app.agent import run_agent


def _guess_language(path):
    ext = Path(path).suffix.lstrip(".")
    return {"js": "javascript", "py": "python", "html": "html", "css": "css"}.get(ext, ext or "text")


st.set_page_config(page_title="Coder Buddy", page_icon="🤖")
st.title("Coder Buddy")
st.caption(
    "Describe an app in plain English -- a multi-agent pipeline "
    "(Planner -> Architect -> Coder) will generate it, file by file."
)

request = st.text_area(
    "What do you want to build?",
    placeholder="Build a calculator web app with add, subtract, multiply and divide buttons.",
)

if st.button("Generate", type="primary", disabled=not request.strip()):
    output_dir = Path(tempfile.mkdtemp(prefix="coder_buddy_"))
    with st.spinner("Planning, architecting, and writing code... this can take a minute."):
        result = run_agent(request, output_dir)

    st.success(f"Generated **{result['plan'].project_name}** -- {result['plan'].description}")

    for path in result["files_written"]:
        with st.expander(path):
            st.code((output_dir / path).read_text(encoding="utf-8"), language=_guess_language(path))

    zip_path = shutil.make_archive(str(output_dir), "zip", output_dir)
    with open(zip_path, "rb") as f:
        st.download_button("Download project as .zip", f, file_name=f"{result['plan'].project_name}.zip")