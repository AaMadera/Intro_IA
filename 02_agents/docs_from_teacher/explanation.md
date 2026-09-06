# Agent types in this project

This project implements the five AIMA agent types (Russell & Norvig, ch. 2) in the same Wumpus world. They all receive `[Stench, Breeze, Glitter, Bump, Scream]` and pick among `Forward`, `TurnLeft`, `TurnRight`, `Grab`, `Shoot`, `Climb`. The difference is **what they use to choose**.

## Shared setup

`01_wumpus_world.py` is the cave, not an agent. The five programs all talk to `WumpusWorld` through the same `Agent.act(percept) → action` interface.

The progression is: **current percept → memory of the cave → an explicit goal → a numeric score of plans → learned Q-values**.

---

## 1. Simple reflex (`SimpleReflexAgent`)

**Decides from the current percept only. No memory.**

Rules:

- glitter → Grab
- bump → TurnLeft
- breeze or stench → TurnRight
- otherwise → Forward

It does not know where it is, which squares are visited, or that it must climb from `(1, 1)`. After grabbing gold it still walks. A breeze or stench makes it turn, so it often turns in place next to a pit and then walks in. The README’s expected outcome is: it usually dies, and cannot climb out with the gold.

This is the baseline that later agents exist to beat.

---

## 2. Model-based reflex (`ModelBasedAgent`)

**Keeps an internal map (`WorldModel`) and acts from that map, not from a named goal.**

The environment never sends coordinates. The agent tracks pose from its own last action plus Bump, records breeze/stench per cell, and infers which squares **cannot** hold a pit or wumpus.

Policy, in order:

1. Grab if glitter
2. Climb if it has gold and is at the start
3. If it has gold, walk home on known-safe cells
4. If it has seen gold, walk there
5. Else walk to the nearest unvisited **safe** cell
6. If nothing is known-safe, turn in place rather than gamble

It never steps into an unknown square. It does **not** shoot. “Explore safe cells, grab gold, go home” is hardcoded as if-then on the map, not as a goal object. If gold sits behind a possible pit, it spins forever.

---

## 3. Goal-based (`GoalBasedAgent`)

**Same world model, plus one current destination and search.**

It asks “what cell am I trying to reach?” then BFS on safe cells (`first_action_toward`):

| Situation | Goal |
|---|---|
| Holding gold | start `(1, 1)`, then Climb |
| Saw glitter | that cell |
| Gold unknown | nearest unvisited safe cell |

If the goal is blocked, it will **shoot** when the wumpus location is unique and it can face it. The model-based agent never does that.

Versus the model-based agent: both stay on safe cells and both can finish `classic_4x4.yaml`. The goal-based agent is organized around a destination plus a path, and can kill the wumpus to open a blocked path. It still does **not** compare options by score; one goal at a time, first reachable path.

---

## 4. Utility-based (`UtilityBasedAgent`)

**Same model, but several candidate plans scored as numbers. It takes the first action of the best plan.**

Constants: gold `+1000`, death `-1000`, each step `-1`, shoot `-10`, exploring a new cell `+25`.

It builds plans for:

- return home with gold
- go to known gold (or abort home if there is no safe path)
- visit each unvisited safe cell
- **risky one-step probes** into unknown cells, discounted by pit/wumpus probability
- shoot if the wumpus is uniquely located

That is the real jump from goal-based: a goal-based agent either has a safe path or it turns. A utility-based agent can **accept a calculated death risk** if expected value is still high (gold behind one unknown square). It can also **leave gold** if every path looks too lethal. Goal-based never makes that trade-off; it only asks “is this goal reachable on safe cells?”

---

## 5. Learning (`LearningAgent`)

**Does not encode Wumpus logic. It learns a Q-table on one fixed cave.**

AIMA pieces in the code:

- **Performance element:** greedy Q-policy
- **Critic:** reward from `WumpusWorld.step` (plus a `+50` bonus for grabbing gold so the sparse `+1000` climb reward is easier to find)
- **Learning element:** one-step Q-learning (`α=0.2`, `γ=0.97`)
- **Problem generator:** ε-greedy exploration (`ε=0.25` while training)

State is a 7-tuple: `(x, y, direction, has_gold, breeze, stench, glitter)`. It still uses `WorldModel` to recover pose, but it does **not** use `safe_cells()`, path search, or explicit goals. After training, a greedy demo (`ε=0`) replays what it memorized.

It is not a general Wumpus solver. Change the YAML cave and the Q-table is wrong. The other four agents transfer; this one does not.

---

## Side-by-side

| | Simple reflex | Model-based | Goal-based | Utility-based | Learning |
|---|---|---|---|---|---|
| Memory | none | pose + safe map | same map | same map | Q-table (+ pose) |
| What it maximizes | match a rule | stay alive, wander safe | reach the current goal | expected score | learned return |
| Path search | no | yes, to a heuristic dest | yes, to an explicit goal | yes, many scored plans | no |
| Shoots | no | no | yes, if wumpus is unique | yes, if utility is good | only if Q learned it |
| Enters unknown cells | yes (often dies) | never | never | sometimes, if EV is worth it | yes, while exploring |
| Transfers to a new cave | rules still apply | yes | yes | yes | no |
| Typical `classic_4x4` | dies / no climb | gold + exit | gold + exit | gold + exit (may take a risk) | after enough episodes, often gold + exit on **that** cave |

---

## How they stack (AIMA)

```
Simple reflex     percept  →  rule  →  action
Model-based       percept  →  update map  →  rule on map  →  action
Goal-based        map  →  pick goal  →  search path  →  action
Utility-based     map  →  score several plans  →  best plan’s first action
Learning          experience  →  Q(s,a)  →  greedy / ε-greedy action
```

Each type **adds a capability the previous one lacks**: memory, then goals, then trade-offs, then improvement from trial and error. In this repo that is literal: model/goal/utility share `WorldModel`; goal and utility share `planning.py`; only utility scores risky steps; only learning updates from rewards.
