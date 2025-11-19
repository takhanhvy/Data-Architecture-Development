"""
Utilities to load the aggregated DVF dataset and prepare payloads for the API.
"""

from collections import defaultdict
import csv
from functools import lru_cache
from statistics import median
from typing import Dict, List, Optional, Tuple

from ..config import GOLD_LAYER_FILE

Row = Dict[str, object]


@lru_cache(maxsize=1)
def _load_rows() -> Tuple[Row, ...]:
    """
    Load the aggregated DVF dataset once and keep it cached in memory.
    """
    rows: List[Row] = []
    with GOLD_LAYER_FILE.open("r", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=";")
        for raw in reader:
            code = raw["code_commune"].strip()
            arrondissement = code[-2:]
            rows.append(
                {
                    "code_commune": code,
                    "arrondissement": arrondissement,
                    "arrondissement_num": int(arrondissement),
                    "annee": int(float(raw["annee"])),
                    "type_local": raw["type_local"].strip(),
                    "prix_m2_med": float(raw["prix_m2_med"]),
                    "nb_ventes": int(float(raw["nb_ventes"])),
                }
            )
    return tuple(rows)


def refresh_cache() -> None:
    """
    Allow live reloads when the gold-layer file is updated.
    """
    _load_rows.cache_clear()
    _load_rows()


def get_available_years() -> List[int]:
    """
    Return the sorted list of available years.
    """
    years = {row["annee"] for row in _load_rows()}
    return sorted(int(year) for year in years)


def _filter_rows(
    year: Optional[int] = None,
    type_local: Optional[str] = None,
) -> List[Row]:
    target_type = type_local.lower() if type_local else None
    results = []
    for row in _load_rows():
        if year is not None and row["annee"] != int(year):
            continue
        if target_type and row["type_local"].lower() != target_type:
            continue
        results.append(row)
    return results


def get_arrondissement_summary(
    year: Optional[int] = None,
    type_local: Optional[str] = None,
) -> List[Dict[str, object]]:
    """
    Aggregate the DVF data at arrondissement level for a given year and optional housing type.
    """
    rows = _filter_rows(year=year, type_local=type_local)
    aggregated: Dict[
        Tuple[str, int, int], Dict[str, object]
    ] = defaultdict(lambda: {"prix_values": [], "nb_ventes": 0})

    for row in rows:
        key = (row["code_commune"], row["annee"], row["arrondissement_num"])
        aggregated[key]["prix_values"].append(row["prix_m2_med"])
        aggregated[key]["nb_ventes"] += int(row["nb_ventes"])
        aggregated[key]["arrondissement"] = row["arrondissement"]

    payload = []
    for (code_commune, annee, arr_num), stats in aggregated.items():
        prix_values = stats["prix_values"]
        payload.append(
            {
                "code_commune": code_commune,
                "annee": annee,
                "arrondissement": stats["arrondissement"],
                "arrondissement_num": arr_num,
                "prix_m2_med": round(median(prix_values), 2) if prix_values else 0,
                "nb_ventes": int(stats["nb_ventes"]),
                "label": f"{arr_num:02d}e arrondissement",
            }
        )

    payload.sort(key=lambda row: (row["annee"], row["arrondissement_num"]))
    return payload


def get_arrondissement_timeseries(
    code_commune: str,
    type_local: Optional[str] = None,
) -> List[Dict[str, object]]:
    """
    Return the time series for a single arrondissement code (e.g. 75101).
    """
    code = str(code_commune).zfill(5)
    rows = [
        row for row in _filter_rows(type_local=type_local) if row["code_commune"] == code
    ]
    aggregated: Dict[int, Dict[str, object]] = defaultdict(
        lambda: {"prix_values": [], "nb_ventes": 0}
    )

    for row in rows:
        aggregated[row["annee"]]["prix_values"].append(row["prix_m2_med"])
        aggregated[row["annee"]]["nb_ventes"] += int(row["nb_ventes"])

    payload = []
    for year, stats in aggregated.items():
        prix_values = stats["prix_values"]
        payload.append(
            {
                "annee": year,
                "prix_m2_med": round(median(prix_values), 2) if prix_values else 0,
                "nb_ventes": int(stats["nb_ventes"]),
            }
        )

    payload.sort(key=lambda row: row["annee"])
    return payload
