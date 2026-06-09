import random
from poke_env.battle import Pokemon, Move

TYPE_CHART = {
    "NORMAL": {"ROCK": 0.5, "STEEL": 0.5, "GHOST": 0},
    "FIRE": {
        "FIRE": 0.5,
        "WATER": 0.5,
        "GRASS": 2,
        "ICE": 2,
        "BUG": 2,
        "ROCK": 0.5,
        "DRAGON": 0.5,
    },
    "WATER": {
        "FIRE": 2,
        "WATER": 0.5,
        "GRASS": 0.5,
        "GROUND": 2,
        "ROCK": 2,
        "DRAGON": 0.5,
    },
    "ELECTRIC": {
        "WATER": 2,
        "ELECTRIC": 0.5,
        "GRASS": 0.5,
        "GROUND": 0,
        "FLYING": 2,
        "DRAGON": 0.5,
    },
    "GRASS": {
        "WATER": 2,
        "FIRE": 0.5,
        "GRASS": 0.5,
        "POISON": 0.5,
        "GROUND": 2,
        "FLYING": 0.5,
        "BUG": 0.5,
        "ROCK": 2,
        "DRAGON": 0.5,
        "STEEL": 0.5,
    },
    "ICE": {
        "GRASS": 2,
        "GROUND": 2,
        "FLYING": 2,
        "DRAGON": 2,
        "FIRE": 0.5,
        "WATER": 0.5,
        "ICE": 0.5,
        "STEEL": 0.5,
    },
    "FIGHTING": {
        "NORMAL": 2,
        "ICE": 2,
        "ROCK": 2,
        "DARK": 2,
        "STEEL": 2,
        "POISON": 0.5,
        "FLYING": 0.5,
        "PSYCHIC": 0.5,
        "BUG": 0.5,
        "FAIRY": 0.5,
        "GHOST": 0,
    },
    "POISON": {
        "GRASS": 2,
        "FAIRY": 2,
        "POISON": 0.5,
        "GROUND": 0.5,
        "ROCK": 0.5,
        "GHOST": 0.5,
        "STEEL": 0,
    },
    "GROUND": {
        "FIRE": 2,
        "ELECTRIC": 2,
        "POISON": 2,
        "ROCK": 2,
        "STEEL": 2,
        "GRASS": 0.5,
        "BUG": 0.5,
        "FLYING": 0,
    },
    "FLYING": {
        "GRASS": 2,
        "FIGHTING": 2,
        "BUG": 2,
        "ELECTRIC": 0.5,
        "ROCK": 0.5,
        "STEEL": 0.5,
    },
    "PSYCHIC": {"FIGHTING": 2, "POISON": 2, "PSYCHIC": 0.5, "STEEL": 0.5, "DARK": 0},
    "BUG": {
        "GRASS": 2,
        "PSYCHIC": 2,
        "DARK": 2,
        "FIRE": 0.5,
        "FIGHTING": 0.5,
        "POISON": 0.5,
        "FLYING": 0.5,
        "GHOST": 0.5,
        "STEEL": 0.5,
        "FAIRY": 0.5,
    },
    "ROCK": {
        "FIRE": 2,
        "ICE": 2,
        "FLYING": 2,
        "BUG": 2,
        "FIGHTING": 0.5,
        "GROUND": 0.5,
        "STEEL": 0.5,
    },
    "GHOST": {"PSYCHIC": 2, "GHOST": 2, "DARK": 0.5, "NORMAL": 0},
    "DRAGON": {"DRAGON": 2, "STEEL": 0.5, "FAIRY": 0},
    "DARK": {"PSYCHIC": 2, "GHOST": 2, "FIGHTING": 0.5, "DARK": 0.5, "FAIRY": 0.5},
    "STEEL": {
        "ICE": 2,
        "ROCK": 2,
        "FAIRY": 2,
        "FIRE": 0.5,
        "WATER": 0.5,
        "ELECTRIC": 0.5,
        "STEEL": 0.5,
    },
    "FAIRY": {
        "DRAGON": 2,
        "FIGHTING": 2,
        "DARK": 2,
        "FIRE": 0.5,
        "POISON": 0.5,
        "STEEL": 0.5,
    },
}


class PokemonCalculator:
    def __init__(self):
        pass

    def get_type_effectiveness(self, move_type, target_types):
        multiplier = 1

        for t in target_types:
            multiplier *= TYPE_CHART.get(move_type, {}).get(t, 1)

        return multiplier

    def get_stab(self, move_type, pokemon):
        return 1.5 if move_type in [t.name for t in pokemon.types] else 1

    def get_estimate_stat(self, pokemon, stat, level):
        base_stat = pokemon.base_stats[stat]
        if stat == "hp":
            return ((((2 * base_stat) + 31 + 20) * level) / 100) + level + 10
        else:
            return ((((2 * (base_stat)) + 31 + 20) * level) / 100) + 5

    def get_damage(self, move: Move, my_pokemon: Pokemon, opp_pokemon: Pokemon):
        if move.category.name == "STATUS" or not move.base_power:
            return 0
        N = my_pokemon.level
        A = (
            my_pokemon.stats["atk"]
            if move.category.name == "PHYSICAL"
            else my_pokemon.stats["spa"]
        )
        P = move.base_power
        D = (
            self.get_estimate_stat(opp_pokemon, "def", opp_pokemon.level)
            if move.category.name == "PHYSICAL"
            else self.get_estimate_stat(opp_pokemon, "spd", opp_pokemon.level)
        )
        B = self.get_stab(move.type.name, my_pokemon)
        E = self.get_type_effectiveness(
            move.type.name, [t.name for t in opp_pokemon.types]
        )
        V = random.uniform(0.85, 1)
        base_damage = (((2 * N / 5) + 2) * P * (A / D)) / 50 + 2
        modifier = B * E * V
        damage = int(base_damage * modifier)
        return damage

    def get_damage_percent(self, move: Move, my_pokemon: Pokemon, opp_pokemon: Pokemon):
        damage = self.get_damage(move, my_pokemon, opp_pokemon)
        hp = self.get_estimate_stat(opp_pokemon, "hp", opp_pokemon.level)
        damage = int((damage / hp) * 100)
        return damage
