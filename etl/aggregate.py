"""
This module contains functions for aggregating cleaned data from various sources.
It prepares ready-to-use datasets for building API endpoints.
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_cleaned_csv_files(file_name: str) -> pd.DataFrame:
    """
    Read csv files from silver layer
    """
    file_path = ROOT / "data" / "silver_layer" / file_name
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    return pd.read_csv(file_path, sep=";", encoding="utf-8", header=0)


def agg_dvf_by_arr_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate DVF data by arrondissement and year, calculating median price per square meter and total number of sale transactions.
    
    Args:
        df (pd.DataFrame): cleaned DVF dataframe.
    Returns:
        pd.DataFrame: Aggregated DVF dataframe by arrondissement and year.
    """
    agg_df = df.groupby(["code_commune", "annee", "type_local", "nombre_pieces_principales"]).agg(
        prix_m2_med=("prix_m2", "median"),
        nb_ventes=("id_mutation", "count")
    ).reset_index()

    return agg_df    


def main(): 
    dvf_data_file = "cleaned_dvf_data.csv"
    dvf_data = read_cleaned_csv_files(dvf_data_file)
    agg_df = agg_dvf_by_arr_year(dvf_data)
    return print(agg_df.head())


if __name__ == "__main__":
    main()