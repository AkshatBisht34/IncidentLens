import sys

from opensearchpy import OpenSearch


INDEX_NAME = "incidentlens-telemetry"


class EvidenceCollector:

    def __init__(self):
        self.client = OpenSearch(
            hosts=[{"host": "localhost", "port": 9200}],
            use_ssl=False,
            verify_certs=False,
        )

    def get_latest_run_id(self, service):
        """
        Find the most recent run_id for this service.

        ProductionSimulator writes the same run_id to every telemetry
        record generated during one production process.
        """

        response = self.client.search(
            index=INDEX_NAME,
            body={
                "size": 1,
                "sort": [
                    {
                        "timestamp": {
                            "order": "desc"
                        }
                    }
                ],
                "_source": ["run_id"],
                "query": {
                    "term": {
                        "service.keyword": service
                    }
                },
            },
        )

        hits = response["hits"]["hits"]

        if not hits:
            raise ValueError(
                f"No telemetry found for service: {service}"
            )

        run_id = hits[0]["_source"].get("run_id")

        if not run_id:
            raise ValueError(
                "Latest telemetry record does not contain a run_id"
            )

        return run_id

    def _run_filter(self, service, run_id):
        """
        Common filter used by all evidence queries.

        Evidence must belong to both:
        - the requested service
        - the selected production run
        """

        return {
            "bool": {
                "must": [
                    {
                        "term": {
                            "service.keyword": service
                        }
                    },
                    {
                        "term": {
                            "run_id.keyword": run_id
                        }
                    },
                ]
            }
        }

    def get_recent_evidence(self, service, run_id, size=20):
        response = self.client.search(
            index=INDEX_NAME,
            body={
                "size": size,
                "sort": [
                    {
                        "timestamp": {
                            "order": "desc"
                        }
                    }
                ],
                "query": self._run_filter(service, run_id),
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]

    def get_failure_evidence(self, service, run_id, size=20):
        response = self.client.search(
            index=INDEX_NAME,
            body={
                "size": size,
                "sort": [
                    {
                        "timestamp": {
                            "order": "desc"
                        }
                    }
                ],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "service.keyword": service
                                }
                            },
                            {
                                "term": {
                                    "run_id.keyword": run_id
                                }
                            },
                            {
                                "term": {
                                    "success": False
                                }
                            },
                        ]
                    }
                },
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]

    def get_latency_evidence(
        self,
        service,
        run_id,
        min_latency_ms=1000,
        size=20,
    ):
        response = self.client.search(
            index=INDEX_NAME,
            body={
                "size": size,
                "sort": [
                    {
                        "latency_ms": {
                            "order": "desc"
                        }
                    }
                ],
                "query": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "service.keyword": service
                                }
                            },
                            {
                                "term": {
                                    "run_id.keyword": run_id
                                }
                            },
                            {
                                "term": {
                                    "type.keyword": "log"
                                }
                            },
                            {
                                "range": {
                                    "latency_ms": {
                                        "gte": min_latency_ms
                                    }
                                }
                            },
                        ]
                    }
                },
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]

    def get_timeline(self, service, run_id, size=30):
        """
        Retrieve telemetry for the selected production run
        in chronological order.

        This gives the investigation agent the sequence of events
        so it can reason about how the incident developed.
        """

        response = self.client.search(
            index=INDEX_NAME,
            body={
                "size": size,
                "sort": [
                    {
                        "timestamp": {
                            "order": "asc"
                        }
                    }
                ],
                "query": self._run_filter(service, run_id),
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python -m evidence.collector <service>"
        )
        sys.exit(1)

    service = sys.argv[1]

    collector = EvidenceCollector()

    # ---------------------------------------------------------
    # Select the latest production run ONCE.
    # ---------------------------------------------------------

    run_id = collector.get_latest_run_id(service)

    print(f"\n=== IncidentLens Evidence Collection ===")
    print(f"Service: {service}")
    print(f"Run ID:  {run_id}")

    # ---------------------------------------------------------
    # Recent evidence
    # ---------------------------------------------------------

    print(f"\n=== Recent evidence for {service} ===")

    recent_evidence = collector.get_recent_evidence(
        service=service,
        run_id=run_id,
        size=20,
    )

    print(
        f"Collected {len(recent_evidence)} recent records.\n"
    )

    for record in recent_evidence:
        print(record)

    # ---------------------------------------------------------
    # Failure evidence
    # ---------------------------------------------------------

    print(f"\n=== Failure evidence for {service} ===")

    failure_evidence = collector.get_failure_evidence(
        service=service,
        run_id=run_id,
        size=20,
    )

    print(
        f"Collected {len(failure_evidence)} failed records.\n"
    )

    for record in failure_evidence:
        print(record)

    # ---------------------------------------------------------
    # High latency evidence
    # ---------------------------------------------------------

    print(f"\n=== High-latency evidence for {service} ===")

    latency_evidence = collector.get_latency_evidence(
        service=service,
        run_id=run_id,
        min_latency_ms=1000,
        size=20,
    )

    print(
        f"Collected {len(latency_evidence)} high-latency "
        "records.\n"
    )

    for record in latency_evidence:
        print(record)

    # ---------------------------------------------------------
    # Timeline
    # ---------------------------------------------------------

    print(f"\n=== Timeline for {service} ===")

    timeline = collector.get_timeline(
        service=service,
        run_id=run_id,
        size=30,
    )

    print(
        f"Collected {len(timeline)} timeline records.\n"
    )

    for record in timeline:
        print(record)
