from poke_env.player import Player


class AgentChatGPT(Player):
    def choose_move(self, battle):
        if not battle.available_moves:
            return self.choose_random_move(battle)

        active = battle.active_pokemon
        opponent = battle.opponent_active_pokemon

        def safe_priority(move):
            try:
                return move.priority
            except Exception:
                return 0

        def safe_accuracy(move):
            try:
                return move.accuracy or 100
            except Exception:
                return 100

        def safe_base_power(move):
            try:
                return move.base_power or 0
            except Exception:
                return 0

        def move_score(move):
            score = 0

            # Base power
            base_power = safe_base_power(move)
            score += base_power

            # STAB
            if move.type and (move.type == active.type_1 or move.type == active.type_2):
                score *= 1.5

            # Type effectiveness
            if opponent and move.type:
                try:
                    multiplier = opponent.damage_multiplier(move.type)
                    score *= multiplier

                    if multiplier == 0:
                        score -= 1000
                except Exception:
                    pass

            # Accuracy
            score *= safe_accuracy(move) / 100

            # Priority
            score += safe_priority(move) * 15

            # Boosts
            try:
                if move.boosts:
                    score += sum(move.boosts.values()) * 20
            except Exception:
                pass

            return score

        best_move = max(battle.available_moves, key=move_score)

        should_tera = False

        if battle.can_tera and opponent:
            try:
                if opponent.damage_multiplier(best_move.type) >= 2:
                    should_tera = True
            except Exception:
                pass

        return self.create_order(best_move, terastallize=should_tera)
