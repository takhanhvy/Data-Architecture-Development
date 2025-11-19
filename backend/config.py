"""
Global configuration for backend services.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
GOLD_LAYER_FILE = ROOT_DIR / "data" / "gold_layer" / "agg_dvf_data.csv"

