import itertools
import threading
import time
import requests
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datasets import load_dataset
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"

REPLAYS_REPO = "HolidayOugi/pokemon-showdown-replays"
FORMAT_FILTER = "gen1randombattle"
STATS_URL = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv/pokemon_stats.csv"


class Spinner:
    """Spinner animado para operaciones bloqueantes sin progreso medible."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, msg: str) -> None:
        self.msg = msg
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self) -> None:
        for frame in itertools.cycle(self.FRAMES):
            if self._stop.is_set():
                break
            elapsed = time.time() - self._start
            print(f"\r  {frame} {self.msg}  [{elapsed:.1f}s]", end="", flush=True)
            time.sleep(0.1)

    def __enter__(self) -> "Spinner":
        self._start = time.time()
        self._thread.start()
        return self

    def __exit__(self, *_) -> None:
        self._stop.set()
        self._thread.join()
        elapsed = time.time() - self._start
        print(f"\r  ✓ {self.msg}  [{elapsed:.1f}s]", flush=True)


def download_battles() -> None:
    dest = RAW / "gen1rb.parquet"
    if dest.exists():
        size_mb = dest.stat().st_size / 1_048_576
        print(f"  gen1rb.parquet ya existe ({size_mb:.1f} MB) — saltando.")
        return

    print(f"  Fuente : {REPLAYS_REPO}")
    print(f"  Filtro : formatid == '{FORMAT_FILTER}'")
    print(f"  Modo   : streaming (evita bajar los 66 GB completos)\n")

    ds = load_dataset(REPLAYS_REPO, split="train", streaming=True)
    filtered = ds.filter(lambda row: row["formatid"] == FORMAT_FILTER)

    BATCH_SIZE = 5_000
    batch: list[dict] = []
    writer: pq.ParquetWriter | None = None
    total_written = 0

    with tqdm(
        desc="  Descargando",
        unit=" batallas",
        colour="cyan",
        bar_format="  {desc}: {n:,}{unit} [{elapsed}, {rate_fmt}]",
    ) as pbar:
        for row in filtered:
            batch.append(row)
            if len(batch) >= BATCH_SIZE:
                table = pa.Table.from_pylist(batch)
                if writer is None:
                    writer = pq.ParquetWriter(dest, table.schema)
                writer.write_table(table)
                total_written += len(batch)
                batch = []
                pbar.set_postfix_str(f"{dest.stat().st_size / 1_048_576:.0f} MB en disco")
            pbar.update(1)

    if batch:
        table = pa.Table.from_pylist(batch)
        if writer is None:
            writer = pq.ParquetWriter(dest, table.schema)
        writer.write_table(table)
        total_written += len(batch)

    if writer:
        writer.close()

    size_mb = dest.stat().st_size / 1_048_576
    schema = pq.read_schema(dest)
    print(f"\n  Guardado → {dest}")
    print(f"  {total_written:,} batallas  |  {size_mb:.1f} MB  |  {len(schema.names)} columnas")
    print(f"  Columnas: {schema.names}")
    print()
    # Lee solo el primer row group para evitar cargar el archivo entero
    first_rows = pq.ParquetFile(dest).read_row_group(0, columns=["id", "players", "rating", "uploadtime"])
    print(first_rows.to_pandas().head(3).to_string(index=False))


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

    section("1/2  Batallas gen1randombattle")
    download_battles()

    section("2/2  Pokémon stats (PokeAPI)")
    download_stats()

    print(f"\n{'─' * 50}")
    print("  Descarga completa.")
    print("  Siguiente paso: uv run python src/02_preprocess.py")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
