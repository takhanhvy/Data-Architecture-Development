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


def save_to_gold(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the aggregated DVF dataframe to a CSV file in the gold layer (data/gold_layer/).
    
    Args:
        df (pd.DataFrame): Aggregated DVF dataframe.
        output_path (Path): Path to save the aggregated DVF CSV file.
    Returns:
        None.
    """    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, header=True, sep=";", encoding="utf-8")


def main(): 
    dvf_data_file = "cleaned_dvf_data.csv"
    dvf_data = read_cleaned_csv_files(dvf_data_file)
    agg_df = agg_dvf_by_arr_year(dvf_data)
    output_path = Path(f"{ROOT}/data/gold_layer/agg_dvf_data.csv")
    save_to_gold(agg_df, output_path)


if __name__ == "__main__":
    main()