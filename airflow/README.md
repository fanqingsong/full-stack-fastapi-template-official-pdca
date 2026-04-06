# Apache Airflow

This directory contains the Apache Airflow workflow management platform configuration for the Full Stack FastAPI Template.

## Overview

Apache Airflow is a platform to programmatically author, schedule and monitor workflows. This integration allows you to:

- Schedule and monitor data processing tasks
- Create complex workflows with dependencies
- Integrate with the FastAPI backend for scheduled jobs
- Access PostgreSQL, MinIO, Qdrant, and other services

## Services

The Airflow setup includes the following services:

- **airflow-webserver** (port 9090): Airflow UI
- **airflow-scheduler**: Schedules DAGs
- **airflow-worker**: Executes tasks
- **airflow-triggerer**: Triggers deferred tasks
- **airflow-postgres**: Airflow metadata database
- **airflow-redis**: Celery broker
- **flower** (port 5555): Celery monitoring UI

## Quick Start

### Development

```bash
# From project root
docker compose -f airflow/docker-compose.yaml -f airflow/docker-compose.dev.yml --env-file .env.dev up -d
```

### Production

```bash
# From project root
docker compose -f airflow/docker-compose.yaml --env-file .env.prod up -d
```

## Access

- **Airflow Web UI**: http://localhost:9090
  - Default username: `airflow`
  - Default password: `airflow`
- **Flower UI**: http://localhost:5555

## Configuration

### Environment Variables

Edit `.env` file to configure:

- `_AIRFLOW_WWW_USER_USERNAME`: Admin username (default: airflow)
- `_AIRFLOW_WWW_USER_PASSWORD`: Admin password (default: airflow)
- `AIRFLOW__CORE__LOAD_EXAMPLES`: Load example DAGs (default: true)

### Available Services

Airflow DAGs can access the following services:

- **PostgreSQL** (app database): `db:5432`
- **MinIO**: `minio:9000`
- **Qdrant**: `qdrant:6333`
- **Redis**: `redis:6379`

## DAGs Structure

```
airflow/
├── dags/              # Your DAG files go here
├── logs/              # Airflow logs
├── plugins/           # Custom plugins
└── Dockerfile         # Airflow image with dependencies
```

## Creating DAGs

1. Create a new Python file in `dags/` directory
2. Import required operators
3. Define your DAG with tasks
4. Airflow will automatically pick up new DAGs

Example:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def my_task():
    print("Hello from Airflow!")

with DAG(
    "my_dag",
    start_date=datetime(2024, 1, 1),
    schedule_interval=timedelta(hours=1),
) as dag:
    task = PythonOperator(
        task_id="my_task",
        python_callable=my_task,
    )
```

## Dependencies

Add Python dependencies to `requirements.txt`:

```
pandas==2.1.4
requests==2.31.0
```

## Monitoring

- **Airflow UI**: View DAG runs, task status, and logs
- **Flower UI**: Monitor Celery workers and tasks

## Common Commands

```bash
# List DAGs
docker compose exec airflow-webserver airflow dags list

# Trigger a DAG manually
docker compose exec airflow-webserver airflow dags trigger my_dag

# Check connections
docker compose exec airflow-webserver airflow connections list

# View logs
docker compose logs airflow-webserver
docker compose logs airflow-scheduler
```

## Security Notes

For production:

1. Change default admin credentials
2. Set `AIRFLOW__CORE__FERNET_KEY` for encryption
3. Set `AIRFLOW__WEBSERVER__EXPOSE_CONFIG=false`
4. Disable example DAGs: `AIRFLOW__CORE__LOAD_EXAMPLES=false`

## Troubleshooting

### DAG not appearing

1. Check DAG file syntax
2. Ensure file is in `dags/` directory
3. Check logs: `docker compose logs airflow-scheduler`

### Task failures

1. Check task logs in Airflow UI
2. Verify environment variables
3. Check service connectivity

### Resource issues

Airflow requires at least 4GB RAM and 2 CPUs. Adjust resources in Docker settings if needed.
