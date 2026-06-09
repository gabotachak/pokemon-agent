"""
utils.py — Funciones compartidas para los scripts de la carpeta cli/.

Provee utilidades de descubrimiento de agentes, interacción con el usuario
(índices, confirmaciones) y un battle logger genérico que intercepta
``choose_move`` y ``_battle_finished_callback`` para imprimir en consola
cuándo inicia y termina cada batalla.

Uso típico:
    from utils import discover_agents, ask_int, make_battle_logger
"""

import importlib.util
import inspect
from pathlib import Path
from poke_env import Player, RandomPlayer

# ── Configuración ──────────────────────────────────────────────
EXAMPLES_DIR = Path(__file__).parent.parent / "agents"
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


def print_title(title: str) -> None:
    """Imprime un banner centrado con bordes decorativos."""
    print(f"\n{'═' * 50}")
    print(f"  {title}")
    print(f"{'═' * 50}")


def discover_agents(exclude: set[str] | None = None) -> dict[str, type]:
    """Escanea ``examples/`` y devuelve ``{nombre_clase: clase}``.

    Busca clases que hereden de ``Player`` o ``RandomPlayer`` en cada
    archivo ``.py`` del directorio de ejemplos, excluyendo archivos
    de infraestructura.

    Args:
        exclude: nombres de archivo a ignorar. Si ``None``, usa los defaults.

    Returns:
        Diccionario mapeando nombre de clase a la clase misma.
        Siempre incluye ``RandomPlayer`` como opción base.
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
    """Imprime la lista de agentes disponibles con índice numérico.

    Args:
        agents: diccionario ``{nombre: clase}`` devuelto por ``discover_agents``.
        bordered: si ``True``, rodea la lista con líneas decorativas.
    """
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
    """Pide al usuario qué agentes incluir (índices separados por coma).

    Args:
        agents: diccionario ``{nombre: clase}`` devuelto por ``discover_agents``.

    Returns:
        Lista de clases seleccionadas. Si no se ingresa nada válido,
        retorna ``[RandomPlayer]``.
    """
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


def ask_agent(agents: dict[str, type]) -> int:
    """Pide al usuario que elija un solo agente.

    Args:
        agents: diccionario ``{nombre: clase}`` devuelto por ``discover_agents``.

    Returns:
        Índice numérico del agente seleccionado en la lista de claves.
    """
    print_agents(agents, bordered=True)
    try:
        idx = int(input(f"  Elegí agente [0]: ").strip() or "0")
    except (ValueError, EOFError):
        idx = 0

    return idx


def ask_int(prompt: str, default: int) -> int:
    """Pide un entero al usuario, usa ``default`` si vacío o inválido.

    Args:
        prompt: texto a mostrar antes del input.
        default: valor por defecto si el usuario no ingresa nada.

    Returns:
        El entero ingresado o el valor por defecto.
    """
    try:
        val = input(f"  {prompt} [{default}]: ").strip()
        return int(val) if val else default
    except (ValueError, EOFError):
        return default


def ask_yes_no(prompt: str, default: str = "y") -> bool:
    """Pide confirmación sí/no al usuario.

    Args:
        prompt: texto a mostrar.
        default: ``'y'`` o ``'n'`` para el valor por defecto.

    Returns:
        ``True`` si el usuario responde afirmativamente, ``False`` en caso contrario.

    Raises:
        ValueError: si ``default`` no es ``'y'`` o ``'n'``.
    """
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


def make_battle_logger(target: type) -> type:
    """Inyecta logging de inicio/fin de batalla en una clase de agente.

    Intercepta ``choose_move`` y ``_battle_finished_callback`` mediante
    monkey-patching para asignar un ID local a cada batalla y mostrar
    en consola cuándo inicia y termina, junto con el resultado.

    Args:
        target: la clase de agente (subclase de ``Player``) a modificar.

    Returns:
        La misma clase con los métodos interceptados.
    """
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
