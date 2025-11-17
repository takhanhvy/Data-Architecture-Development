"""
This module contains functions for cleaning and preprocessing data from various sources.

Data sources include CSV files (data/bronze_layer/*.csv): 
* DVF - Demandes de valeurs foncières 2020-2025 (data.gouv.fr) containing real estate transaction data in France.
* Air quality data - Air quality measurements in Paris, France (airparif.fr) 
* Public transport data - RATP open data (data.ratp.fr) containing information about public transport in Paris, France.
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_dvf_data(file_path) -> pd.DataFrame:
    """
    Read raw DVF data from a CSV file ("data/bronze_layer/dvf_75_[year].csv") and returns a dataframe containing the raw DVF data for one single year.
    
    Args:
        file_path (Path): Path to the raw DVF CSV file.
    Returns:
        pd.DataFrame: raw DVF dataframe.
    """    
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    return pd.read_csv(file_path, sep=",", encoding="utf-8", header = 0)


def preprocess_raw_dvf_data() -> pd.DataFrame:
    """
    Preprocess raw DVF data by selecting relevant columns and filtering rows based on specific criteria.
    
    Args:
        None.
    Returns:
        pd.DataFrame: Preprocessed DVF dataframe.
    """
    
    # list of dataframes for each year  
    df_list = [] 

    for year in range(2020, 2026):
        file_path = Path(f"{ROOT}/data/bronze_layer/dvf_75_{year}.csv")
        df = read_raw_dvf_data(file_path)

        # filter nature_mutation to keep only sales : "Vente" 
        df = df[df["nature_mutation"] == "Vente"]

        # add year column
        df["year"] = year

        # drop duplicates
        df = df.drop_duplicates()

        # drop rows with missing code_commune, valeur_fonciere, type_local, surface_reelle_bati
        df = df.dropna(subset=["code_commune", "valeur_fonciere", "type_local", "surface_reelle_bati"])

        # filter type_local to keep only "Appartement" and "Maison"
        df = df[df["type_local"].isin(["Appartement", "Maison"])]

        # drop rows with missing or zero values in "valeur_fonciere" or "surface_reelle_bati"
        df = df.dropna(subset=["valeur_fonciere", "surface_reelle_bati"])

        # exclude "Maison" with surface <10 m2 or > 300 m2 , and "Appartement" with surface > 200 m2
        df = df[~((df["type_local"] == "Maison") & (df["surface_reelle_bati"] < 10))]
        df = df[~((df["type_local"] == "Maison") & (df["surface_reelle_bati"] > 300))]
        df = df[~((df["type_local"] == "Appartement") & (df["surface_reelle_bati"] > 200))]

        # exclude housing with more than 8 principle rooms
        df = df[~(df["nombre_pieces_principales"] > 8)]

        # exclude housing with value valeur_fonciere <= 2€
        df = df[~(df["valeur_fonciere"] <= 2)]

        # calculate price per square meter
        df["price_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

        df_list.append(df)

    return pd.concat(df_list, ignore_index=True)


def main():
    res = preprocess_raw_dvf_data()
    print(res)

if __name__ == "__main__":
    main()