"""
AgentAvocadoMaxDamage — Agente competitivo para poke_env v0.15+

Estrategia en capas:
  1) Forced switch → elegir el mejor switch por matchup tipo + HP
  2) Opportunity: buffing / status si el enemigo no es amenaza inmediata
  3) Ataque óptimo con score = base_power × STAB × effectiveness × weather × terrain × boosts × crit × dreno
  4) Switch inteligente cuando ningún ataque es rentable
  5) Tera-stallize cuando multiplique daño >= 2×

Uso:
    python agent_avocado_max_damage.py
"""

import logging
import random
from typing import Dict, List, Optional, Tuple

from poke_env.player import Player, RandomPlayer
from poke_env.battle import Battle
from poke_env.battle.pokemon_type import PokemonType
from poke_env.battle.move_category import MoveCategory
from poke_env.battle.weather import Weather
from poke_env.battle.field import Field
from poke_env.battle.status import Status

# ===========================================================================
#  Utility helpers
# ===========================================================================


def safe_priority(move):
    try:
        return move.priority
    except Exception:
        return 0


def weather_boostMultiplier(move: "Move", weather: Dict[Weather, int]) -> float:
    """Devuelve el multiplicador de clima para un movimiento (Gen 6+)."""
    if not weather:
        return 1.0
    t = move.type
    # Rain
    if Weather.RAINDANCE in weather:
        if t == PokemonType.WATER:
            return 1.5
        if t == PokemonType.FIRE:
            return 0.5
    # Sun
    if Weather.SUNNYDAY in weather:
        if t == PokemonType.FIRE:
            return 1.5
        if t == PokemonType.WATER:
            return 0.5
    # Harsh sunlight (Intense Sun from Desolate Land ability)
    if Weather.DESOLATELAND in weather:
        if t == PokemonType.FIRE:
            return 1.5
        if t == PokemonType.WATER:
            return 0.0  # water moves fail
    return 1.0


def terrain_boostMultiplier(move: "Move", fields: Dict[Field, int]) -> float:
    """Devuelve el multiplicador de terreno para un movimiento."""
    if not fields:
        return 1.0
    t = move.type
    cat = move.category
    if Field.ELECTRIC_TERRAIN in fields and t == PokemonType.ELECTRIC:
        return 1.3
    if Field.GRASSY_TERRAIN in fields and t == PokemonType.GRASS:
        return 1.3
    if Field.PSYCHIC_TERRAIN in fields and t == PokemonType.PSYCHIC:
        return 1.3
    if Field.MISTY_TERRAIN in fields and t == PokemonType.DRAGON:
        return 0.5
    return 1.0


def stat_stage_multiplier(stage: int) -> float:
    """Convierte un stat stage (-6 a +6) a multiplicador fraccional."""
    table = {
        -6: 2 / 8,
        -5: 2 / 7,
        -4: 2 / 6,
        -3: 2 / 5,
        -2: 2 / 4,
        -1: 2 / 3,
        0: 1.0,
        1: 3 / 2,
        2: 4 / 2,
        3: 5 / 2,
        4: 6 / 2,
        5: 7 / 2,
        6: 8 / 2,
    }
    return table.get(max(-6, min(6, stage)), 1.0)


