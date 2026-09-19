from datetime import datetime, timedelta


def _parse_timestamp(timestamp):
    """Convert an ISO timestamp into a datetime object."""
    return datetime.fromisoformat(timestamp)


def correlate_latency_and_failures(
    latency_evidence,
    failure_evidence,
    overlap_window_seconds=5,
):
    """
    Compare high-latency and failure timestamps and return
    a compact correlation summary.
    """

    window = timedelta(seconds=overlap_window_seconds)

    matched_pairs = 0
    closest_overlap_seconds = None
    latency_values = []

    for latency_record in latency_evidence:
        latency_time = _parse_timestamp(
            latency_record["timestamp"]
        )

        latency_value = latency_record.get("latency_ms")

        if latency_value is not None:
            latency_values.append(latency_value)

        for failure_record in failure_evidence:
            failure_time = _parse_timestamp(
                failure_record["timestamp"]
            )

            time_difference = abs(
                latency_time - failure_time
            )

            if time_difference <= window:
                matched_pairs += 1

                difference_seconds = (
                    time_difference.total_seconds()
                )

                if (
                    closest_overlap_seconds is None
                    or difference_seconds < closest_overlap_seconds
                ):
                    closest_overlap_seconds = difference_seconds

    average_latency_ms = None

    if latency_values:
        average_latency_ms = round(
            sum(latency_values) / len(latency_values),
            2,
        )

    return {
        "overlap": matched_pairs > 0,
        "matched_pairs": matched_pairs,
        "closest_overlap_seconds": (
            round(closest_overlap_seconds, 3)
            if closest_overlap_seconds is not None
            else None
        ),
        "average_latency_ms": average_latency_ms,
        "failure_count": len(failure_evidence),
    }
