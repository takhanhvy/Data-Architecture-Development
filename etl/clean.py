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


def read_raw_dvf_data(file_path) -> pd.DataFrame:
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
    The aim is to have 2020-2025 DVF data with the equivalent perimeter as the 2014-2020 aggregated DVF data (data/bronze_layer/donnees-valeurs-foncieres-a-la-commune_2014_2020.csv).
    
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

    raw_dvf_data = pd.concat(df_list, ignore_index=True)

    # aggregate by code_commune and year 
    # to get total number of sale transactions and average price per square meter
    agg_raw_dvf_data = raw_dvf_data.groupby(["code_commune", "year"]).agg(
        nbmut_vente =("id_mutation", "count"),
        nbmut_ventem = ("id_mutation", lambda x: x["type_local"].value_counts().get("Maison", 0)),
        nbmut_ventea = ("id_mutation", lambda x: x["type_local"].value_counts().get("Appartement", 0)),
        vfm2_ventea = ("price_m2", "mean"),
        vfm2_ventea_t1 = ("price_m2", lambda x: (x["nombre_pieces_principales"] == 1).mean()),
        vfm2_ventea_t2 = ("price_m2", lambda x: (x["nombre_pieces_principales"] == 2).mean()),
        vfm2_ventea_t3 = ("price_m2", lambda x: (x["nombre_pieces_principales"] == 3).mean()),
        vfm2_ventea_t4 = ("price_m2", lambda x: (x["nombre_pieces_principales"] == 4).mean()),
        vfm2_ventea_t5 = ("price_m2", lambda x: (x["nombre_pieces_principales"] == 5).mean()),
    ).reset_index()

    return agg_raw_dvf_data


def read_agg_dvf_data() -> pd.DataFrame:
    """
    Read and clean aggregated DVF data from a CSV file ("data/bronze_layer/donnees-valeurs-foncieres-a-la-commune_2014_2020.csv") and returns a dataframe.
    
    Args:
        None
    Returns:
        pd.DataFrame: cleaned aggregated DVF dataframe.
    """
    file_path = Path(f"{ROOT}/data/bronze_layer/donnees-valeurs-foncieres-a-la-commune_2014_2020.csv")
    if not file_path.exists():
        raise FileNotFoundError(file_path)
    
    df = pd.read_csv(file_path, sep=";", encoding="utf-8", header=0)

    return df


def clean_agg_dvf_data() -> pd.DataFrame:

    """
    Clean aggregated DVF data by selecting relevant columnsa.
    
    Args:
        None.
    Returns:
        pd.DataFrame: Cleaned aggregated DVF dataframe.
    """    
    df = read_agg_dvf_data()
    
    # drop duplicates
    df = df.drop_duplicates()

    # select relevant columns
    columns_to_keep = ["anneemut", "codgeo_2020", "nbmut_vente", "nbmut_ventem", "nbmut_ventea",
                       "vfm2_ventea", "vfm2_ventea_t1", "vfm2_ventea_t2", "vfm2_ventea_t3", 
                       "vfm2_ventea_t4", "vfm2_ventea_t5"]
    df = df[columns_to_keep]

    return df


def main():
    res = preprocess_raw_dvf_data()
    print(res)

if __name__ == "__main__":
    main()