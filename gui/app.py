"""
app.py — PyWebView Api Bridge class.

Exposes 5 JS-callable methods that orchestrate battles via existing
cli/ async functions. Each battle operation runs in a daemon thread
with its own event loop to keep the UI responsive.
"""

import asyncio
import json
import os
import threading

CONFIG_DIR = os.path.expanduser("~/.config/pokemon-agent")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


class Api:
    def __init__(self):
        self._creds = None
        self._user = None
        self._password = None
        # Buffers for polling-based log/progress/result streaming.
        # Worker threads write here; JS polls via bridge methods.
        self._log_buffer: list[str] = []
        self._progress_buffer: dict = {"pct": 0, "status": ""}
        self._result_buffer: dict | None = None
        # Cargar config existente al inicio
        self._load_config()

    def save_config(self, user, password):
        if not user or not password:
            return False
        self._creds = {"user": user, "password": password}
        self._user = user
        self._password = password
        self._save_config_to_file(user, password)  # persistir a disco
        return True

    def _load_config(self):
        """Cargar credenciales desde el archivo de configuración si existe."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                user = data.get("user", "")
                password = data.get("password", "")
                if user and password:
                    self._user = user
                    self._password = password
                    self._creds = {"user": user, "password": password}
        except Exception:
            pass  # Si el archivo está corrupto, ignorar silenciosamente

    def _save_config_to_file(self, user, password):
        """Persistir credenciales al archivo de configuración."""
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(CONFIG_FILE, "w") as f:
                json.dump({"user": user, "password": password}, f)
        except Exception:
            pass  # Si no se puede escribir, no es crítico

    def has_config(self):
        """Devuelve True si hay credenciales guardadas (en memoria = archivo cargado)."""
        return self._user is not None and self._password is not None

    def get_config(self):
        """Devuelve las credenciales o None si no hay configuración."""
        if self._creds:
            return {"user": self._user, "password": self._password}
        return None

    def discover_agents(self):
        from cli.utils import discover_agents

        agents = discover_agents()
        return [{"name": name, "class_name": name} for name in agents]

    def search_battles(self, params):
        threading.Thread(
            target=self._run_search, args=(params,), daemon=True
        ).start()
        return {"status": "started"}

    def accept_battles(self, params):
        threading.Thread(
            target=self._run_accept, args=(params,), daemon=True
        ).start()
        return {"status": "started"}

    def cross_evaluate(self, params):
        threading.Thread(
            target=self._run_cross, args=(params,), daemon=True
        ).start()
        return {"status": "started"}

    # ── Buffer-based streaming (worker → buffer → JS polls) ────
    # PyWebView evaluate_js() only works from the main GUI thread.
    # Instead of pushing JS from daemon threads, we buffer data
    # and let JS poll via bridge methods.

    def _push_log(self, msg):
        self._log_buffer.append(msg)

    def _update_progress(self, pct, status):
        self._progress_buffer = {"pct": pct, "status": status}

    def _show_results(self, mode, data):
        self._result_buffer = {"mode": mode, "data": data}

    # ── JS-bridge polling methods ───────────────────────────────

    def poll_logs(self):
        """Return all buffered log messages and clear the buffer."""
        logs = list(self._log_buffer)
        self._log_buffer.clear()
        return logs

    def poll_progress(self):
        """Return the latest progress snapshot and reset."""
        p = dict(self._progress_buffer)
        self._progress_buffer = {"pct": 0, "status": ""}
        return p

    def poll_result(self):
        """Return results once, then None until the next _show_results call."""
        r = self._result_buffer
        self._result_buffer = None
        return r

    # ── Battle workers ───────────────────────────────────────────

    def _run_search(self, params):
        import cli.utils
        from cli.search_battles import search_battles

        agents = cli.utils.discover_agents()
        agent_cls = agents.get(params["agent"])
        if agent_cls is None:
            self._push_log(
                f"Error: agente '{params['agent']}' no encontrado"
            )
            self._update_progress(0, "Error")
            return

        from poke_env import (
            ShowdownServerConfiguration,
            LocalhostServerConfiguration,
            AccountConfiguration,
        )

        server = params.get("server", "localhost")
        use_official = server != "localhost"
        server_config = (
            ShowdownServerConfiguration
            if use_official
            else LocalhostServerConfiguration
        )
        account = AccountConfiguration(
            username=getattr(self, "_user", "BotAvocado"),
            password=getattr(self, "_password", "BotAvocado123"),
        )

        n_games = max(1, int(params.get("n_games", 5)))

        # NO usar make_battle_logger — queremos logs en la UI, no en terminal
        player = agent_cls(
            account_configuration=account,
            server_configuration=server_config,
            max_concurrent_battles=n_games,
        )

        # Interceptar choose_move para detectar inicio y _battle_finished para fin
        original_choose_move = player.choose_move
        original_finished = player._battle_finished_callback
        n_done = [0]
        tracked = set()
        n_finished = [0]  # contador separado para batallas finalizadas

        def on_choose_move(battle):
            if battle.battle_tag not in tracked:
                n_done[0] += 1
                tracked.add(battle.battle_tag)
                opp = battle.opponent_username or "Desconocido"
                self._push_log(
                    f"#{n_done[0]} Batalla iniciada contra {opp} ⚔️"
                )
            return original_choose_move(battle)

        def on_battle_finished(battle):
            n_finished[0] += 1
            result = "Victoria 🏆" if battle.won else "Derrota 💀"
            opp = battle.opponent_username or "Desconocido"
            self._push_log(f"#{n_finished[0]} vs {opp}: {result}")
            pct = int(n_finished[0] / n_games * 100)
            self._update_progress(pct, f"Batalla {n_finished[0]}/{n_games}")
            return original_finished(battle)

        player.choose_move = lambda *args, **kw: on_choose_move(args[-1])
        player._battle_finished_callback = lambda *args, **kw: on_battle_finished(
            args[-1]
        )

        self._push_log(
            f"Iniciando {n_games} batallas en {'Showdown' if use_official else 'Localhost'}..."
        )
        self._update_progress(0, "Buscando oponentes...")

        async def run():
            await search_battles(
                player,
                n_games,
                on_log=self._push_log,
                on_progress=self._update_progress,
            )

        asyncio.run(run())
        if player.n_finished_battles > 0:
            self._show_results(
                "standard",
                {
                    "wins": player.n_won_battles,
                    "losses": player.n_lost_battles,
                    "wr": round(player.win_rate * 100, 1),
                },
            )

    def _run_accept(self, params):
        import cli.utils
        from cli.accept_battles import accept_battles

        agents = cli.utils.discover_agents()
        agent_cls = agents.get(params["agent"])
        if agent_cls is None:
            self._push_log(
                f"Error: agente '{params['agent']}' no encontrado"
            )
            self._update_progress(0, "Error")
            return

        from poke_env import (
            ShowdownServerConfiguration,
            LocalhostServerConfiguration,
            AccountConfiguration,
        )

        server = params.get("server", "localhost")
        use_official = server != "localhost"
        server_config = (
            ShowdownServerConfiguration
            if use_official
            else LocalhostServerConfiguration
        )
        account = AccountConfiguration(
            username=getattr(self, "_user", "BotAvocado"),
            password=getattr(self, "_password", "BotAvocado123"),
        )

        n_games = max(1, int(params.get("n_games", 5)))

        # NO usar make_battle_logger — queremos logs en la UI, no en terminal
        player = agent_cls(
            account_configuration=account,
            server_configuration=server_config,
            max_concurrent_battles=n_games,
        )

        # Interceptar choose_move para detectar inicio y _battle_finished para fin
        original_choose_move = player.choose_move
        original_finished = player._battle_finished_callback
        n_done = [0]
        tracked = set()
        n_finished = [0]  # contador separado para batallas finalizadas

        def on_choose_move(battle):
            if battle.battle_tag not in tracked:
                n_done[0] += 1
                tracked.add(battle.battle_tag)
                opp = battle.opponent_username or "Desconocido"
                self._push_log(
                    f"#{n_done[0]} Batalla iniciada contra {opp} ⚔️"
                )
            return original_choose_move(battle)

        def on_battle_finished(battle):
            n_finished[0] += 1
            result = "Victoria 🏆" if battle.won else "Derrota 💀"
            opp = battle.opponent_username or "Desconocido"
            self._push_log(f"#{n_finished[0]} vs {opp}: {result}")
            pct = int(n_finished[0] / n_games * 100)
            self._update_progress(pct, f"Batalla {n_finished[0]}/{n_games}")
            return original_finished(battle)

        player.choose_move = lambda *args, **kw: on_choose_move(args[-1])
        player._battle_finished_callback = lambda *args, **kw: on_battle_finished(
            args[-1]
        )

        self._push_log("Esperando desafíos entrantes...")
        self._update_progress(0, "Esperando desafíos...")

        async def run():
            await accept_battles(
                player,
                n_games,
                on_log=self._push_log,
                on_progress=self._update_progress,
            )

        asyncio.run(run())
        if player.n_finished_battles > 0:
            self._show_results(
                "standard",
                {
                    "wins": player.n_won_battles,
                    "losses": player.n_lost_battles,
                    "wr": round(player.win_rate * 100, 1),
                },
            )

    def _run_cross(self, params):
        import cli.utils
        from cli.cross_evaluate import cross_evaluate_manual

        agent_names = params.get("agents", [])
        if len(agent_names) < 2:
            self._push_log("Error: se requieren al menos 2 agentes")
            return

        agents = cli.utils.discover_agents()
        selected_cls = []
        for name in agent_names:
            cls = agents.get(name)
            if cls:
                selected_cls.append(cls)
            else:
                self._push_log(
                    f"Advertencia: agente '{name}' no encontrado, ignorado"
                )

        if len(selected_cls) < 2:
            self._push_log("Error: menos de 2 agentes válidos")
            return

        n_battles = max(1, int(params.get("n_battles", 10)))

        players = []
        for i, agent_cls in enumerate(selected_cls):
            username = f"{agent_cls.__name__} {i + 1}"
            try:
                player = agent_cls(
                    username=username,
                    max_concurrent_battles=1,
                )
            except TypeError:
                player = agent_cls(max_concurrent_battles=0)
                if hasattr(player, "_username"):
                    player._username = username
            players.append(player)

        async def run():
            results = await cross_evaluate_manual(
                players,
                n_challenges=n_battles,
                on_log=self._push_log,
                on_progress=self._update_progress,
            )
            table = []
            for i, p in enumerate(players):
                name = p.username
                matchups = results.get(name, {})
                total_wr = (
                    sum(matchups.values()) / len(matchups) if matchups else 0
                )
                points = int(total_wr * 100)
                table.append(
                    {
                        "pos": i + 1,
                        "name": name,
                        "pts": points,
                        "wr": round(total_wr * 100, 1),
                    }
                )
            table.sort(key=lambda r: r["pts"], reverse=True)
            for i, row in enumerate(table):
                row["pos"] = i + 1
            self._show_results("cross", table)

        asyncio.run(run())
