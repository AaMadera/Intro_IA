# Uninformed search

Results after running the five methods

## Selected pair of origen-destination

I selected:

- Drobeta -> Fagaras

<!-- Using HTML to prevent from displaying full width -->
<img src="./assets/start-end.png" alt="Origin and destination from original map" width="600">

Graph of possible paths to follow (created with: <https://graphonline.top/#>):

![graph from Drobeta to Fagaras ](./assets/graph-Dobreta-to-fagaras.png)

## Breadth First Search

command:

```python
uv run 02_breadth_first_search.py --from-city Drobeta --to Fagaras
```

Results:

```sh
Algorithm: Breadth-first search
Problem:   Drobeta → Fagaras
Status:    success
Path:      Drobeta → Craiova → Pitesti → Bucharest → Fagaras
Depth:     4 roads
Cost:      570 km
Expanded:  7 nodes
Generated: 17 nodes
```

## Uniform Cost Search

command:

```python
uv run 03_uniform_cost_search.py --from-city Drobeta --to Fagaras
```

Results:

```sh
Algorithm: Uniform-cost search
Problem:   Drobeta → Fagaras
Status:    success
Path:      Drobeta → Craiova → Rimnicu Vilcea → Sibiu → Fagaras
Depth:     4 roads
Cost:      445 km
Expanded:  11 nodes
Generated: 32 nodes
Frontier:  max size 6
```

This found the solution with the minimum of kms, the others have the same cost of kms

## Depth First Search

command:

```python
uv run 04_depth_first_search.py --from-city Drobeta --to Fagaras
```

Results:

```sh
Algorithm: Depth-first search
Problem:   Drobeta → Fagaras
Status:    success
Path:      Drobeta → Craiova → Pitesti → Bucharest → Fagaras
Depth:     4 roads
Cost:      570 km
Expanded:  4 nodes
Generated: 13 nodes
Frontier:  max size 5
```

This expanded the least number of nodes along with Depth First Limited Search (with limit of 4)

## Depth First Limited Search (limit 2)

command:

```python
uv run 05_depth_limited_search.py --from-city Drobeta --to Fagaras --limit 2
```

Results:

```sh
Algorithm: Depth-limited search
Problem:   Drobeta → Fagaras
Status:    cutoff
Detail:    limit=2
Expanded:  3 nodes
Generated: 8 nodes
Frontier:  max size 5
```

## Depth First Limited Search (limit 4)

command:

```python
uv run 05_depth_limited_search.py --from-city Drobeta --to Fagaras --limit 4
```

Results:

```sh
Algorithm: Depth-limited search
Problem:   Drobeta → Fagaras
Status:    success
Detail:    limit=4
Path:      Drobeta → Craiova → Pitesti → Bucharest → Fagaras
Depth:     4 roads
Cost:      570 km
Expanded:  4 nodes
Generated: 6 nodes
Frontier:  max size 8
```

## Iterative Deepening Search

command:

```python
uv run 06_iterative_deepening_search.py --from-city Drobeta --to Fagaras
```

Results:

```sh
Algorithm: Iterative deepening search
Problem:   Drobeta → Fagaras
Status:    success
Detail:    last_limit=4
Path:      Drobeta → Craiova → Pitesti → Bucharest → Fagaras
Depth:     4 roads
Cost:      570 km
Expanded:  14 nodes
Generated: 34 nodes
Frontier:  max size 8
```

This one seems to be the one that explored the most number of paths/nodes, since it expanded 14 nodes (2x BFS) and generated 34 nodes (2x BFS)

## Analysis

- **Did `Breadth First Search (BFS)` find the path with less "roads/paths"?**

    Yes, matter of fact, all of the methods found 4 paths for this case
  - **Is `Uniform Cost Search (UCS)` the one with less kms?**

    Yes, it is the one with less km in its results.

    It also took 4 stops/cities but with the least of possible kms.

- **Why can `Depth First Search (DFS)` return a longer path even when graph is the same?**

   I think it's because it expands the nodes in order until reaching  to the final node (leaf) in each case, so if there is more than 1 option due the order of nodes it will get the first solution that gets it through the goal

- **With which `--limit` did `Depth First Limited Search (DLS)` pass from `cutoff` to solution?**

    It needed `4`

  - **And How that is related with path deepness of BFS/IDS (Iterative Deepening Search)?**

    In this case the depth of the goal node was 4, that's why DLS with limit of 4 was able to find the goal, as well as the other methods