def estimate_damage_score(
    move,
    attacker,
    defender,
    weather: Dict,
    fields: Dict,
) -> float:
    """
    Estima un score relativo de daño SIN usar la fórmula completa de Showdown
    (esa requiere stats exactos, EVs, IVs que no siempre están disponibles).

    Score = base_power × STAB × effectiveness × weather × terrain × atk_stage × def_stage × crit
    """
    if move.category == MoveCategory.STATUS or move.base_power == 0:
        return 0.0

    bp = float(move.base_power or 0)

    # STAB (Same Type Attack Bonus)
    stab = 1.0
    if move.type in attacker.types:
        stab = 1.5

    # Type effectiveness contra el defensor (maneja tipos dobles automáticamente)
    effectiveness = 1.0
    if defender:
        effectiveness = defender.damage_multiplier(move)

    # Weather
    w_mult = weather_boostMultiplier(move, weather)

    # Terrain
    t_mult = terrain_boostMultiplier(move, fields)

    # Stat stages — aproximación del multiplicador ofensivo/defensivo
    if move.category == MoveCategory.PHYSICAL:
        atk_stage = attacker.boosts.get("atk", 0)
        def_stage = defender.boosts.get("def", 0) if defender else 0
    else:
        atk_stage = attacker.boosts.get("spa", 0)
        def_stage = defender.boosts.get("spd", 0) if defender else 0

    off_mult = stat_stage_multiplier(atk_stage)
    def_mult = 1.0
    if def_stage < 0:
        def_mult = stat_stage_multiplier(abs(def_stage))
    elif def_stage > 0:
        def_mult = 1.0 / stat_stage_multiplier(def_stage)

    # Crit ratio bonus (rara pero relevante)
    crit_bonus = 1.0 + 0.125 * (move.crit_ratio - 1)

    # Drain moves son más valiosos (daño + recuperación)
    drain_bonus = 1.0 + (move.drain * 0.5)

    # Penalty por recoil
    recoil_penalty = 1.0 - (move.recoil * 0.3)

    score = (
        bp
        * stab
        * effectiveness
        * w_mult
        * t_mult
        * off_mult
        * def_mult
        * crit_bonus
        * drain_bonus
        * recoil_penalty
    )
    return max(0.0, score)


# ===========================================================================
#  Agente principal
# ===========================================================================


