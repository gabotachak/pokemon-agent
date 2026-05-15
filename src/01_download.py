import requests
import pandas as pd
from pathlib import Path
from datasets import load_dataset

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"

REPLAYS_REPO = "HolidayOugi/pokemon-showdown-replays"
FORMAT_FILTER = "gen1randombattle"
STATS_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/pokemon_stats.csv"


def download_battles() -> None:
    dest = RAW / "gen1rb.parquet"
    if dest.exists():
        print(f"gen1rb.parquet ya existe ({dest.stat().st_size / 1_048_576:.1f} MB) — saltando.")
        return

    print(f"Descargando {FORMAT_FILTER} de {REPLAYS_REPO} (streaming — no baja los 66 GB completos)...")
    ds = load_dataset(REPLAYS_REPO, split="train", streaming=True)
    filtered = ds.filter(lambda row: row["formatid"] == FORMAT_FILTER)

    rows = []
    for i, row in enumerate(filtered):
        rows.append(row)
        if (i + 1) % 5_000 == 0:
            print(f"  {i + 1:,} batallas leídas...")

    df = pd.DataFrame(rows)
    df.to_parquet(dest, index=False)

    size_mb = dest.stat().st_size / 1_048_576
    print(f"\nGuardado → {dest}")
    print(f"  {len(df):,} batallas  |  {size_mb:.1f} MB")
    print(f"  Columnas: {list(df.columns)}")
    print(df[["id", "players", "rating", "uploadtime"]].head(3).to_string(index=False))


def download_stats() -> None:
    dest = RAW / "pokemon_stats.csv"
    if dest.exists():
        print(f"pokemon_stats.csv ya existe — saltando.")
        return

    print(f"Descargando pokemon_stats.csv...")
    response = requests.get(STATS_URL, timeout=30)
    response.raise_for_status()
    dest.write_bytes(response.content)

    df = pd.read_csv(dest)
    size_kb = dest.stat().st_size / 1024
    print(f"  {len(df):,} filas  |  {size_kb:.1f} KB")
    print(f"  Columnas: {list(df.columns)}")
    # stat_id: 1=HP 2=Atk 3=Def 4=SpAtk 5=SpDef 6=Speed
    print(df.head(3).to_string(index=False))


def main() -> None:
    print("=== Descarga de datos ===\n")
    RAW.mkdir(parents=True, exist_ok=True)

    download_battles()
    print()
    download_stats()

    print("\nDescarga completa. Siguiente paso:")
    print("  uv run python src/02_preprocess.py")


if __name__ == "__main__":
    main()
