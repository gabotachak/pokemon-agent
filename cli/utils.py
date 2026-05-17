"""
utils.py — Funciones compartidas para scripts de ejemplos.
"""

import importlib.util
import inspect
from pathlib import Path
from poke_env import Player, RandomPlayer

# ── Configuración ──────────────────────────────────────────────
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
BASE_CLASSES = (Player, RandomPlayer)

# Excluidos por defecto (scripts de infraestructura, no agentes)
DEFAULT_EXCLUDE = frozenset(
    {
        "cross_evaluate.py",
        "run_agent.py",
        "accept_battles_local.py",
        "utils.py",
    }
)


def print_title(title):
    print(f"\n{'═' * 50}")
    print(f"  {title}")
    print(f"{'═' * 50}")


def discover_agents(exclude: set[str] | None = None) -> dict[str, type]:
    """Escanea examples/ y devuelve {nombre_clase: clase}.

    Args:
        exclude: nombres de archivo a ignorar. Si None, usa los defaults.
    """
    agents: dict[str, type] = {"RandomPlayer": RandomPlayer}
    skip = exclude if exclude is not None else DEFAULT_EXCLUDE

    for py_file in EXAMPLES_DIR.glob("*.py"):
        if py_file.name.startswith("_") or py_file.name in skip:
            continue

        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        if spec is None or spec.loader is None:
            continue

        try:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"  ⚠️  No se pudo cargar {py_file.name}: {e}")
            continue

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BASE_CLASSES) and obj not in BASE_CLASSES:
                agents[name] = obj

    return agents


def print_agents(agents: dict[str, type], bordered: bool = False) -> None:
    """Imprime la lista de agentes disponibles con índice."""
    if bordered:
        print(f"\n  {'─' * 50}")
        print(f"  Agentes disponibles:")
    else:
        print(f"\n  Agentes disponibles:")

    for i, (name, cls) in enumerate(agents.items()):
        module = inspect.getmodule(cls)
        src = module.__name__.replace("examples.", "") if module else "poke_env"
        print(f"    [{i}] {name:25s} ({src})")

    if bordered:
        print(f"  {'─' * 50}")
    else:
        print()


def ask_agents(agents: dict[str, type]) -> list[type]:
    """Pide al usuario qué agentes incluir (índices separados por coma)."""
    print_agents(agents, bordered=True)

    try:
        val = input("  Agentes a evaluar: ").strip()
    except EOFError:
        val = "0"

    if not val:
        return [RandomPlayer]

    indices = []
    for part in val.split(","):
        part = part.strip()
        if part.isdigit():
            indices.append(int(part))

    names = list(agents.keys())
    selected = []
    for idx in indices:
        if 0 <= idx < len(names):
            selected.append(agents[names[idx]])

    if not selected:
        print("  Ningún agente válido, uso RandomPlayer.")
        return [RandomPlayer]

    return selected


def ask_agent(agents: dict[str, type]) -> type:
    print_agents(agents, bordered=True)
    try:
        idx = int(input(f"  Elegí agente [0]: ").strip() or "0")
    except (ValueError, EOFError):
        idx = 0

    return idx


def ask_int(prompt: str, default: int) -> int:
    """Pide un entero al usuario, usa default si vacío o inválido."""
    try:
        val = input(f"  {prompt} [{default}]: ").strip()
        return int(val) if val else default
    except (ValueError, EOFError):
        return default


def ask_yes_no(prompt: str, default: str = "y") -> bool:
    default = default.lower()
    if default not in ("y", "n"):
        raise ValueError("default debe ser 'y' o 'n'")

    suffix = "(Y/n)" if default == "y" else "(y/N)"
    while True:
        answer = input(f"{prompt} {suffix} ").strip().lower()
        if answer == "":
            return default == "y"
        if answer in ("y", "yes", "s", "si"):
            return True
        if answer in ("n", "no"):
            return False

        print("Por favor responda con 'y' o 'n'.")


def make_battle_logger(target):
    original_choose_move = target.choose_move
    original_battle_finished = target._battle_finished_callback

    def logged_choose_move(*args, **kwargs):
        if len(args) == 2:
            self_obj, battle = args
        else:
            battle = args[0]
            self_obj = target
        if not hasattr(self_obj, "_logger_battle_count"):
            self_obj._logger_battle_count = 0
            self_obj._logger_tracked_battles = set()
        if battle.battle_tag not in self_obj._logger_tracked_battles:
            self_obj._logger_battle_count += 1
            battle._local_battle_id = self_obj._logger_battle_count
            self_obj._logger_tracked_battles.add(battle.battle_tag)

            opponent = battle.opponent_username or "Desconocido"
            print(f"  #{battle._local_battle_id} Batalla iniciada contra {opponent} ⚔️")

        return original_choose_move(*args, **kwargs)

    def logged_battle_finished(*args, **kwargs):
        if len(args) == 2:
            self_obj, battle = args
        else:
            battle = args[0]
            self_obj = target

        if not hasattr(self_obj, "_logger_battle_count"):
            self_obj._logger_battle_count = 0
            self_obj._logger_tracked_battles = set()

        if battle.battle_tag not in self_obj._logger_tracked_battles:
            self_obj._logger_battle_count += 1
            battle._local_battle_id = self_obj._logger_battle_count
            self_obj._logger_tracked_battles.add(battle.battle_tag)

            opponent = battle.opponent_username or "Desconocido"
            print(
                f"  #{self_obj._logger_battle_count} Batalla iniciada contra {opponent} ⚔️"
            )

        b_id = getattr(
            battle, "_local_battle_id", getattr(self_obj, "_logger_battle_count", 0)
        )
        opponent = battle.opponent_username or "Desconocido"

        if battle.won:
            resultado = "¡Ganaste! 🏆"
        elif battle.lost:
            resultado = "¡Perdiste! 💀"
        else:
            resultado = "Empate / Abortada"

        print(f"  #{b_id} Batalla finalizada contra {opponent}: {resultado}")

        return original_battle_finished(*args, **kwargs)

    target.choose_move = logged_choose_move
    target._battle_finished_callback = logged_battle_finished

    return target
