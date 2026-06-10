"""
cross_evaluate.py — Evaluar agentes en round-robin local.

Permite seleccionar múltiples agentes y enfrentarlos entre sí en
partidas locales (servidor localhost). Cada par de agentes se enfrenta
``N`` veces y se calcula el win rate de cada uno contra el otro.

El resultado muestra el porcentaje de victorias de cada agente contra cada oponente.

Uso:
    # Terminal A — servidor Showdown
    cd showdown && node pokemon-showdown start --no-security

    # Terminal B — este script
    python -m cli.cross_evaluate
"""

import asyncio
import json
from cli.utils import ask_agents, ask_int, discover_agents, print_title


async def cross_evaluate_manual(
    players,
    n_challenges=10,
    on_log=print,
    on_progress=lambda pct, s: print(f"{pct}% {s}"),
    on_result=lambda d: print(json.dumps(d, indent=2)),
):
    results = {p.username: {} for p in players}
    total = (len(players) * (len(players) - 1)) // 2
    current = 0
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            p1 = players[i]
            p2 = players[j]
            current += 1

            p1.reset_battles()
            p2.reset_battles()
            label = f"{p1.username} vs {p2.username}"

            on_log(f"  [{current}/{total}] {label} ({n_challenges} battles)...")
            on_progress(int(current / total * 100), label)
            await p1.battle_against(
                p2,
                n_battles=n_challenges,
            )
            results[p1.username][p2.username] = p1.win_rate
            results[p2.username][p1.username] = p2.win_rate

    on_progress(100, "Completado")
    on_result(results)
    return results


def print_results(results: dict) -> None:
    print_title("Resultados")

    for agent, matchups in results.items():
        print(f"\n  {agent}")

        for opponent, winrate in matchups.items():
            percent = winrate * 100

            print(f"    ├─ vs {opponent:<25}" f"{percent:>6.1f}% WR")


async def main():
    print_title("🔬 Cross-Evaluate de Agentes")

    # Agent selection
    agents = discover_agents(exclude={"cross_evaluate.py"})
    selected = ask_agents(agents)

    # Configuration
    n_battles = ask_int("Batallas por matchup", 10)

    # Loop
    players = []
    for i, agent_cls in enumerate(selected):
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

    results = await cross_evaluate_manual(players, n_challenges=n_battles)
    print_results(results)


if __name__ == "__main__":
    asyncio.run(main())
