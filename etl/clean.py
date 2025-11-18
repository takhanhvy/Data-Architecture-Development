"""
This module contains functions for cleaning data from various sources.

Data sources include CSV files (data/bronze_layer/*.csv): 
* DVF - Demandes de valeurs foncières 2020-2025 (data.gouv.fr) containing real estate transaction data in France.
* Air quality data - Air quality measurements in Paris, France (airparif.fr) 
* Public transport data - RATP open data (data.ratp.fr) containing information about public transport in Paris, France.
"""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_dvf_data() -> pd.DataFrame:
    """
    Read DVF data from CSV files for the years 2020 to 2025 and concatenate them into a single dataframe.
    Args:
        None.
    Returns:
        pd.DataFrame: Concatenated DVF dataframe for the years 2020 to 2025.
    """
    df_list = []
    for year in range(2020, 2026):
        file_path = ROOT / "data" / "bronze_layer" / f"dvf_75_{year}.csv"
        if not file_path.exists():
            raise FileNotFoundError(file_path)
        df = pd.read_csv(file_path, sep=",", encoding="utf-8", header=0)
        df["annee"] = year
        df_list.append(df)
    return pd.concat(df_list, ignore_index=True)


def clean_dvf_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess raw DVF data by selecting relevant columns and filtering rows based on specific criteria.
    Args:
        df (pd.DataFrame): Raw DVF dataframe.
    Returns:
        pd.DataFrame: Cleaned DVF dataframe.
    """

    # columns to keep
    columns_to_keep = [
        "id_mutation",
        "code_commune",
        "annee",
        "valeur_fonciere",
        "type_local",
        "surface_reelle_bati",
        "nombre_pieces_principales",
        "prix_m2"
    ]

    # filter nature_mutation to keep only sales : "Vente" 
    df = df[df["nature_mutation"] == "Vente"]

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
    df["prix_m2"] = df["valeur_fonciere"] / df["surface_reelle_bati"]

    # keep only relevant columns
    df = df[columns_to_keep]

    return df


def save_to_silver(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save the cleaned DVF dataframe to a CSV file in the silver layer (data/silver_layer/).
    
    Args:
        df (pd.DataFrame): Cleaned DVF dataframe.
        output_path (Path): Path to save the cleaned DVF CSV file.
    Returns:
        None.
    """    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, header=True, sep=";", encoding="utf-8")


def main(): 
    dvf_data = read_dvf_data()
    cleaned_dvf_data = clean_dvf_data(dvf_data)
    output_path = Path(f"{ROOT}/data/silver_layer/cleaned_dvf_data.csv")
    save_to_silver(cleaned_dvf_data, output_path)


if __name__ == "__main__":
    main()