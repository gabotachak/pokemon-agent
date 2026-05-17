from poke_env.player import Player


class AgentGemini(Player):
    def choose_move(self, battle):
        # 1. Si no hay movimientos disponibles, cambia al mejor Pokémon disponible
        if not battle.available_moves:
            if battle.available_switches:
                return self.create_order(self._get_best_switch(battle))
            return self.choose_random_move(battle)

        active = battle.active_pokemon
        opponent = battle.opponent_active_pokemon

        # 2. Evaluar si debemos cambiar de Pokémon (Switching)
        best_switch = self._get_best_switch(battle)
        if best_switch and self._should_switch(active, opponent):
            return self.create_order(best_switch)

        # 3. Evaluar los movimientos disponibles
        best_move = max(
            battle.available_moves,
            key=lambda m: self._evaluate_move(m, active, opponent, battle),
        )

        # 4. Lógica de Teracristalización (Mejorada)
        should_tera = False
        if battle.can_tera and opponent:
            # Tera ofensivo: Si el mejor movimiento es del mismo tipo que nuestro teratipo y es potente
            if best_move.type == active.tera_type and best_move.base_power >= 80:
                should_tera = True
            # Tera defensivo: Si el oponente tiene ventaja de tipo sobre nosotros (ej. debilidad x2 o x4)
            elif active.damage_multiplier(opponent.type_1) >= 2 or (
                opponent.type_2 and active.damage_multiplier(opponent.type_2) >= 2
            ):
                should_tera = True

        return self.create_order(best_move, terastallize=should_tera)

    def _evaluate_move(self, move, active, opponent, battle):
        score = 0

        # --- A. MOVIMIENTOS OFENSIVOS ---
        if move.base_power > 0:
            score += move.base_power

            # STAB
            if move.type in [active.type_1, active.type_2]:
                score *= 1.5

            # Efectividad de tipos
            if opponent and move.type:
                multiplier = opponent.damage_multiplier(move.type)
                score *= multiplier
                if multiplier == 0:
                    return -1000  # Evitar inmunidades a toda costa

            # Precisión y Prioridad
            accuracy = move.accuracy or 100
            score *= accuracy / 100
            priority = move.priority or 0
            score += priority * 25

        # --- B. MOVIMIENTOS DE ESTADO Y SOPORTE ---
        else:
            hp_fraction = active.current_hp_fraction

            # Curación (ej. Recuperación, Respiro)
            if move.heal:
                if hp_fraction < 0.5:
                    score += (
                        150  # Muy prioritario si estamos a menos de la mitad de vida
                    )
                elif hp_fraction == 1.0:
                    score -= 100  # Inútil si estamos con la salud al máximo

            # Problemas de estado (ej. Fuego Fatuo, Tóxico)
            elif move.status and opponent:
                if opponent.status is None:
                    score += 100
                else:
                    score -= 200  # No intentar quemar a algo que ya está quemado

            # Boosts de estadísticas (ej. Danza Espada)
            elif move.boosts:
                if hp_fraction > 0.7:  # Solo boostearse si tenemos buena salud
                    score += sum(move.boosts.values()) * 30
                else:
                    score -= 50

            # Trampas (ej. Trampa Rocas, Púas)
            elif move.id in ["stealthrock", "spikes", "toxicspikes", "stickyweb"]:
                # Si la condición no está en el lado del oponente, la priorizamos
                if move.id not in battle.opponent_side_conditions:
                    score += 120
                else:
                    score -= 100

        return score

    def _should_switch(self, active, opponent):
        if not opponent:
            return False

        # Si nuestra vida es muy baja y somos débiles a los tipos del oponente, huimos.
        for opp_type in filter(None, [opponent.type_1, opponent.type_2]):
            if active.damage_multiplier(opp_type) >= 2.0:
                return True

        return False

    def _get_best_switch(self, battle):
        if not battle.available_switches:
            return None

        opponent = battle.opponent_active_pokemon
        if not opponent:
            return battle.available_switches[0]

        best_switch = None
        best_score = -float("inf")

        for pokemon in battle.available_switches:
            score = 0

            # Evaluamos la resistencia defensiva del Pokémon en el banquillo
            for opp_type in filter(None, [opponent.type_1, opponent.type_2]):
                multiplier = pokemon.damage_multiplier(opp_type)
                # Castigamos si es débil, premiamos si resiste o es inmune
                if multiplier >= 2:
                    score -= 50
                elif multiplier < 1:
                    score += 50

            # Evaluamos si tiene movimientos eficaces contra el rival
            for move in pokemon.moves.values():
                if move.base_power > 0 and move.type:
                    score += opponent.damage_multiplier(move.type) * 15

            if score > best_score:
                best_score = score
                best_switch = pokemon

        return best_switch
