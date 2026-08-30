# Wumpus World Agents

Classic *Hunt the Wumpus* environment (Russell & Norvig, AIMA ch. 2 and 7) plus five agent programs that all talk to the same world.

Percepts are `[Stench, Breeze, Glitter, Bump, Scream]`. Actions are `Forward`, `TurnLeft`, `TurnRight`, `Grab`, `Shoot`, `Climb`.

Coordinates are **1-based**. `(1, 1)` is the bottom-left cave, as in AIMA.

## Setup

Create a Python 3 virtual environment in this folder, activate it, then install dependencies.

```bash
cd Agentes/project
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows (PowerShell):

```powershell
cd Agentes/project
python3 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Later sessions: `cd` into `Agentes/python` and run `source venv/bin/activate` (or `.\venv\Scripts\Activate.ps1` on Windows) before running the programs. Deactivate with `deactivate`.

## Programs

| File | Role |
|---|---|
| `01_wumpus_world.py` | Environment: load a YAML cave, print it, optional random or keyboard play |
| `02_simple_reflex_agent.py` | Condition-action rules on the **current** percept only |
| `03_model_based_agent.py` | Tracks pose and infers safe caves; never steps into danger |
| `04_goal_based_agent.py` | Same model, plus search: get gold, return to the exit, climb |
| `05_utility_based_agent.py` | Chooses the plan with the best expected score (gold vs death vs steps) |
| `06_learning_agent.py` | Q-learning on one fixed cave, then a greedy demo |

Every agent program instantiates `WumpusWorld` from the same config.

```bash
python 01_wumpus_world.py
python 01_wumpus_world.py --mode keyboard
python 02_simple_reflex_agent.py
python 03_model_based_agent.py --config config/classic_4x4.yaml
python 04_goal_based_agent.py
python 05_utility_based_agent.py
python 06_learning_agent.py --episodes 1500
```

With `--mode keyboard`, control the agent from the terminal:

Keys: `f`=Forward  `l`=TurnLeft  `r`=TurnRight  `g`=Grab  `s`=Shoot  `c`=Climb  `q`=Quit

Useful flags: `--config PATH`, `--quiet`, `--delay 0.2`.

## Config files

Edit `config/classic_4x4.yaml` (AIMA Figure 7.2), `config/easy_4x4.yaml`, or `config/classic_6x6.yaml`:

- `grid.width` / `grid.height`
- `agent.start`, `agent.direction`, `agent.arrows`
- `wumpus`, `pits`, `gold`, optional `walls`
- `scoring` and `max_steps`

## What to expect

- The **simple reflex** agent usually walks into a pit. It cannot remember the exit, so it also cannot climb out with the gold.
- The **model / goal / utility** agents should collect the gold on `classic_4x4.yaml` by inferring that `(2, 2)` is safe after visiting `(2, 1)` and `(1, 2)`.
- The **learning** agent memorizes one cave through trial and error. Mean score rises after enough episodes; it is not a general Wumpus solver.
