from datetime import datetime, timezone

from opensearchpy import OpenSearch

from simulator.services.payment_api import PaymentAPI


# Connect to the local OpenSearch container
client = OpenSearch(
    hosts=[{"host": "localhost", "port": 9200}],
    use_ssl=False,
    verify_certs=False,
)

INDEX_NAME = "incidentlens-telemetry"


def send_to_opensearch(record):
    response = client.index(
        index=INDEX_NAME,
        body=record,
    )

    print(
        f"Sent {record['type']} to OpenSearch "
        f"(document ID: {response['_id']})"
    )


def generate_telemetry(service):
    # Ask the simulated production service to process a request
    result = service.process_payment()

    timestamp = datetime.now(timezone.utc).isoformat()

    log = {
        "timestamp": timestamp,
        "type": "log",
        "service": result["service"],
        "message": "Payment request processed",
        "state": result["state"],
        "success": result["success"],
        "latency_ms": result["latency_ms"],
    }

    metric = {
        "timestamp": timestamp,
        "type": "metric",
        "service": result["service"],
        "metric": "request_latency_ms",
        "state": result["state"],
        "value": result["latency_ms"],
    }

    event = {
        "timestamp": timestamp,
        "type": "event",
        "service": result["service"],
        "event": "payment_processed",
        "state": result["state"],
        "success": result["success"],
    }

    return [log, metric, event]


if __name__ == "__main__":
    service = PaymentAPI()

    telemetry_records = generate_telemetry(service)

    for record in telemetry_records:
        print(f"{record['type'].upper()}: {record}")
        send_to_opensearch(record)
