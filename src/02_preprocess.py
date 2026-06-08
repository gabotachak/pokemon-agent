"""02_preprocess.py — Feature engineering: gen8rb.parquet → battles_featured.parquet"""

import re
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from multiprocessing import Pool, cpu_count
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

POKEAPI = "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/data/v2/csv"
STAT_ID = {1: "hp", 2: "attack", 3: "defense", 4: "sp_attack", 5: "sp_defense", 6: "speed"}
DAMAGE_CLASS = {1: "status", 2: "physical", 3: "special"}


# ── Supplementary data ──────────────────────────────────────────────────────


def fetch_csv(filename: str) -> pd.DataFrame:
    dest = RAW / filename
    if not dest.exists():
        print(f"  Descargando {filename}...", flush=True)
        r = requests.get(f"{POKEAPI}/{filename}", timeout=30)
        r.raise_for_status()
        dest.write_bytes(r.content)
    return pd.read_csv(dest)


def load_stats_lookup() -> dict:
    """Returns {pokemon_name: {hp, attack, defense, sp_attack, sp_defense, speed, stat_total}}"""
    pokemon = fetch_csv("pokemon.csv")[["id", "identifier"]].rename(columns={"identifier": "name"})
    stats_df = fetch_csv("pokemon_stats.csv")
    stats_df["stat_name"] = stats_df["stat_id"].map(STAT_ID)
    wide = stats_df.pivot(index="pokemon_id", columns="stat_name", values="base_stat").reset_index()
    wide.columns.name = None
    merged = pokemon.merge(wide, left_on="id", right_on="pokemon_id")
    cols = ["hp", "attack", "defense", "sp_attack", "sp_defense", "speed"]
    merged["stat_total"] = merged[cols].sum(axis=1)
    return merged.set_index("name")[cols + ["stat_total"]].to_dict("index")


def load_types_lookup() -> dict:
    """Returns {pokemon_name: [type_name, ...]}"""
    pokemon = fetch_csv("pokemon.csv")[["id", "identifier"]].rename(columns={"identifier": "name"})
    ptypes = fetch_csv("pokemon_types.csv")
    tnames = fetch_csv("types.csv")[["id", "identifier"]].rename(columns={"identifier": "type_name"})
    merged = ptypes.merge(tnames, left_on="type_id", right_on="id")
    merged = merged.merge(pokemon, left_on="pokemon_id", right_on="id")
    return merged.groupby("name")["type_name"].apply(list).to_dict()


def load_moves_lookup() -> tuple[dict, dict]:
    """Returns (damage_class_lookup, type_lookup): {move_id: class}, {move_id: type_name}"""
    moves_df = fetch_csv("moves.csv")[["identifier", "damage_class_id", "type_id"]]
    tnames = fetch_csv("types.csv")[["id", "identifier"]].rename(
        columns={"id": "type_id", "identifier": "type_name"}
    )
    merged = moves_df.merge(tnames, on="type_id", how="left")
    merged["damage_class"] = merged["damage_class_id"].map(DAMAGE_CLASS).fillna("status")
    damage = merged.set_index("identifier")["damage_class"].to_dict()
    move_type = merged.set_index("identifier")["type_name"].to_dict()
    return damage, move_type


# ── Name normalization ──────────────────────────────────────────────────────


_POKEMON_OVERRIDES = {
    "nidoran♀": "nidoran-f",
    "nidoran♂": "nidoran-m",
    "flabébé": "flabebe",
    "type: null": "type-null",
    "farfetch'd": "farfetchd",
    "farfetch'd-galar": "farfetchd-galar",
    "sirfetch'd": "sirfetchd",
    "mr. mime": "mr-mime",
    "mime jr.": "mime-jr",
    "mr. rime": "mr-rime",
    "tapu koko": "tapu-koko",
    "tapu lele": "tapu-lele",
    "tapu bulu": "tapu-bulu",
    "tapu fini": "tapu-fini",
    "ho-oh": "ho-oh",
    "porygon-z": "porygon-z",
    "jangmo-o": "jangmo-o",
    "hakamo-o": "hakamo-o",
    "kommo-o": "kommo-o",
}


def normalize_pokemon(name: str) -> str:
    lower = name.lower().strip()
    if lower in _POKEMON_OVERRIDES:
        return _POKEMON_OVERRIDES[lower]
    result = lower.replace(". ", "-").replace(".", "").replace("'", "")
    result = result.replace(": ", "-").replace(" ", "-")
    result = re.sub(r"-+", "-", result).strip("-")
    return result


def normalize_move(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "").strip()


# ── Log parsing ─────────────────────────────────────────────────────────────


