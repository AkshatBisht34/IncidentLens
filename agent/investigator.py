from strands import Agent, tool
from strands.models.ollama import OllamaModel

from evidence.collector import EvidenceCollector
from evidence.correlator import correlate_latency_and_failures


# Shared evidence collector.
collector = EvidenceCollector()


def silent_callback(*args, **kwargs):
    pass

@tool
def get_recent_evidence(service: str, size: int = 20):
    """
    Retrieve recent telemetry records for a service from OpenSearch.
    """
    return collector.get_recent_evidence(
        service,
        size=size,
    )


@tool
def get_failure_evidence(service: str, size: int = 20):
    """
    Retrieve failure records for a service from OpenSearch.
    """
    return collector.get_failure_evidence(
        service,
        size=size,
    )


@tool
def get_latency_evidence(
    service: str,
    min_latency_ms: float = 1000,
    size: int = 20,
):
    """
    Retrieve high-latency telemetry records for a service.
    """
    return collector.get_latency_evidence(
        service,
        min_latency_ms=min_latency_ms,
        size=size,
    )


@tool
def get_timeline(service: str, size: int = 30):
    """
    Retrieve chronological telemetry for a service.
    """
    return collector.get_timeline(
        service,
        size=size,
    )


@tool
def correlate_latency_and_failures_for_service(
    service: str,
    min_latency_ms: float = 1000,
    size: int = 20,
):
    """
    Compare high-latency records with failure records
    and report whether they overlap in time.
    """

    latency_evidence = collector.get_latency_evidence(
        service,
        min_latency_ms=min_latency_ms,
        size=size,
    )

    failure_evidence = collector.get_failure_evidence(
        service,
        size=size,
    )

    return correlate_latency_and_failures(
        latency_evidence,
        failure_evidence,
    )


# Local Qwen3 model running through Ollama.
model = OllamaModel(
    host="http://localhost:11434",
    model_id="qwen3:4b",
)


# The model decides which tools to use and when.
agent = Agent(
    model=model,
    tools=[
        get_recent_evidence,
        get_failure_evidence,
        get_latency_evidence,
        get_timeline,
        correlate_latency_and_failures_for_service,
    ],
    system_prompt="""
You are an incident investigation agent for IncidentLens.

Investigate the user's question using the available evidence and tools.

Structure your investigation as:

1. OBSERVATIONS
   State only facts directly supported by retrieved evidence.

2. HYPOTHESES
   Identify plausible explanations suggested by the observations.
   Do not present hypotheses as facts.

3. TESTING
   Use the available tools to test relevant hypotheses.
   Explain what evidence supports, weakens, or fails to establish each hypothesis.

4. CONCLUSION
   State the conclusion that is supported by the available evidence.
   Distinguish correlation or temporal overlap from proven causation.

5. CONFIDENCE AND LIMITATIONS
   State your confidence in the conclusion and identify important evidence
   that is missing or could not be tested.

Important rules:
- Do not claim causation unless the retrieved evidence directly supports it.
- Do not invent evidence, events, dependencies, or system behavior.
- Clearly distinguish observed facts from inferences.
- Unsupported possibilities must be explicitly labeled as unverified.
- If a hypothesis cannot be tested with the available tools or evidence,
  say so rather than treating it as confirmed.
- Do not present an unverified possibility as the likely root cause.
""",
callback_handler=silent_callback,
)


if __name__ == "__main__":
    question = input(
        "What would you like to investigate? "
    )

    response = agent(question)

    print("\n=== IncidentLens Investigation ===\n")
    print(response)
