"""Main ETL pipeline orchestrator."""
import logging
import sys
from datetime import datetime

from extract import extract_financial, extract_sales
from load import get_connection, load_clients, load_dates, load_financial, load_products, load_sales
from transform import (
    transform_clients,
    transform_dates,
    transform_financial,
    transform_products,
    transform_sales,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f"etl_{datetime.now().strftime('%Y%m%d')}.log"),
    ],
)
logger = logging.getLogger(__name__)


def run_pipeline(date: str = None):
    """Run the full ETL pipeline."""
    start = datetime.now()
    logger.info(f"Starting ETL pipeline at {start}")

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    try:
        # Extract
        logger.info("=== EXTRACT ===")
        raw_sales = extract_sales(date)
        raw_financial = extract_financial(date)

        # Transform
        logger.info("=== TRANSFORM ===")
        products = transform_products(raw_sales)
        clients = transform_clients(raw_sales)
        dates = transform_dates(raw_sales)
        sales = transform_sales(raw_sales)
        financial = transform_financial(raw_financial)

        # Load
        logger.info("=== LOAD ===")
        conn = get_connection()
        try:
            load_products(products, conn)
            load_clients(clients, conn)
            load_dates(dates, conn)
            load_sales(sales, conn)
            load_financial(financial, conn)
        finally:
            conn.close()

        elapsed = (datetime.now() - start).total_seconds()
        logger.info(f"ETL pipeline completed successfully in {elapsed:.2f}s")
        return True

    except Exception as e:
        logger.error(f"ETL pipeline failed: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
