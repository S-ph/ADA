"""Apache Airflow DAG for daily ETL pipeline."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "scale_to_insight_etl",
    default_args=default_args,
    description="Daily ETL pipeline for Scale-to-Insight",
    schedule_interval="0 2 * * *",  # Daily at 2 AM
    catchup=False,
    tags=["etl", "data-warehouse"],
)


def extract_task(**kwargs):
    import sys
    sys.path.insert(0, "/opt/airflow/pipelines/etl")
    from extract import extract_financial, extract_sales
    date = kwargs.get("ds", datetime.now().strftime("%Y-%m-%d"))
    sales = extract_sales(date)
    financial = extract_financial(date)
    return {"sales_count": len(sales), "financial_count": len(financial)}


def transform_task(**kwargs):
    import sys
    sys.path.insert(0, "/opt/airflow/pipelines/etl")
    from extract import extract_sales
    from transform import transform_clients, transform_dates, transform_financial, transform_products, transform_sales
    raw_sales = extract_sales()
    products = transform_products(raw_sales)
    clients = transform_clients(raw_sales)
    dates = transform_dates(raw_sales)
    return {"products": len(products), "clients": len(clients), "dates": len(dates)}


def load_task(**kwargs):
    import sys
    sys.path.insert(0, "/opt/airflow/pipelines/etl")
    from main import run_pipeline
    date = kwargs.get("ds", datetime.now().strftime("%Y-%m-%d"))
    success = run_pipeline(date)
    if not success:
        raise Exception("ETL pipeline failed")


extract = PythonOperator(task_id="extract", python_callable=extract_task, dag=dag, provide_context=True)
transform = PythonOperator(task_id="transform", python_callable=transform_task, dag=dag, provide_context=True)
load = PythonOperator(task_id="load", python_callable=load_task, dag=dag, provide_context=True)

extract >> transform >> load
