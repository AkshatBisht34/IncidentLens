import time
import uuid
from datetime import datetime, timezone

from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionError as OpenSearchConnectionError

from simulator.services.payment_api import PaymentAPI


INDEX_NAME = "incidentlens-telemetry"


class ProductionSimulator:

    def __init__(self):
        self.payment_api = PaymentAPI("healthy")

        # One ID for this entire simulated production run.
        self.run_id = str(uuid.uuid4())

        # Connect to the local OpenSearch container
        self.client = OpenSearch(
            hosts=[{"host": "localhost", "port": 9200}],
            use_ssl=False,
            verify_certs=False,
        )

    def set_state(self, state):
        self.payment_api.set_state(state)

        print(f"\n=== Production state changed to: {state.upper()} ===")

    def send_to_opensearch(self, record):
        try:
            response = self.client.index(
                index=INDEX_NAME,
                body=record,
            )
            print(
                f"Sent {record['type']} to OpenSearch "
                f"(document ID: {response['_id']})"
            )
        except OpenSearchConnectionError:
            print(
                f"WARNING: OpenSearch unavailable. "
                f"Could not send {record['type']}."
            )

    def generate_request(self):
        result = self.payment_api.process_payment()

        timestamp = datetime.now(timezone.utc).isoformat()

        log = {
            "run_id": self.run_id,
            "timestamp": timestamp,
            "type": "log",
            "service": result["service"],
            "state": result["state"],
            "message": "Payment request processed",
            "success": result["success"],
            "latency_ms": result["latency_ms"],
        }

        metric = {
            "run_id": self.run_id,
            "timestamp": timestamp,
            "type": "metric",
            "service": result["service"],
            "metric": "request_latency_ms",
            "state": result["state"],
            "value": result["latency_ms"],
        }

        event = {
            "run_id": self.run_id,
            "timestamp": timestamp,
            "type": "event",
            "service": result["service"],
            "event": "payment_processed",
            "state": result["state"],
            "success": result["success"],
        }

        return [log, metric, event]


if __name__ == "__main__":
    simulator = ProductionSimulator()

    print("IncidentLens simulated production started.")
    print(f"Run ID: {simulator.run_id}")
    print("Production will continuously generate telemetry.")

    while True:

        # HEALTHY
        simulator.set_state("healthy")

        for _ in range(5):
            records = simulator.generate_request()

            for record in records:
                print(f"{record['type'].upper()}: {record}")
                simulator.send_to_opensearch(record)

            time.sleep(2)

        # DEGRADED
        simulator.set_state("degraded")

        for _ in range(5):
            records = simulator.generate_request()

            for record in records:
                print(f"{record['type'].upper()}: {record}")
                simulator.send_to_opensearch(record)

            time.sleep(2)

        # FAILING
        simulator.set_state("failing")

        for _ in range(5):
            records = simulator.generate_request()

            for record in records:
                print(f"{record['type'].upper()}: {record}")
                simulator.send_to_opensearch(record)

            time.sleep(2)
