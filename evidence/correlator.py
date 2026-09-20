from datetime import datetime


def parse_timestamp(record, record_type):
    """
    Parse and validate a telemetry timestamp.

    Timestamps must:
    - be valid ISO-8601 timestamps
    - contain timezone information

    Invalid or timezone-naive timestamps raise ValueError.
    """

    timestamp = record.get("timestamp")

    if not timestamp:
        raise ValueError(
            f"{record_type} record is missing a timestamp: {record}"
        )

    try:
        parsed = datetime.fromisoformat(timestamp)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid timestamp in {record_type} record: {timestamp}"
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError(
            f"Timezone-naive timestamp in {record_type} record: {timestamp}"
        )

    return parsed


def correlate_latency_and_failures(
    latency_records,
    failure_records,
    latency_threshold_ms=500,
    max_time_difference_seconds=5,
):
    """
    Compare latency records with failure records.

    This function only performs correlation calculations.
    It does not interpret the cause of failures.
    """

    high_latency_records = [
        record
        for record in latency_records
        if record.get("latency_ms", 0) >= latency_threshold_ms
    ]

    failure_count = len(failure_records)

    if high_latency_records:
        average_latency_ms = (
            sum(record["latency_ms"] for record in high_latency_records)
            / len(high_latency_records)
        )
    else:
        average_latency_ms = None

    matched_pairs = []
    closest_overlap_seconds = None

    for latency_record in high_latency_records:
        latency_time = parse_timestamp(
            latency_record,
            "latency",
        )

        for failure_record in failure_records:
            failure_time = parse_timestamp(
                failure_record,
                "failure",
            )

            difference_seconds = abs(
                (latency_time - failure_time).total_seconds()
            )

            if difference_seconds <= max_time_difference_seconds:
                matched_pairs.append(
                    {
                        "latency_timestamp": latency_record["timestamp"],
                        "failure_timestamp": failure_record["timestamp"],
                        "difference_seconds": difference_seconds,
                    }
                )

                if (
                    closest_overlap_seconds is None
                    or difference_seconds < closest_overlap_seconds
                ):
                    closest_overlap_seconds = difference_seconds

    return {
        "parameters": {
            "latency_threshold_ms": latency_threshold_ms,
            "max_time_difference_seconds": max_time_difference_seconds,
        },
        "results": {
            "matched_pairs": len(matched_pairs),
            "closest_overlap_seconds": closest_overlap_seconds,
            "average_latency_ms": average_latency_ms,
            "failure_count": failure_count,
        },
    }
