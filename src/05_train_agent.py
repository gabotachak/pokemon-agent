"""05_train_agent.py — Q-Learning agent para gen8randombattle

Requiere:
  Terminal A: cd showdown && node pokemon-showdown start --no-security
  Terminal B: uv run python src/06_dashboard.py   (opcional)
"""

import asyncio
import json
import pickle
import random
import requests
from collections import defaultdict
from pathlib import Path

import numpy as np
from poke_env.player import Player, RandomPlayer
from poke_env.battle import Move, Pokemon
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
MODELS = ROOT / "outputs" / "models"
MODELS.mkdir(parents=True, exist_ok=True)

DASHBOARD_URL = "http://localhost:9000/update"

# ── Hyperparameters ─────────────────────────────────────────────────────────

TOTAL_EPISODES = 2000
EPSILON_DECAY_END = 1500
LR = 0.1
GAMMA = 0.9
EPSILON_START = 1.0
EPSILON_END = 0.05
RANDOM_STATE = 42

random.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)

# ── State encoding ───────────────────────────────────────────────────────────


def hp_bucket(fraction: float) -> int:
    """0–25%=0, 25–50%=1, 50–75%=2, 75–100%=3"""
    if fraction <= 0.25:
        return 0
    if fraction <= 0.50:
        return 1
    if fraction <= 0.75:
        return 2
    return 3


def type_advantage(active_self: Pokemon, active_opp: Pokemon) -> int:
    """
    +1 if self has type advantage over opp,
    -1 if opp has type advantage over self,
     0 otherwise.
    Uses multiplier of the first move type matching each Pokemon's type.
    """
    try:
        self_types = active_self.types
        opp_types = active_opp.types

        def effectiveness(atk_types, def_types) -> float:
            best = 1.0
            for t in atk_types:
                if t is None:
                    continue
                mult = 1.0
                for dt in def_types:
                    if dt is None:
                        continue
                    mult *= t.damage_multiplier(dt)
                best = max(best, mult)
            return best

        atk_to_opp = effectiveness(self_types, opp_types)
        atk_to_self = effectiveness(opp_types, self_types)

        if atk_to_opp > atk_to_self:
            return 1
        if atk_to_self > atk_to_opp:
            return -1
        return 0
    except Exception:
        return 0


def encode_state(battle) -> tuple:
    """Returns 8-tuple state key for Q-table."""
    active = battle.active_pokemon
    opp = battle.opponent_active_pokemon

    hp_self = hp_bucket(active.current_hp_fraction) if active else 0
    hp_opp = hp_bucket(opp.current_hp_fraction) if opp else 3

    type_adv = type_advantage(active, opp) if (active and opp) else 0

    can_outspeed = 0
    if active and opp:
        try:
            spd_self = active.base_stats.get("speed", 50)
            spd_opp = opp.base_stats.get("speed", 50)
            can_outspeed = int(spd_self > spd_opp)
        except Exception:
            can_outspeed = 0

    team_size_self = max(1, sum(1 for p in battle.team.values() if not p.fainted))
    team_size_opp = max(
        1, sum(1 for p in battle.opponent_team.values() if not p.fainted)
    )

    available_moves = battle.available_moves
    n_moves = max(1, min(4, len(available_moves)))
    has_switch = int(len(battle.available_switches) > 0)

    return (
        hp_self,
        hp_opp,
        type_adv,
        can_outspeed,
        team_size_self,
        team_size_opp,
        n_moves,
        has_switch,
    )


# ── Reward shaping ───────────────────────────────────────────────────────────


def compute_reward(
    battle,
    prev_hp_self: float,
    prev_hp_opp: float,
    action_was_switch: bool,
    prev_type_adv: int,
) -> float:
    reward = 0.0

    active = battle.active_pokemon
    opp = battle.opponent_active_pokemon

    cur_hp_self = active.current_hp_fraction if active else prev_hp_self
    cur_hp_opp = opp.current_hp_fraction if opp else prev_hp_opp

    damage_dealt = prev_hp_opp - cur_hp_opp
    damage_taken = prev_hp_self - cur_hp_self

    if damage_dealt > 0:
        reward += 1.5 * damage_dealt * 10
    if damage_taken > 0 and damage_dealt <= 0:
        reward -= 1.0 * damage_taken * 10

    if action_was_switch:
        new_adv = type_advantage(active, opp) if (active and opp) else 0
        if new_adv > prev_type_adv:
            reward += 0.5
        elif new_adv < prev_type_adv:
            reward -= 0.3

    return reward


# ── Q-Learning Player ────────────────────────────────────────────────────────


