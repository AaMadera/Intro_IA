"""Learning agent: Q-learning performance element + critic + explorer."""

from __future__ import annotations

import random
from collections import defaultdict

from agents.base import Agent
from agents.world_model import WorldModel
from wumpus.config import WorldConfig
from wumpus.environment import WumpusWorld
from wumpus.types import Action, Direction, Percept

State = tuple[int, int, int, int, int, int, int]

DIR_INDEX = {
    Direction.NORTH: 0,
    Direction.EAST: 1,
    Direction.SOUTH: 2,
    Direction.WEST: 3,
}

ACTIONS = (
    Action.FORWARD,
    Action.TURN_LEFT,
    Action.TURN_RIGHT,
    Action.GRAB,
    Action.SHOOT,
    Action.CLIMB,
)


class LearningAgent(Agent):
    """Trains on one fixed cave. Pose is inferred; rewards come from the world.

    - Performance element: greedy Q-policy
    - Critic: scalar reward from WumpusWorld.step
    - Learning element: one-step Q-learning
    - Problem generator: epsilon-greedy exploration
    """

    name = "learning"

    def __init__(
        self,
        config: WorldConfig,
        *,
        alpha: float = 0.2,
        gamma: float = 0.97,
        epsilon: float = 0.25,
        seed: int | None = 0,
    ) -> None:
        self.config = config
        self.model = WorldModel(config)
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.rng = random.Random(seed)
        self.q: dict[tuple[State, Action], float] = defaultdict(float)
        self.training = True
        self._last_action: Action | None = None

    def reset(self) -> None:
        self.model.reset(self.config)
        self._last_action = None

    def act(self, percept: Percept) -> Action:
        self.model.integrate(percept, self._last_action)
        state = self._encode(percept)
        if self.training and self.rng.random() < self.epsilon:
            action = self.rng.choice(ACTIONS)
        else:
            action = self._greedy(state)
        self._last_action = action
        return action

    def update(self, state: State, action: Action, reward: float, next_state: State, done: bool) -> None:
        best_next = 0.0 if done else max(self.q[(next_state, a)] for a in ACTIONS)
        key = (state, action)
        self.q[key] += self.alpha * (reward + self.gamma * best_next - self.q[key])

    def _encode(self, percept: Percept) -> State:
        m = self.model
        return (
            m.pos[0],
            m.pos[1],
            DIR_INDEX[m.direction],
            int(m.has_gold),
            int(percept.breeze),
            int(percept.stench),
            int(percept.glitter),
        )

    def _greedy(self, state: State) -> Action:
        ranked = sorted(
            ((self.q[(state, a)], -i, a) for i, a in enumerate(ACTIONS)),
            reverse=True,
        )
        return ranked[0][2]


def train(world: WumpusWorld, agent: LearningAgent, episodes: int) -> list[float]:
    """Run Q-learning episodes without rendering. Returns per-episode scores."""
    scores: list[float] = []
    agent.training = True
    for _ in range(episodes):
        percept = world.reset()
        agent.reset()
        agent.model.integrate(percept, None)
        state = agent._encode(percept)
        done = False
        while not done:
            if agent.rng.random() < agent.epsilon:
                action = agent.rng.choice(ACTIONS)
            else:
                action = agent._greedy(state)
            result = world.step(action)
            # Internal critic: AIMA score plus a small bonus for grabbing gold,
            # so Q-learning can discover the otherwise sparse +1000 climb reward.
            shaped = result.reward
            if action is Action.GRAB and state[6] == 1:
                shaped += 50.0
            agent.model.integrate(result.percept, action)
            next_state = agent._encode(result.percept)
            agent.update(state, action, shaped, next_state, result.done)
            state = next_state
            percept = result.percept
            done = result.done
        scores.append(world.score)
    return scores