def parse_log(log: str) -> dict:
    p1_user = p2_user = ""
    team_p1: set = set()
    team_p2: set = set()
    winner = -1
    n_turns = 0
    moves_p1: list = []
    moves_p2: list = []
    switches_p1 = 0
    switches_p2 = 0
    started = False

    for line in log.split("\n"):
        parts = line.split("|")
        if len(parts) < 2:
            continue
        cmd = parts[1]

        if cmd == "player" and len(parts) > 3:
            if parts[2] == "p1":
                p1_user = parts[3]
            elif parts[2] == "p2":
                p2_user = parts[3]

        elif cmd == "start":
            started = True

        elif cmd == "turn" and len(parts) > 2:
            try:
                n_turns = int(parts[2])
            except ValueError:
                pass

        elif cmd in ("switch", "drag") and len(parts) > 3:
            side = parts[2][:2]
            poke_raw = parts[3].split(",")[0].strip()
            if side == "p1":
                team_p1.add(poke_raw)
                if started:
                    switches_p1 += 1
            elif side == "p2":
                team_p2.add(poke_raw)
                if started:
                    switches_p2 += 1

        elif cmd == "move" and len(parts) > 3:
            side = parts[2][:2]
            move = parts[3]
            if side == "p1":
                moves_p1.append(move)
            elif side == "p2":
                moves_p2.append(move)

        elif cmd == "win" and len(parts) > 2:
            uname = parts[2].strip()
            if uname == p1_user:
                winner = 0
            elif uname == p2_user:
                winner = 1

    # Subtract initial lead-out (first send-out is automatic, not a player choice)
    switches_p1 = max(0, switches_p1 - 1)
    switches_p2 = max(0, switches_p2 - 1)

    return {
        "team_p1": list(team_p1),
        "team_p2": list(team_p2),
        "winner": winner,
        "n_turns": n_turns,
        "moves_p1": moves_p1,
        "moves_p2": moves_p2,
        "switches_p1": switches_p1,
        "switches_p2": switches_p2,
    }


def parse_logs_batch(logs: list) -> list:
    return [parse_log(log) for log in logs]


# ── Feature computation ─────────────────────────────────────────────────────


def _team_stats(team: list, stats_lookup: dict) -> dict:
    records = [stats_lookup[normalize_pokemon(p)] for p in team
               if normalize_pokemon(p) in stats_lookup]
    empty = {"avg_hp": 0.0, "avg_attack": 0.0, "avg_defense": 0.0,
             "avg_sp_attack": 0.0, "avg_sp_defense": 0.0, "avg_speed": 0.0,
             "avg_stat_total": 0.0, "n_fast_pokemon": 0}
    if not records:
        return empty
    return {
        "avg_hp": float(np.mean([r["hp"] for r in records])),
        "avg_attack": float(np.mean([r["attack"] for r in records])),
        "avg_defense": float(np.mean([r["defense"] for r in records])),
        "avg_sp_attack": float(np.mean([r["sp_attack"] for r in records])),
        "avg_sp_defense": float(np.mean([r["sp_defense"] for r in records])),
        "avg_speed": float(np.mean([r["speed"] for r in records])),
        "avg_stat_total": float(np.mean([r["stat_total"] for r in records])),
        "n_fast_pokemon": int(sum(1 for r in records if r["speed"] > 100)),
    }


def _type_features(team: list, types_lookup: dict) -> dict:
    all_types = []
    for p in team:
        all_types.extend(types_lookup.get(normalize_pokemon(p), []))
    return {"type_diversity": len(set(all_types))}


def _move_type_coverage(moves: list, move_type_lookup: dict) -> int:
    return len({move_type_lookup[normalize_move(m)]
                for m in moves
                if normalize_move(m) in move_type_lookup})


def _winning_action_type(winner: int, moves_p1: list, moves_p2: list,
                          switches_p1: int, switches_p2: int,
                          damage_class_lookup: dict) -> str:
    if winner < 0:
        return "unknown"
    moves = moves_p1 if winner == 0 else moves_p2
    sw = switches_p1 if winner == 0 else switches_p2
    counts: dict[str, int] = {"physical": 0, "special": 0, "status": 0, "switch": sw}
    for m in moves:
        cls = damage_class_lookup.get(normalize_move(m), "status")
        counts[cls] += 1
    return max(counts, key=lambda k: counts[k])


