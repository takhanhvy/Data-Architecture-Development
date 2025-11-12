"""
This module contains functions for cleaning and preprocessing data from various sources.

Data sources include CSV files (data/bronze_layer/*.csv): 
* DVF - Demandes de valeurs foncières 2020-2025 (data.gouv.fr) containing real estate transaction data in France.
* DVF 2014-2020 aggregated at the municipal level (opendata.caissedesdepots.fr) and applied certain filters to offer stable and consistent data over clearly identified perimeters.
    -> Raw and aggredated DVF data versions need to be preprocessed then merged to create a complete dataset.
* Air quality data - Air quality measurements in Paris, France (airparif.fr) 
* Public transport data - RATP open data (data.ratp.fr) containing information about public transport in Paris, France.
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_raw_dvf_data(filepath):
    """
    Read and merge raw DVF data from a CSV files ("data/bronze_layer/dvf_75_[year].csv") and returns a one single raw dataframe.
    
    Args:
        file_path (str): Path to the CSV file containing DVF data.
    Returns:
        pd.DataFrame: merged DVF data.
    """
    frames = []
    for year in range(2020, 2026):
        file_path = Path(f"{ROOT}/data/bronze_layer/dvf_75_{year}.csv")
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        frames.append(pd.read_csv(file_path, sep=",", encoding="utf-8"))
    return pd.concat(frames, ignore_index=True)    


def main():
    res = read_raw_dvf_data(f"{ROOT}/data/bronze_layer/dvf_75_2020.csv")
    print(res)

if __name__ == "__main__":
    main()