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

def read_dvf_data(file_path):
    """
    Reads raw DVF data from a CSV files ("data/bronze_layer/dvf_75_[year].csv") and returns a cleaned DataFrame.
    
    Args:
        file_path (str): Path to the CSV file containing DVF data.
    Returns:
        pd.DataFrame: Cleaned DVF data.
    """

    df = pd.read_csv(file_path, sep=';', encoding='utf-8', header=0)
    return df.head()
    # Perform cleaning operations   


def main():
    if __name__ == "__main__":
        res = read_dvf_data("./data/bronze_layer/dvf_75_2020.csv")
        print(res)