"""
search_battles.py — Buscar oponentes en el ladder automáticamente.

Permite elegir un agente, seleccionar servidor (local u oficial),
y buscar ``N`` partidas contra oponentes aleatorios del ladder.
A diferencia de ``accept_battles``, este script inicia la búsqueda
en lugar de esperar challenges entrantes.

Uso:
    # Terminal A — servidor Showdown (si usas localhost)
    cd showdown && node pokemon-showdown start --no-security

    # Terminal B — este script
    python -m cli.search_battles
"""

import asyncio
import json
from poke_env import (
    LocalhostServerConfiguration,
    ShowdownServerConfiguration,
    AccountConfiguration,
)
from cli.utils import (
    ask_int,
    ask_yes_no,
    discover_agents,
    print_title,
    ask_agent,
    make_battle_logger,
)


async def search_battles(
    player,
    n_games,
    on_log=print,
    on_progress=lambda pct, status: print(f"{pct}% {status}"),
    on_result=lambda d: print(json.dumps(d, indent=2)),
):
    await player.ladder(n_games)

    if player.n_finished_battles > 0:
        wr = player.win_rate
        on_log(f"\n  {'─' * 40}")
        on_log(
            f"  Final: {player.n_won_battles}W / {player.n_lost_battles}L  ({wr:.1%})"
        )
        on_log(f"  {'─' * 40}")
        on_progress(100, "Completado")
        on_result({
            "wins": player.n_won_battles,
            "losses": player.n_lost_battles,
            "wr": round(wr * 100, 1),
        })


async def main():
    print_title("🔍 Search Battles")

    # Server selection
    use_official = ask_yes_no("  ¿Usar servidor oficial?", "n")
    server_config = (
        ShowdownServerConfiguration if use_official else LocalhostServerConfiguration
    )

    account = AccountConfiguration(
        username="BotAvocado",
        password="BotAvocado123",
    )

    # Agent selection
    agents = discover_agents()
    idx = ask_agent(agents)

    names = list(agents.keys())
    agent_cls = names[idx]
    agent_type = agents[agent_cls]

    # Battle logger
    agent_type = make_battle_logger(agent_type)

    # Configuration
    n_games = ask_int("¿Cuántas batallas?", 10)
    n_games = max(1, n_games)

    # Loop
    player = agent_type(
        account_configuration=account,
        server_configuration=server_config,
        max_concurrent_battles=n_games,
    )

    print(f"\n  {'─' * 40}")
    print(f"  Servidor: {'Showdown' if use_official else 'Localhost'}")
    print(f"  Nombre del Agente: {player.username} ({agent_cls})")
    print(f"  Batallas a buscar: {n_games}")
    print(f"  {'─' * 40}")

    await search_battles(player, n_games)


if __name__ == "__main__":
    asyncio.run(main())
