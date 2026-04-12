# Monitoring Setup Guide

This document describes how to set up and use the monitoring stack for the PDCA application.

## Architecture

The monitoring stack consists of:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **FastAPI integration**: Application metrics exposed via `/metrics` endpoint

## Quick Start

### 1. Start Monitoring Services

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Verify services are running
docker-compose -f docker-compose.monitoring.yml ps
```

### 2. Access Dashboards

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin` (change in production!)

- **Prometheus**: http://localhost:9090

### 3. View Metrics

Grafana dashboards are automatically provisioned:
- API Overview
- PDCA Analytics
- AI Performance
- Infrastructure

## Metrics Collected

### HTTP Metrics
- Request rate by endpoint and status code
- Request duration (P50, P95, P99)
- Active requests

### PDCA Metrics
- Cycles created by user and department
- Cycle status distribution
- Stage duration

### AI Agent Metrics
- Request count by provider and model
- Token usage (prompt and completion)
- Estimated cost
- Request duration

### Infrastructure Metrics
- Database connection pool usage
- Query performance

## Maintenance

### Restart Services

```bash
docker-compose -f docker-compose.monitoring.yml restart
```

### View Logs

```bash
# Prometheus logs
docker-compose -f docker-compose.monitoring.yml logs prometheus

# Grafana logs
docker-compose -f docker-compose.monitoring.yml logs grafana
```

### Stop Services

```bash
docker-compose -f docker-compose.monitoring.yml down
```

## Troubleshooting

### Prometheus not scraping metrics

1. Check if backend is running: `curl http://localhost:8000/metrics`
2. Verify Prometheus configuration: `docker exec prometheus promtool check config /etc/prometheus/prometheus.yml`
3. Check Prometheus targets: http://localhost:9090/targets

### Grafana no data

1. Verify datasource is connected: http://localhost:3000/datasources
2. Check Prometheus has data: http://localhost:9090/graph
3. Verify dashboard time range

## Security Notes

**IMPORTANT** for production:
1. Change default Grafana password
2. Restrict `/metrics` endpoint access
3. Enable authentication on Prometheus
4. Use HTTPS/TLS for all services
5. Regular security updates
