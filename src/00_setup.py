import subprocess
import sys
import shutil
import re
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

ROOT = Path(__file__).parent.parent


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def run_silent(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"\n  ERROR: {' '.join(cmd)}\n{result.stderr}")
        sys.exit(1)
    return result


def run_streaming(cmd: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"\n  ERROR: {' '.join(cmd)}")
        sys.exit(1)


def check_node() -> None:
    if shutil.which("node") is None:
        print(
            "\n  ERROR: Node.js no encontrado.\n"
            "  Instalar desde https://nodejs.org (versión LTS recomendada)\n"
            "  y volver a correr este script."
        )
        sys.exit(1)
    version = run_silent(["node", "--version"]).stdout.strip()
    ok(f"Node.js {version}")


def check_uv() -> None:
    if shutil.which("uv") is None:
        print("\n  ERROR: uv no encontrado. Instalar desde https://docs.astral.sh/uv/")
        sys.exit(1)
    version = run_silent(["uv", "--version"]).stdout.strip()
    ok(version)


def setup_python_deps() -> None:
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        print("  Inicializando proyecto uv...")
        run_streaming(["uv", "init", "--no-readme"], cwd=ROOT)

    print("  Instalando dependencias Python (uv):\n")
    run_streaming(
        [
            "uv", "add",
            "poke-env",
            "pandas", "numpy",
            "scikit-learn", "xgboost",
            "fastapi", "uvicorn", "websockets",
            "huggingface_hub", "datasets", "pyarrow",
            "matplotlib", "seaborn", "requests",
            "python-dotenv", "tqdm",
        ],
        cwd=ROOT,
    )
    ok("Dependencias Python instaladas")


def setup_showdown() -> None:
    showdown_dir = ROOT / "showdown"

    if not showdown_dir.exists():
        print("  Clonando smogon/pokemon-showdown...\n")
        run_streaming(
            ["git", "clone", "https://github.com/smogon/pokemon-showdown.git", "showdown"],
            cwd=ROOT,
        )
        ok("Repositorio clonado")
    else:
        ok("showdown/ ya existe — saltando clone")

    print("\n  Instalando dependencias npm...\n")
    run_streaming(["npm", "install"], cwd=showdown_dir)
    ok("npm install completado")

    config_example = showdown_dir / "config" / "config-example.js"
    config = showdown_dir / "config" / "config.js"

    if not config.exists():
        shutil.copy(config_example, config)

    text = config.read_text()

    if "exports.workers" not in text:
        text += "\nexports.workers = 1;\n"
    else:
        text = re.sub(r"exports\.workers\s*=\s*\d+;", "exports.workers = 1;", text)

    if "exports.noguestsecurity" not in text:
        text += "exports.noguestsecurity = true;\n"
    else:
        text = re.sub(
            r"exports\.noguestsecurity\s*=\s*\w+;",
            "exports.noguestsecurity = true;",
            text,
        )

    config.write_text(text)
    ok("config.js parcheado (workers=1, noguestsecurity=true)")


def create_dirs() -> None:
    dirs = [
        ROOT / "outputs" / "figures",
        ROOT / "outputs" / "models",
        ROOT / "data" / "raw",
        ROOT / "data" / "processed",
        ROOT / "report",
    ]
    for d in tqdm(dirs, desc="  Creando carpetas", bar_format="{l_bar}{bar:20}{r_bar}", colour="green"):
        d.mkdir(parents=True, exist_ok=True)


def main() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║       Pokémon Showdown RL — Setup inicial        ║")
    print("╚══════════════════════════════════════════════════╝")

    section("1/4  Verificando dependencias del sistema")
    check_node()
    check_uv()

    section("2/4  Dependencias Python")
    setup_python_deps()

    section("3/4  Pokémon Showdown (Node.js)")
    setup_showdown()

    section("4/4  Estructura de carpetas")
    create_dirs()

    print(f"\n{'─' * 50}")
    print("  Setup completo. Para continuar:")
    print()
    print("    uv run python src/01_download.py")
    print()
    print("  Cuando tengas los datos, para entrenar el agente:")
    print("    Terminal A: cd showdown && node pokemon-showdown start --no-security")
    print("    Terminal B: uv run python src/06_dashboard.py")
    print("    Terminal C: uv run python src/05_train_agent.py")
    print()
    print("    http://localhost:8000  →  combates en vivo")
    print("    http://localhost:9000  →  dashboard de entrenamiento")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