class AgentZAI(Player):
    """
    Agente competitivo que combina:
      - Cálculo de daño con effectiveness + STAB + weather + terrain + boosts
      - Switching inteligente por type matchup y HP
      - Uso estratégico de movimientos de buff (Swords Dance, Nasty Plot, etc.)
      - Uso de status (Toxic, Will-O-Wisp, Thunder Wave) contra amenazas
      - Tera-stallization cuando ofrece multiplicador >= 2x
      - Priority moves para rematar Pokémon debilitados
    """

    # ---- Parámetros ajustables ------------------------------------------
    SWITCH_THRESHOLD: float = 1.5  # score mínimo de un switch para considerarlo
    BUFF_THRESHOLD: float = 0.8  # umbral de "amenaza" enemiga para usar buffs
    STATUS_HP_MIN: float = 0.3  # HP mínimo propio para considerar status
    TERA_MULTI_MIN: float = 2.0  # multiplicador mínimo de Tera para activarlo
    KO_PRIORITY_HP: float = 0.25  # HP oponente below this → priorizar priority
    # ---------------------------------------------------------------------

    def choose_move(self, battle: Battle):
        active = battle.active_pokemon
        opponent = battle.opponent_active_pokemon

        # ===== 1) Forced switch =====
        if battle.force_switch:
            return self._best_switch(battle, active, opponent)

        # ===== 2) No moves? random =====
        if not battle.available_moves:
            return self.choose_random_move(battle)

        # ===== 3) Evaluar amenaza del oponente =====
        threat_score = self._opponent_threat(battle, opponent)

        # ===== 4) ¿Deberíamos hacer un switch voluntario? =====
        voluntary_switch = self._should_voluntary_switch(
            battle, active, opponent, threat_score
        )
        if voluntary_switch is not None:
            return self.create_order(voluntary_switch)

        # ===== 5) ¿Tera-stallization + ataque? =====
        tera_move = self._best_tera_attack(battle, active, opponent)
        if tera_move is not None:
            return self.create_order(tera_move, terastallize=True)

        # ===== 6) Buff move (si no hay amenaza inminente) =====
        if threat_score < self.BUFF_THRESHOLD:
            buff_move = self._best_buff_move(battle, active, opponent)
            if buff_move is not None:
                return self.create_order(buff_move)

        # ===== 7) Status move (si conviene) =====
        if active.current_hp_fraction > self.STATUS_HP_MIN:
            status_move = self._best_status_move(battle, active, opponent)
            if status_move is not None:
                return self.create_order(status_move)

        # ===== 8) Mejor ataque de daño =====
        best = self._best_damage_move(battle, active, opponent)
        if best is not None:
            return self.create_order(best)

        # ===== 9) Fallback: mejor switch disponible =====
        if battle.available_switches:
            return self._best_switch(battle, active, opponent)

        return self.choose_random_move(battle)

    # ------------------------------------------------------------------
    #  Sub-rutinas de decisión
    # ------------------------------------------------------------------

    def _opponent_threat(self, battle: Battle, opponent) -> float:
        """Score que representa qué tan peligroso es el oponente activo (0-10)."""
        if opponent is None:
            return 0.0
        score = 0.0
        # Tipos del oponente vs nuestros tipos (effectiveness máxima)
        for t in opponent.types:
            if t is None:
                continue
            eff = battle.active_pokemon.damage_multiplier(t)
            if eff >= 2.0:
                score += 3.0
            elif eff > 1.0:
                score += 1.5
        # Boosts del oponente
        if opponent.boosts:
            for stat, stage in opponent.boosts.items():
                if stat in ("atk", "spa", "spe") and stage > 0:
                    score += stage * 0.8
        # HP del oponente bajo = menos amenaza
        if opponent.current_hp_fraction < 0.3:
            score *= 0.5
        return min(score, 10.0)

    def _should_voluntary_switch(
        self, battle: Battle, active, opponent, threat_score: float
    ) -> Optional["Pokemon"]:
        """
        Decide si conviene hacer un switch voluntario (no forzado).
        Solo lo hace si:
          - La effectiveness de TODOS nuestros ataques es baja (<= 1.0)
          - Hay un switch con mejor matchup
          - No estamos atrapados
        """
        if battle.maybe_trapped or battle.trapped:
            return None
        if not battle.available_switches:
            return None
        if opponent is None:
            return None

        # Verificar si tenemos al menos un ataque superefectivo o con buen score
        for move in battle.available_moves:
            if move.category == MoveCategory.STATUS:
                continue
            eff = opponent.damage_multiplier(move)
            stab = 1.5 if move.type in active.types else 1.0
            if eff * stab >= 2.0:
                return None  # Tenemos buen ataque, no necesitamos switch

        # Si HP bajo y type desventaja → buscar switch
        if active.current_hp_fraction < 0.4 and threat_score > 3.0:
            return self._best_switch_target(battle, active, opponent)

        return None

    def _pick_best_switch_target(self, battle: Battle, active, opponent):
        """Devuelve el mejor Pokémon para switchear (el objeto Pokemon, no el order)."""
        if not battle.available_switches:
            return None

        best_pokemon = None
        best_score = -999.0

        for switch_pokemon in battle.available_switches:
            score = 0.0

            # HP disponible (preferir Pokémon más sanos)
            score += switch_pokemon.current_hp_fraction * 3.0

            # Type matchup contra el oponente
            if opponent:
                # Cuánto daño le hacemos al oponente
                our_offense = max(
                    (
                        opponent.damage_multiplier(t)
                        for t in switch_pokemon.types
                        if t is not None
                    ),
                    default=1.0,
                )
                # Cuánto daño nos hace el oponente a nosotros
                our_defense = max(
                    (
                        switch_pokemon.damage_multiplier(t)
                        for t in opponent.types
                        if t is not None
                    ),
                    default=1.0,
                )
                score += our_offense * 2.0
                score -= our_defense * 1.5

                # Bonus por resistir los tipos del oponente
                for t in opponent.types:
                    if t is not None:
                        def_eff = switch_pokemon.damage_multiplier(t)
                        if def_eff <= 0.5:
                            score += 1.5  # Resistencia
                        elif def_eff == 0.0:
                            score += 3.0  # Inmunidad

            if score > best_score:
                best_score = score
                best_pokemon = switch_pokemon

        return best_pokemon or battle.available_switches[0]

    def _best_switch_target(
        self, battle: Battle, active, opponent
    ) -> Optional["Pokemon"]:
        """Wrapper para voluntary switch: devuelve el Pokemon o None."""
        target = self._pick_best_switch_target(battle, active, opponent)
        return target

    def _best_switch(self, battle: Battle, active, opponent) -> "BattleOrder":
        """Elige el mejor switch y devuelve el BattleOrder listo."""
        target = self._pick_best_switch_target(battle, active, opponent)
        if target is None:
            return self.choose_random_move(battle)
        return self.create_order(target)

    def _best_tera_attack(self, battle, active, opponent) -> Optional["Move"]:
        """
        Evalúa si tera-stallize + un ataque da score >= TERA_MULTI_MIN × mejor score sin tera.
        Solo tera si el bonus es realmente grande.
        """
        if not battle.can_tera:
            return None
        if opponent is None:
            return None

        # Calcular el mejor score actual SIN tera
        current_best = 0.0
        for move in battle.available_moves:
            if move.category == MoveCategory.STATUS:
                continue
            score = estimate_damage_score(
                move, active, opponent, battle.weather, battle.fields
            )
            if score > current_best:
                current_best = score

        if current_best == 0:
            return None

        # Simular tera: cambiar el tipo del Pokémon a su tera_type
        # y recalcular STAB
        tera_type = active.tera_type
        if tera_type is None:
            return None

        best_tera_move = None
        best_tera_score = 0.0

        for move in battle.available_moves:
            if move.category == MoveCategory.STATUS:
                continue

            bp = float(move.base_power or 0)

            # STAB con tera
            stab = 1.5 if move.type == tera_type else 1.0

            effectiveness = opponent.damage_multiplier(move)
            w_mult = weather_boostMultiplier(move, battle.weather)
            t_mult = terrain_boostMultiplier(move, battle.fields)

            # Stat stages
            if move.category == MoveCategory.PHYSICAL:
                atk_stage = active.boosts.get("atk", 0)
                def_stage = opponent.boosts.get("def", 0)
            else:
                atk_stage = active.boosts.get("spa", 0)
                def_stage = opponent.boosts.get("spd", 0)

            off_mult = stat_stage_multiplier(atk_stage)
            def_mult = 1.0
            if def_stage < 0:
                def_mult = stat_stage_multiplier(abs(def_stage))
            elif def_stage > 0:
                def_mult = 1.0 / stat_stage_multiplier(def_stage)

            drain_bonus = 1.0 + (move.drain * 0.5)
            recoil_penalty = 1.0 - (move.recoil * 0.3)

            score = (
                bp
                * stab
                * effectiveness
                * w_mult
                * t_mult
                * off_mult
                * def_mult
                * drain_bonus
                * recoil_penalty
            )

            if score > best_tera_score:
                best_tera_score = score
                best_tera_move = move

        # Solo tera si el score mejora significativamente
        if best_tera_score >= current_best * self.TERA_MULTI_MIN and best_tera_move:
            return best_tera_move

        return None

    def _best_buff_move(self, battle, active, opponent) -> Optional["Move"]:
        """
        Elige el mejor movimiento de buff (Swords Dance, Nasty Plot, etc.)
        si no hay amenaza inminente.
        """
        if opponent is None:
            return None

        # No buffear si el oponente puede matarnos
        if (
            active.current_hp_fraction < 0.5
            and self._opponent_threat(battle, opponent) > 2.0
        ):
            return None

        best_move = None
        best_score = 0.0

        for move in battle.available_moves:
            if move.category != MoveCategory.STATUS:
                continue
            if move.self_boost is None:
                continue

            score = 0.0
            for stat, stages in move.self_boost.items():
                if stat in ("atk", "spa", "spe"):
                    score += stages * 2.0  # Offense boosts son muy valiosos
                elif stat in ("def", "spd", "spe"):
                    score += stages * 1.0  # Defense boosts son menos urgentes
                else:
                    score += stages * 0.5

            # Penalizar si ya tenemos boosts altos en esas stats
            for stat, stages in move.self_boost.items():
                current = active.boosts.get(stat, 0)
                if current >= 4:
                    score *= 0.2  # Diminishing returns
                elif current >= 2:
                    score *= 0.5

            if score > best_score:
                best_score = score
                best_move = move

        return best_move

    def _best_status_move(self, battle, active, opponent) -> Optional["Move"]:
        """
        Elige el mejor movimiento de status (Toxic, Will-O-Wisp, Thunder Wave).
        Solo si el oponente no tiene ya un status malo.
        """
        if opponent is None:
            return None

        # No aplicar status si el oponente ya tiene uno
        if opponent.status is not None:
            # Permitir stacks de Toxic si no es ya badly poisoned
            if opponent.status != Status.TOX:
                return None

        best_move = None
        best_score = 0.0

        for move in battle.available_moves:
            if move.category != MoveCategory.STATUS:
                continue

            score = 0.0

            # Status-inflicting moves
            if move.status is not None:
                if move.status == Status.TOX:
                    # Toxic es excelente contra Pokémon con HP alto / defensivos
                    score = 4.0 + (opponent.current_hp_fraction * 2.0)
                    # Inefectivo contra tipos Poison/Steel (no afecta a Steel en Gen 9)
                    if (
                        PokemonType.POISON in opponent.types
                        or PokemonType.STEEL in opponent.types
                    ):
                        score = 0.0
                elif move.status == Status.BRN:
                    # Burn es bueno contra physical attackers
                    score = 3.0
                    if opponent.boosts.get("atk", 0) >= 1:
                        score += 2.0
                    # Inefectivo contra Fire types
                    if PokemonType.FIRE in opponent.types:
                        score = 0.0
                elif move.status == Status.PAR:
                    # Paralyze es bueno contra Pokémon rápidos
                    score = 3.0
                    if PokemonType.ELECTRIC in opponent.types:
                        score = 0.0
                    if PokemonType.GROUND in opponent.types:
                        score = 0.0
                else:
                    score = 2.0

            # Volatile status (e.g., Thunder Wave via volatile_status)
            elif move.volatile_status is not None:
                score = 2.5

            # Moves que bajan stats del oponente
            elif move.boosts is not None:
                for stat, stages in move.boosts.items():
                    if stat in ("atk", "spa"):
                        score += abs(stages) * 1.5
                    elif stat == "spe":
                        score += abs(stages) * 2.0
                    elif stat in ("def", "spd"):
                        score += abs(stages) * 1.0
                    else:
                        score += abs(stages) * 0.5

            # Solo usar status si score es razonable
            if score > best_score and score >= 2.0:
                best_score = score
                best_move = move

        return best_move

    def _best_damage_move(self, battle, active, opponent) -> Optional["Move"]:
        """
        Elige el ataque con el mejor score de daño estimado.
        Considera priority moves para KOear Pokémon debilitados.
        """
        if not battle.available_moves:
            return None

        best_move = None
        best_score = -1.0

        # Si el oponente tiene poco HP, priorizar movimientos de prioridad
        use_priority = False
        if opponent and opponent.current_hp_fraction <= self.KO_PRIORITY_HP:
            use_priority = True

        for move in battle.available_moves:
            if move.category == MoveCategory.STATUS:
                continue

            score = estimate_damage_score(
                move, active, opponent, battle.weather, battle.fields
            )

            # Si oponente débil y es priority move, dar bonus enorme
            if use_priority and safe_priority(move) > 0:
                score *= 2.5

            # Small random factor to avoid predictability (simula "mix up")
            score *= 0.95 + random.random() * 0.10

            if score > best_score:
                best_score = score
                best_move = move

        return best_move
