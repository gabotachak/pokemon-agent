import subprocess
import sys
import shutil
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {' '.join(cmd)}\n{result.stderr}")
        sys.exit(1)
    return result


def check_node() -> None:
    if shutil.which("node") is None:
        print(
            "Node.js no encontrado.\n"
            "Instalar desde https://nodejs.org (versión LTS recomendada).\n"
            "Luego volver a correr este script."
        )
        sys.exit(1)
    version = subprocess.run(["node", "--version"], capture_output=True, text=True).stdout.strip()
    print(f"Node.js: {version}")


def setup_python_deps() -> None:
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        print("Inicializando proyecto uv...")
        run(["uv", "init", "--no-readme"], cwd=ROOT)

    print("Instalando dependencias Python...")
    run(
        [
            "uv", "add",
            "poke-env",
            "pandas", "numpy",
            "scikit-learn", "xgboost",
            "fastapi", "uvicorn", "websockets",
            "huggingface_hub", "datasets", "pyarrow",
            "matplotlib", "seaborn", "requests",
        ],
        cwd=ROOT,
    )
    print("Dependencias instaladas.")


def setup_showdown() -> None:
    showdown_dir = ROOT / "showdown"

    if not showdown_dir.exists():
        print("Clonando Pokémon Showdown...")
        run(
            ["git", "clone", "https://github.com/smogon/pokemon-showdown.git", "showdown"],
            cwd=ROOT,
        )

    print("Instalando dependencias npm...")
    run(["npm", "install"], cwd=showdown_dir)

    config_example = showdown_dir / "config" / "config-example.js"
    config = showdown_dir / "config" / "config.js"

    if not config.exists():
        shutil.copy(config_example, config)

    text = config.read_text()

    # Set workers = 1
    if "exports.workers" not in text:
        text += "\nexports.workers = 1;\n"
    else:
        text = re.sub(r"exports\.workers\s*=\s*\d+;", "exports.workers = 1;", text)

    # Enable noguestsecurity
    if "exports.noguestsecurity" not in text:
        text += "exports.noguestsecurity = true;\n"
    else:
        text = re.sub(
            r"exports\.noguestsecurity\s*=\s*\w+;",
            "exports.noguestsecurity = true;",
            text,
        )

    config.write_text(text)
    print("Showdown configurado.")


def create_dirs() -> None:
    dirs = [
        ROOT / "outputs" / "figures",
        ROOT / "outputs" / "models",
        ROOT / "data" / "raw",
        ROOT / "data" / "processed",
        ROOT / "report",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    print("Carpetas creadas.")


def main() -> None:
    print("=== Setup Pokémon Showdown RL ===\n")
    check_node()
    setup_python_deps()
    setup_showdown()
    create_dirs()

    print("""
Setup completo. Para continuar:

  1. Terminal A: cd showdown && node pokemon-showdown start --no-security
  2. Terminal B: uv run python src/06_dashboard.py
  3. Terminal C: uv run python src/05_train_agent.py

  Browser:
    http://localhost:8000  →  combates en vivo
    http://localhost:9000  →  dashboard de entrenamiento
""")


if __name__ == "__main__":
    main()
