from opentelemetry import metrics
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from prometheus_client import start_http_server

# Start Prometheus client
start_http_server(port=8099, addr="0.0.0.0")

# Create resource and exporter
resource = Resource(attributes={SERVICE_NAME: "gdgaic-lossteach-model"})
reader = PrometheusMetricReader()
provider = MeterProvider(resource=resource, metric_readers=[reader])

# Set global provider
metrics.set_meter_provider(provider)

# Create and expose meter
meter = metrics.get_meter("lossteach-ggaic", "1.0")