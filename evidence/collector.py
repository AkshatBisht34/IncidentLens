from opensearchpy import OpenSearch


INDEX_NAME = "incidentlens-telemetry"


class EvidenceCollector:
    def __init__(self):
        self.client = OpenSearch(
            hosts=[{"host": "localhost", "port": 9200}],
            use_ssl=False,
            verify_certs=False,
        )

    def get_recent_telemetry(self, size=20):
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
                    "match_all": {}
                },
            },
        )

        return [
            hit["_source"]
            for hit in response["hits"]["hits"]
        ]


if __name__ == "__main__":
    collector = EvidenceCollector()

    evidence = collector.get_recent_telemetry()

    print(f"Collected {len(evidence)} telemetry records.\n")

    for record in evidence:
        print(record)
