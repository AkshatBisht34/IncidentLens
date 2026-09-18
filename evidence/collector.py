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

    def get_recent_evidence(self, service, size=20):
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
                    "term": {
                        "service.keyword": service
                    }
                },
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]

    def get_failure_evidence(self, service, size=20):
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

    def get_timeline(self, service, size=30):
        """
        Retrieve telemetry for a service in chronological order.

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
                "query": {
                    "term": {
                        "service.keyword": service
                    }
                },
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m evidence.collector <service>")
        sys.exit(1)

    service = sys.argv[1]

    collector = EvidenceCollector()

    print(f"\n=== Recent evidence for {service} ===")

    recent_evidence = collector.get_recent_evidence(
        service=service,
        size=20,
    )

    print(f"Collected {len(recent_evidence)} recent records.\n")

    for record in recent_evidence:
        print(record)

    print(f"\n=== Failure evidence for {service} ===")

    failure_evidence = collector.get_failure_evidence(
        service=service,
        size=20,
    )

    print(f"Collected {len(failure_evidence)} failed records.\n")

    for record in failure_evidence:
        print(record)

    print(f"\n=== High-latency evidence for {service} ===")

    latency_evidence = collector.get_latency_evidence(
        service=service,
        min_latency_ms=1000,
        size=20,
    )

    print(
        f"Collected {len(latency_evidence)} high-latency records.\n"
    )

    for record in latency_evidence:
        print(record)

    print(f"\n=== Timeline for {service} ===")

    timeline = collector.get_timeline(
        service=service,
        size=30,
    )

    print(f"Collected {len(timeline)} timeline records.\n")

    for record in timeline:
        print(record)