def compute_features(parsed: dict, stats_lookup: dict, types_lookup: dict,
                     damage_class_lookup: dict, move_type_lookup: dict) -> dict | None:
    if parsed["winner"] < 0 or parsed["n_turns"] < 1:
        return None

    s1 = _team_stats(parsed["team_p1"], stats_lookup)
    s2 = _team_stats(parsed["team_p2"], stats_lookup)
    if s1["avg_hp"] == 0 or s2["avg_hp"] == 0:
        return None

    t1 = _type_features(parsed["team_p1"], types_lookup)
    t2 = _type_features(parsed["team_p2"], types_lookup)
    tc1 = _move_type_coverage(parsed["moves_p1"], move_type_lookup)
    tc2 = _move_type_coverage(parsed["moves_p2"], move_type_lookup)

    n_turns = parsed["n_turns"]
    winner = parsed["winner"]
    w_switches = parsed["switches_p1"] if winner == 0 else parsed["switches_p2"]

    wat = _winning_action_type(
        winner, parsed["moves_p1"], parsed["moves_p2"],
        parsed["switches_p1"], parsed["switches_p2"], damage_class_lookup
    )
    if wat == "unknown":
        return None

    return {
        "winner": winner,
        "n_turns": n_turns,
        # P1 team
        "avg_hp_p1": s1["avg_hp"],
        "avg_attack_p1": s1["avg_attack"],
        "avg_defense_p1": s1["avg_defense"],
        "avg_sp_attack_p1": s1["avg_sp_attack"],
        "avg_sp_defense_p1": s1["avg_sp_defense"],
        "avg_speed_p1": s1["avg_speed"],
        "type_diversity_p1": t1["type_diversity"],
        "n_fast_pokemon_p1": s1["n_fast_pokemon"],
        "type_coverage_p1": tc1,
        # P2 team
        "avg_hp_p2": s2["avg_hp"],
        "avg_attack_p2": s2["avg_attack"],
        "avg_defense_p2": s2["avg_defense"],
        "avg_sp_attack_p2": s2["avg_sp_attack"],
        "avg_sp_defense_p2": s2["avg_sp_defense"],
        "avg_speed_p2": s2["avg_speed"],
        "type_diversity_p2": t2["type_diversity"],
        "n_fast_pokemon_p2": s2["n_fast_pokemon"],
        "type_coverage_p2": tc2,
        # Derived
        "stat_total_diff": s1["avg_stat_total"] - s2["avg_stat_total"],
        "speed_advantage_ratio": s1["avg_speed"] / max(s2["avg_speed"], 1.0),
        "switch_rate": w_switches / n_turns,
        # Target
        "winning_action_type": wat,
    }


# ── Main ────────────────────────────────────────────────────────────────────


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def main() -> None:
    print("╔══════════════════════════════════════════════════╗")
    print("║    Pokémon Showdown — Preprocesamiento           ║")
    print("╚══════════════════════════════════════════════════╝")

    section("1/4  Datos suplementarios (PokeAPI)")
    stats_lookup = load_stats_lookup()
    types_lookup = load_types_lookup()
    damage_class_lookup, move_type_lookup = load_moves_lookup()
    print(f"  ✓ Stats  : {len(stats_lookup):,} Pokémon")
    print(f"  ✓ Types  : {len(types_lookup):,} Pokémon")
    print(f"  ✓ Moves  : {len(damage_class_lookup):,} movimientos")

    section("2/4  Cargando batallas")
    df = pd.read_parquet(RAW / "gen8rb.parquet")
    print(f"  ✓ {len(df):,} batallas")

    section("3/4  Parseando logs")
    logs = df["log"].tolist()
    n_workers = max(1, cpu_count() - 1)
    chunk_size = max(500, len(logs) // (n_workers * 8))
    chunks = [logs[i:i + chunk_size] for i in range(0, len(logs), chunk_size)]
    print(f"  {n_workers} workers · {len(chunks)} chunks · ~{chunk_size:,} batallas/chunk")

    parsed_all: list = []
    with Pool(n_workers) as pool:
        for result in tqdm(
            pool.imap(parse_logs_batch, chunks),
            total=len(chunks),
            desc="  Parseando",
            unit=" chunk",
        ):
            parsed_all.extend(result)

    section("4/4  Computando features")
    rows = []
    skipped = 0
    for parsed in tqdm(parsed_all, desc="  Features", unit=" batalla"):
        row = compute_features(parsed, stats_lookup, types_lookup,
                               damage_class_lookup, move_type_lookup)
        if row is None:
            skipped += 1
        else:
            rows.append(row)

    print(f"\n  Procesadas : {len(rows):,}")
    print(f"  Omitidas   : {skipped:,} (sin ganador o stats desconocidos)")

    out = pd.DataFrame(rows)
    dest = PROCESSED / "battles_featured.parquet"
    out.to_parquet(dest, index=False)

    size_mb = dest.stat().st_size / 1_048_576
    print(f"\n  Guardado → {dest}")
    print(f"  {len(out):,} filas  |  {size_mb:.1f} MB  |  {len(out.columns)} columnas")
    print(f"\n  Distribución winning_action_type:")
    print(out["winning_action_type"].value_counts().to_string())
    print(f"\n  Stats descriptivas (primeras features):")
    print(out[["avg_hp_p1", "avg_speed_p1", "stat_total_diff", "n_turns"]].describe().to_string())

    print(f"\n{'─' * 50}")
    print("  Preprocesamiento completo.")
    print("  Siguiente paso: uv run python src/03_clustering.py")
    print(f"{'─' * 50}\n")


if __name__ == "__main__":
    main()