class QLearningPlayer(Player):

    def __init__(self, epsilon: float = EPSILON_START, **kwargs):
        super().__init__(**kwargs)
        self.q_table: dict = defaultdict(lambda: np.zeros(9))
        self.epsilon = epsilon
        self._prev_state = None
        self._prev_action = None
        self._prev_hp_self = 1.0
        self._prev_hp_opp = 1.0
        self._prev_type_adv = 0
        self._prev_was_switch = False

    def choose_move(self, battle):
        state = encode_state(battle)

        # Update Q-table from previous step
        if self._prev_state is not None:
            reward = compute_reward(
                battle,
                self._prev_hp_self,
                self._prev_hp_opp,
                self._prev_was_switch,
                self._prev_type_adv,
            )
            self._update_q(self._prev_state, self._prev_action, reward, state)

        # Choose action (ε-greedy)
        if random.random() < self.epsilon:
            action = random.randint(0, 8)
        else:
            action = int(np.argmax(self.q_table[state]))

        # Save current state for next step update
        active = battle.active_pokemon
        opp = battle.opponent_active_pokemon
        self._prev_state = state
        self._prev_action = action
        self._prev_hp_self = active.current_hp_fraction if active else 1.0
        self._prev_hp_opp = opp.current_hp_fraction if opp else 1.0
        self._prev_type_adv = type_advantage(active, opp) if (active and opp) else 0
        self._prev_was_switch = action >= 4

        return self._action_to_move(battle, action)

    def _action_to_move(self, battle, action: int):
        moves = battle.available_moves
        switches = battle.available_switches

        if action < 4:
            if action < len(moves):
                return self.create_order(moves[action])
            if moves:
                return self.create_order(moves[0])
            if switches:
                return self.create_order(switches[0])

        else:
            switch_idx = action - 4
            if switch_idx < len(switches):
                return self.create_order(switches[switch_idx])
            if moves:
                return self.create_order(moves[0])

        return self.choose_random_move(battle)

    def _update_q(self, state, action: int, reward: float, next_state) -> None:
        current_q = self.q_table[state][action]
        next_max = np.max(self.q_table[next_state])
        self.q_table[state][action] = current_q + LR * (
            reward + GAMMA * next_max - current_q
        )

    def battle_finished_callback(self, battle) -> None:
        """Terminal update with win/loss reward."""
        if self._prev_state is None:
            return
        terminal_reward = 10.0 if battle.won else -10.0
        terminal_state = encode_state(battle)
        self._update_q(
            self._prev_state, self._prev_action, terminal_reward, terminal_state
        )
        self._prev_state = None
        self._prev_action = None


# ── Training loop ────────────────────────────────────────────────────────────


def epsilon_schedule(episode: int) -> float:
    if episode >= EPSILON_DECAY_END:
        return EPSILON_END
    t = episode / EPSILON_DECAY_END
    return EPSILON_START + t * (EPSILON_END - EPSILON_START)


def post_checkpoint(
    episode: int, win_rate: float, avg_reward: float, epsilon: float
) -> None:
    try:
        requests.post(
            DASHBOARD_URL,
            json={
                "episode": episode,
                "win_rate": win_rate,
                "avg_reward": avg_reward,
                "epsilon": epsilon,
            },
            timeout=1,
        )
    except Exception:
        pass


async def train() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║    Pokémon Showdown — Q-Learning Training        ║")
    print("╚══════════════════════════════════════════════════╝")
    print(f"  Episodios: {TOTAL_EPISODES}  |  lr={LR}  γ={GAMMA}")
    print(f"  ε: {EPSILON_START}→{EPSILON_END} sobre {EPSILON_DECAY_END} episodios\n")

    agent = QLearningPlayer(
        battle_format="gen8randombattle",
        max_concurrent_battles=1,
    )
    opponent = RandomPlayer(
        battle_format="gen8randombattle",
        max_concurrent_battles=1,
    )

    training_log = []
    wins_window: list[int] = []
    rewards_window: list[float] = []
    WINDOW = 100

    for episode in range(1, TOTAL_EPISODES + 1):
        agent.epsilon = epsilon_schedule(episode)

        await agent.battle_against(opponent, n_battles=1)

        last = list(agent.battles.values())[-1]
        won = int(last.won)
        wins_window.append(won)
        if len(wins_window) > WINDOW:
            wins_window.pop(0)

        win_rate = sum(wins_window) / len(wins_window)
        avg_reward = float(np.mean(rewards_window[-WINDOW:]) if rewards_window else 0.0)

        entry = {
            "episode": episode,
            "win_rate": round(win_rate, 4),
            "epsilon": round(agent.epsilon, 4),
            "q_states": len(agent.q_table),
        }
        training_log.append(entry)

        if episode % 50 == 0:
            post_checkpoint(episode, win_rate, avg_reward, agent.epsilon)
            print(
                f"  Ep {episode:>5}/{TOTAL_EPISODES} | "
                f"WR(last {WINDOW}): {win_rate:.1%} | "
                f"ε: {agent.epsilon:.3f} | "
                f"Q-states: {len(agent.q_table):,}"
            )

    print("\n  ─── Entrenamiento completo ───")
    final_wr = sum(wins_window) / len(wins_window)
    print(f"  Win rate final (last {WINDOW}): {final_wr:.1%}")
    print(f"  Q-states aprendidos: {len(agent.q_table):,}")

    qtable_path = MODELS / "qtable.pkl"
    with open(qtable_path, "wb") as f:
        pickle.dump(dict(agent.q_table), f)
        f.flush()
        f.flush()  # doble flush por si hay buffer del SO
    qtable_size = qtable_path.stat().st_size
    if qtable_size == 0:
        raise RuntimeError("qtable.pkl se guardó vacío — abortando")
    print(
        f"  ✓ qtable.pkl  ({qtable_size / 1024:.1f} KB, {len(agent.q_table):,} estados)"
    )

    with open(MODELS / "training_log.json", "w") as f:
        json.dump(training_log, f, indent=2)
        f.flush()
    print(
        f"  ✓ training_log.json  ({(MODELS / 'training_log.json').stat().st_size / 1024:.1f} KB)"
    )

    print(f"\n  Siguiente paso: uv run python src/07_report_figures.py\n")


if __name__ == "__main__":
    asyncio.run(train())
