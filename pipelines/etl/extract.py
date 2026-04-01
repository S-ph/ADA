"""Extract data from APIs and Data Lake."""
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

RAW_DATA_PATH = Path(os.getenv("RAW_DATA_PATH", "data/raw"))
VENDAS_API_URL = os.getenv("VENDAS_API_URL", "http://localhost:8000")
FINANCEIRO_API_URL = os.getenv("FINANCEIRO_API_URL", "http://localhost:8001")


def extract_sales(date: str = None) -> list:
    """Extract sales data from API or raw files."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Try API first
    try:
        response = requests.get(f"{VENDAS_API_URL}/vendas", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Extracted {len(data)} sales records from API")

        # Save to raw layer
        raw_path = RAW_DATA_PATH / "sales" / date
        raw_path.mkdir(parents=True, exist_ok=True)
        with open(raw_path / "sales.json", "w") as f:
            json.dump(data, f, indent=2, default=str)

        return data
    except Exception as e:
        logger.warning(f"Could not fetch from API: {e}. Loading from raw files.")

    # Fallback to raw files
    raw_file = RAW_DATA_PATH / "sales" / "sample.json"
    if raw_file.exists():
        with open(raw_file) as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} sales records from raw files")
        return data

    return []


def extract_financial(date: str = None) -> list:
    """Extract financial data from API."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    try:
        response = requests.get(f"{FINANCEIRO_API_URL}/transacoes", timeout=10)
        response.raise_for_status()
        data = response.json()
        logger.info(f"Extracted {len(data)} financial records from API")

        raw_path = RAW_DATA_PATH / "financial" / date
        raw_path.mkdir(parents=True, exist_ok=True)
        with open(raw_path / "transactions.json", "w") as f:
            json.dump(data, f, indent=2, default=str)

        return data
    except Exception as e:
        logger.warning(f"Could not fetch financial data: {e}")
        return []
