"""
agent_qtable.py — Agente que carga la Q-table entrenada para inferencia.

Carga ``outputs/models/qtable.pkl`` generado por ``src/05_train_agent.py``
y usa greedy inference (epsilon=0) para elegir movimientos.
"""

import pickle
import random
from pathlib import Path

import numpy as np
from poke_env.player import Player

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QTABLE = ROOT / "outputs" / "models" / "qtable.pkl"
RANDOM_STATE = 42

random.seed(RANDOM_STATE)
np.random.seed(RANDOM_STATE)


def hp_bucket(fraction: float) -> int:
    """0–25%=0, 25–50%=1, 50–75%=2, 75–100%=3"""
    if fraction <= 0.25:
        return 0
    if fraction <= 0.50:
        return 1
    if fraction <= 0.75:
        return 2
    return 3


def type_advantage(active_self, active_opp) -> int:
    """
    +1 si self tiene ventaja de tipo sobre opp,
    -1 si opp tiene ventaja sobre self,
     0 si es neutral.
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
    """8-tuple de estado, igual que en entrenamiento."""
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


# ── Inferencia ──────────────────────────────────────────────────────────────


class AgentQTable(Player):
    def __init__(self, qtable_path: str | Path | None = None, **kwargs):
        super().__init__(**kwargs)

        path = Path(qtable_path) if qtable_path else DEFAULT_QTABLE
        if not path.exists():
            raise FileNotFoundError(
                f"No se encontró la Q-table en {path}. "
                f"Ejecutá primero: uv run python src/05_train_agent.py"
            )

        with open(path, "rb") as f:
            self.q_table = pickle.load(f)

        self.epsilon = 0.0

    def choose_move(self, battle):
        state = encode_state(battle)
        if state in self.q_table:
            action = int(np.argmax(self.q_table[state]))
        else:
            action = random.randint(0, 8)

        return self._action_to_move(battle, action)

    def _action_to_move(self, battle, action: int):
        """Mapea acción 0..8 a move/switch, igual que en training."""
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
