#!/bin/bash
set -e

echo "Verifying monitoring stack..."

# Check if services are running
echo "Checking services..."
docker-compose -f docker-compose.monitoring.yml ps | grep -q "prometheus.*Up"
echo "✓ Prometheus is running"

docker-compose -f docker-compose.monitoring.yml ps | grep -q "grafana.*Up"
echo "✓ Grafana is running"

# Check metrics endpoint
echo "Checking /metrics endpoint..."
curl -s http://localhost:8000/metrics | grep -q "http_requests_total"
echo "✓ /metrics endpoint is accessible"

# Check Prometheus targets
echo "Checking Prometheus targets..."
curl -s http://localhost:9090/api/v1/targets | grep -q "health"
echo "✓ Prometheus is configured"

# Check Grafana datasources
echo "Checking Grafana datasources..."
curl -s http://localhost:3000/api/datasources | grep -q "Prometheus"
echo "✓ Grafana datasource is configured"

echo ""
echo "All checks passed! ✓"
echo ""
echo "Access your dashboards at:"
echo "  Grafana: http://localhost:3000 (admin/admin)"
echo "  Prometheus: http://localhost:9090"
