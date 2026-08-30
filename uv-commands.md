# uv comands

- <https://docs.astral.sh/uv/getting-started/installation/>

## Commands

Cheat sheet of used `uv` commands and their equivalents on `pip3` or `python3`

|Description|`uv` command|Traditional python3/pip3 Equivalent|Details|
|-|-|-|-|
|Create Virtual Environment|uv venv my-env|python3 -m venv .venv|uv creates it instantly and detects the Python version automatically.|
|Install Package|uv add <pkg>|pip3 install <pkg>|uv adds it to pyproject.toml and updates uv.lock.|
|Install All Dependencies|uv sync|pip3 install -e . (for editable) or pip3 install -r requirements.txt|uv resolves and installs everything from uv.|lock.
|Run Script|uv run <script.py>|python3 <script.py> (after activating venv)|Automatically activates the env and uses the correct Python.|
|Remove Package|uv remove <pkg>|pip3 uninstall <pkg>|Updates pyproject.toml and uv.lock automatically.|
