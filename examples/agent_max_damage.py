from poke_env.player import Player


class AgentMaxDamage(Player):
    def choose_move(self, battle):
        if not battle.available_moves:
            return self.choose_random_move(battle)

        best_move = max(
            battle.available_moves,
            key=lambda move: (
                (move.base_power or 0)
                * (1.5 if move.type == battle.active_pokemon.type_1 else 1.0)
            ),
        )

        return self.create_order(best_move)
