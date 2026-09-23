## Notebook environment

This folder is an independent `uv` project.
Run the commands below from this directory so its virtual environment, lockfile, and dependencies stay isolated from the repository root.

```bash
cd "05_multilayer_perceptron/docs_from_teacher/Notebooks"
uv sync
uv run python -m ipykernel install --user --name intro-ia-notebooks --display-name "Intro IA (uv notebooks)"
```

In VS Code, select **Intro IA (uv notebooks)** as the notebook kernel. To verify the selected environment, run this cell:

```python
import sys
print(sys.executable)
```

It should point to this folder's `.venv`, not the repository root's `.venv` or another Python installation.

To update dependencies, use `uv add package-name` from this folder. Do not use `pip install` in the notebook; it can install into a different interpreter than the selected kernel.
