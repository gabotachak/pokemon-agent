from poke_env.player import Player, BattleOrder
from poke_env.battle import Battle
from agents.pokemon_calculator import PokemonCalculator
import random


class AgentUngaBunga(Player):
    def __init__(self, *args, **kwargs):
        self.c = PokemonCalculator()
        super().__init__(*args, **kwargs)

    def choose_move(self, battle: Battle) -> BattleOrder:
        if battle.finished:
            return self.choose_random_move(battle)
        if not battle.available_moves and not battle.available_switches:
            return self.choose_random_move(battle)

        opponent = battle.opponent_active_pokemon
        if not opponent:
            if battle.available_moves:
                return self.create_order(random.choice(battle.available_moves))
            return self.choose_random_move(battle)

        best_move = None
        max_damage = -1

        if battle.available_moves:
            for move in battle.available_moves:
                damage = self.c.get_damage_percent(
                    move, battle.active_pokemon, opponent
                )
                if damage > max_damage:
                    max_damage = damage
                    best_move = move

        best_switch = None
        best_switch_damage = -1

        if battle.available_switches:
            for pokemon in battle.available_switches:
                for move in pokemon.moves.values():
                    damage = self.c.get_damage_percent(move, pokemon, opponent)
                    if damage > best_switch_damage:
                        best_switch_damage = damage
                        best_switch = pokemon

        if battle.available_switches and best_switch:
            if max_damage < 15 and (best_switch_damage > max_damage * 1.5):
                return self.create_order(best_switch)

        if best_move:
            return self.create_order(best_move)

        if battle.available_switches:
            return self.create_order(random.choice(battle.available_switches))

        return self.choose_random_move(battle)
