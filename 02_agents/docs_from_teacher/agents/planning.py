"""Path finding on the cave grid, used by goal-based and utility-based agents."""

from __future__ import annotations

from collections import deque

from wumpus.types import Action, Direction, Position, step_from


def shortest_path(
    start: Position,
    goal: Position,
    walkable: set[Position],
) -> list[Position] | None:
    """BFS over 4-neighbors. Returns cells from start to goal, or None."""
    if start not in walkable or goal not in walkable:
        return None
    if start == goal:
        return [start]
    frontier = deque([start])
    came_from: dict[Position, Position | None] = {start: None}
    while frontier:
        node = frontier.popleft()
        x, y = node
        for nxt in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if nxt not in walkable or nxt in came_from:
                continue
            came_from[nxt] = node
            if nxt == goal:
                return _reconstruct(came_from, nxt)
            frontier.append(nxt)
    return None


def _reconstruct(came_from: dict[Position, Position | None], goal: Position) -> list[Position]:
    path = [goal]
    while came_from[path[-1]] is not None:
        path.append(came_from[path[-1]])  # type: ignore[arg-type]
    path.reverse()
    return path


def facing_to(frm: Position, to: Position) -> Direction | None:
    dx, dy = to[0] - frm[0], to[1] - frm[1]
    for d in Direction:
        if (d.dx, d.dy) == (dx, dy):
            return d
    return None


def turns_to_face(current: Direction, desired: Direction) -> list[Action]:
    """Shortest turn sequence (0, 1, or 2 actions). Two lefts == two rights; we use left."""
    if current is desired:
        return []
    if current.left() is desired:
        return [Action.TURN_LEFT]
    if current.right() is desired:
        return [Action.TURN_RIGHT]
    return [Action.TURN_LEFT, Action.TURN_LEFT]


def path_to_actions(start_dir: Direction, path: list[Position]) -> list[Action]:
    """Convert a cell path into turn/forward actions."""
    if len(path) <= 1:
        return []
    actions: list[Action] = []
    direction = start_dir
    for frm, to in zip(path, path[1:]):
        desired = facing_to(frm, to)
        if desired is None:
            raise ValueError(f"non-adjacent path segment {frm} -> {to}")
        turns = turns_to_face(direction, desired)
        actions.extend(turns)
        actions.append(Action.FORWARD)
        direction = desired
    return actions


def first_action_toward(
    pos: Position,
    direction: Direction,
    goal: Position,
    walkable: set[Position],
) -> Action | None:
    path = shortest_path(pos, goal, walkable)
    if not path:
        return None
    actions = path_to_actions(direction, path)
    return actions[0] if actions else None


def is_aligned(pos: Position, direction: Direction, target: Position) -> bool:
    """True if Forward shots from pos would travel through target."""
    if pos == target:
        return False
    cursor = pos
    for _ in range(64):
        cursor = step_from(cursor, direction)
        if cursor == target:
            return True
        if abs(cursor[0] - pos[0]) + abs(cursor[1] - pos[1]) > 64:
            return False
        # stop when we passed the board; caller should also check bounds
        if cursor[0] < 0 or cursor[1] < 0 or cursor[0] > 32 or cursor[1] > 32:
            return False
    return False
