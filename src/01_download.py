import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from huggingface_hub import hf_hub_download
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"

REPLAYS_REPO = "HolidayOugi/pokemon-showdown-replays"
GEN8_RB_FILES = [
    "[Gen 8] RANDOMBATTLE_part1.parquet",
    "[Gen 8] RANDOMBATTLE_part2.parquet",
    "[Gen 8] RANDOMBATTLE_part3.parquet",
]
STATS_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/pokemon_stats.csv"


def download_battles() -> None:
    dest = RAW / "gen8rb.parquet"
    if dest.exists():
        size_mb = dest.stat().st_size / 1_048_576
        print(f"  gen8rb.parquet ya existe ({size_mb:.1f} MB) — saltando.")
        return

    print(f"  Fuente : {REPLAYS_REPO}")
    print(f"  Archivos: {len(GEN8_RB_FILES)} partes de Gen 8 Random Battle\n")

    frames = []
    for filename in tqdm(GEN8_RB_FILES, desc="  Descargando partes", unit=" archivo", colour="cyan"):
        path = hf_hub_download(repo_id=REPLAYS_REPO, filename=filename, repo_type="dataset")
        frames.append(pd.read_parquet(path))
        tqdm.write(f"  ✓ {filename} ({frames[-1].shape[0]:,} batallas)")

    df = pd.concat(frames, ignore_index=True)
    df.to_parquet(dest, index=False)

    size_mb = dest.stat().st_size / 1_048_576
    print(f"\n  Guardado → {dest}")
    print(f"  {len(df):,} batallas  |  {size_mb:.1f} MB  |  {len(df.columns)} columnas")
    print(f"  Columnas: {list(df.columns)}")
    print()
    print(df[["id", "players", "rating", "uploadtime"]].head(3).to_string(index=False))


def download_stats() -> None:
    dest = RAW / "pokemon_stats.csv"
    if dest.exists():
        print(f"  pokemon_stats.csv ya existe — saltando.")
        return

    print(f"  Fuente: PokeAPI")

    response = requests.get(STATS_URL, stream=True, timeout=30)
    response.raise_for_status()

    total = int(response.headers.get("content-length", 0))
    with (
        open(dest, "wb") as f,
        tqdm(
            total=total,
            desc="  Descargando",
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            colour="yellow",
            bar_format="{l_bar}{bar:30}{r_bar}",
        ) as pbar,
    ):
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            pbar.update(len(chunk))

    df = pd.read_csv(dest)
    size_kb = dest.stat().st_size / 1024
    print(f"\n  {len(df):,} filas  |  {size_kb:.1f} KB")
    print(f"  Columnas: {list(df.columns)}")


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def main() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║         Pokémon Showdown — Descarga datos        ║")
    print("╚══════════════════════════════════════════════════╝")

    RAW.mkdir(parents=True, exist_ok=True)

    section("1/2  Batallas gen8randombattle")
    download_battles()

    section("2/2  Pokémon stats (PokeAPI)")
    download_stats()

    print(f"\n{'─' * 50}")
    print("  Descarga completa.")
    print("  Siguiente paso: uv run python src/02_preprocess.py")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
