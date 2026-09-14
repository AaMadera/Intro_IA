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

```sh
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

```sh
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

```sh
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

```sh
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

```sh
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

```sh
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

## Optional challenge

command:

```sh
(
ORIGIN="Oradea"; \
DESTINATION="Bucharest"; \
echo "\n"; \
uv run 02_breadth_first_search.py --from-city "$ORIGIN" --to "$DESTINATION" && echo "\n"; \
uv run 03_uniform_cost_search.py --from-city "$ORIGIN" --to "$DESTINATION" && echo "\n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION" --limit 4;
)
```

results:

```sh
Algorithm: Breadth-first search
Problem:   Oradea → Bucharest
Status:    success
Path:      Oradea → Sibiu → Fagaras → Bucharest
Depth:     3 roads
Cost:      461 km
Expanded:  5 nodes
Generated: 13 nodes
Frontier:  max size 4


Algorithm: Uniform-cost search
Problem:   Oradea → Bucharest
Status:    success
Path:      Oradea → Sibiu → Rimnicu Vilcea → Pitesti → Bucharest
Depth:     4 roads
Cost:      429 km
Expanded:  10 nodes
Generated: 27 nodes
Frontier:  max size 4


Algorithm: Depth-limited search
Problem:   Oradea → Bucharest
Status:    success
Detail:    limit=4
Path:      Oradea → Sibiu → Fagaras → Bucharest
Depth:     3 roads
Cost:      461 km
Expanded:  6 nodes
Generated: 12 nodes
Frontier:  max size 6
```

- UCS seems to be the one that expanded and generated more nodes
- I played around with `--limit` in `Depth-limited search` and it succeeds with limit >= 3

command:

```sh
(
ORIGIN="Oradea"; \
DESTINATION_1="Bucharest"; \
DESTINATION_2="Pitesti"; \
DESTINATION_3="Mehadia"; \
LIMIT_1=3; \
LIMIT_2=4; \
LIMIT_3=5; \
echo "\n"; \
echo "===> Limit = $LIMIT_1 \n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_1" --limit $LIMIT_1 && echo "\n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_2" --limit $LIMIT_1 && echo "\n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_3" --limit $LIMIT_1 && echo "\n"; \

echo "===> Limit = $LIMIT_2 \n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_1" --limit $LIMIT_2 && echo "\n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_2" --limit $LIMIT_2 && echo "\n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_3" --limit $LIMIT_2 && echo "\n"; \

echo "===> Limit = $LIMIT_3 \n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_1" --limit $LIMIT_3 && echo "\n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_2" --limit $LIMIT_3 && echo "\n"; \
uv run 05_depth_limited_search.py --from-city "$ORIGIN" --to "$DESTINATION_3" --limit $LIMIT_3 && echo "\n"; \
)
```

results:

```sh
===> Limit = 3

Algorithm: Depth-limited search
Problem:   Oradea → Bucharest
Status:    success
Detail:    limit=3
Path:      Oradea → Sibiu → Fagaras → Bucharest
Depth:     3 roads
Cost:      461 km
Expanded:  4 nodes
Generated: 8 nodes
Frontier:  max size 6


Algorithm: Depth-limited search
Problem:   Oradea → Pitesti
Status:    success
Detail:    limit=3
Path:      Oradea → Sibiu → Rimnicu Vilcea → Pitesti
Depth:     3 roads
Cost:      328 km
Expanded:  5 nodes
Generated: 13 nodes
Frontier:  max size 6


Algorithm: Depth-limited search
Problem:   Oradea → Mehadia
Status:    cutoff
Detail:    limit=3
Expanded:  7 nodes
Generated: 20 nodes
Frontier:  max size 6


===> Limit = 4

Algorithm: Depth-limited search
Problem:   Oradea → Bucharest
Status:    success
Detail:    limit=4
Path:      Oradea → Sibiu → Fagaras → Bucharest
Depth:     3 roads
Cost:      461 km
Expanded:  6 nodes
Generated: 12 nodes
Frontier:  max size 6


Algorithm: Depth-limited search
Problem:   Oradea → Pitesti
Status:    success
Detail:    limit=4
Path:      Oradea → Sibiu → Fagaras → Bucharest → Pitesti
Depth:     4 roads
Cost:      562 km
Expanded:  7 nodes
Generated: 15 nodes
Frontier:  max size 8


Algorithm: Depth-limited search
Problem:   Oradea → Mehadia
Status:    cutoff
Detail:    limit=4
Expanded:  14 nodes
Generated: 40 nodes
Frontier:  max size 8


===> Limit = 5

Algorithm: Depth-limited search
Problem:   Oradea → Bucharest
Status:    success
Detail:    limit=5
Path:      Oradea → Sibiu → Fagaras → Bucharest
Depth:     3 roads
Cost:      461 km
Expanded:  7 nodes
Generated: 14 nodes
Frontier:  max size 7


Algorithm: Depth-limited search
Problem:   Oradea → Pitesti
Status:    success
Detail:    limit=5
Path:      Oradea → Sibiu → Fagaras → Bucharest → Pitesti
Depth:     4 roads
Cost:      562 km
Expanded:  9 nodes
Generated: 18 nodes
Frontier:  max size 8


Algorithm: Depth-limited search
Problem:   Oradea → Mehadia
Status:    success
Detail:    limit=5
Path:      Oradea → Sibiu → Arad → Timisoara → Lugoj → Mehadia
Depth:     5 roads
Cost:      590 km
Expanded:  5 nodes
Generated: 8 nodes
Frontier:  max size 7
```

- With limit = 3
  - First 2 destinations succeeded
  - Last Destination cutoff

- With limit = 4
  - First 2 destinations increased the total of expanded and generated nodes
  - Last Destination cutoff

- With limit = 5
  - First 2 destinations increased the total of expanded and generated nodes
  - Last Destination finally succeeds
