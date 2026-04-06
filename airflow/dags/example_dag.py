"""
Example Airflow DAG for Full Stack FastAPI Template
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
import os


def print_hello():
    """Simple Python function to test Airflow"""
    print("Hello from Airflow!")
    return "Hello from Airflow!"


def check_environment_variables():
    """Check if environment variables are accessible"""
    import os
    env_vars = {
        "POSTGRES_SERVER": os.getenv("POSTGRES_SERVER"),
        "POSTGRES_DB": os.getenv("POSTGRES_DB"),
        "MINIO_ENDPOINT": os.getenv("MINIO_ENDPOINT"),
        "QDRANT_HOST": os.getenv("QDRANT_HOST"),
    }
    print("Environment Variables:")
    for key, value in env_vars.items():
        print(f"  {key}: {value}")
    return env_vars


# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    "example_fastapi_dag",
    default_args=default_args,
    description="A simple example DAG for Full Stack FastAPI Template",
    schedule_interval=timedelta(hours=1),
    catchup=False,
    tags=["example", "fastapi", "test"],
)

# Task 1: Print Hello
hello_task = PythonOperator(
    task_id="print_hello",
    python_callable=print_hello,
    dag=dag,
)

# Task 2: Check Environment Variables
check_env_task = PythonOperator(
    task_id="check_environment_variables",
    python_callable=check_environment_variables,
    dag=dag,
)

# Task 3: Simple Bash command
bash_task = BashOperator(
    task_id="print_date",
    bash_command="date",
    dag=dag,
)

# Set task dependencies
hello_task >> check_env_task >> bash_task
