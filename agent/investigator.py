from strands import Agent, tool
from strands.models.ollama import OllamaModel

from evidence.collector import EvidenceCollector
from evidence.correlator import correlate_latency_and_failures


# Shared evidence collector.
collector = EvidenceCollector()


def silent_callback(*args, **kwargs):
    pass

@tool
def get_recent_evidence(service: str, size: int = 8):
    """
    Retrieve recent telemetry records for a service from OpenSearch.
    """
    return collector.get_recent_evidence(
        service,
        size=size,
    )


@tool
def get_failure_evidence(service: str, size: int = 8):
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
    size: int = 8,
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
def get_timeline(service: str, size: int = 12):
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
    size: int = 8,
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
    system_prompt = """
You are the IncidentLens incident investigation agent.

Investigate the user's question using ONLY evidence retrieved through the available tools.

Your job is to distinguish observed facts from hypotheses and conclusions.

IMPORTANT:
- Never claim causation from temporal correlation alone.
- Temporal overlap does NOT prove that one event caused another.
- Do not invent database, network, CPU, memory, dependency, or infrastructure problems.
- If the available telemetry cannot identify the root cause, explicitly say so.
- Hypotheses must be labeled as hypotheses.
- Use the correlation tool when latency and failures need to be compared.

Your final response MUST contain exactly these six sections:

OBSERVATIONS
HYPOTHESES
TESTING
CONCLUSION
CONFIDENCE
LIMITATIONS

Do not create any other headings.
Do not use headings such as Analysis, Root Cause, Recommendation, or Key Insight.

Keep each section concise.

OBSERVATIONS:
Only facts directly supported by retrieved evidence.

HYPOTHESES:
Possible explanations suggested by the observations.
Do not present them as confirmed facts.

TESTING:
Describe which tools/evidence were used to test the hypotheses and what they showed.

CONCLUSION:
State only what the evidence supports.
Do not claim causation unless directly established.

CONFIDENCE:
Give High, Medium, or Low confidence and briefly explain why.

LIMITATIONS:
State what important information is unavailable.

Example format:

OBSERVATIONS
- ...

HYPOTHESES
- ...

TESTING
- ...

CONCLUSION
...

CONFIDENCE
Medium — ...

LIMITATIONS
- ...
Your final response MUST be valid JSON.

Use exactly this structure:

{
  "observations": [
    "fact supported by evidence"
  ],
  "hypotheses": [
    "possible explanation"
  ],
  "testing": [
    "test performed and result"
  ],
  "conclusion": "evidence-supported conclusion",
  "confidence": "Medium",
  "limitations": [
    "important missing evidence"
  ]
}

Rules:

- Return JSON only.
- Do not use Markdown.
- Do not add extra fields.
- observations must contain facts from retrieved evidence.
- hypotheses must be explicitly uncertain.
- testing must describe evidence actually retrieved or correlation actually performed.
- conclusion must not claim causation from temporal correlation alone.
- confidence must be High, Medium, or Low.
- limitations must identify missing evidence.
""" ,
callback_handler=silent_callback,
)


if __name__ == "__main__":
    question = input(
        "What would you like to investigate? "
    )

    response = agent(question)

    print("\n=== IncidentLens Investigation ===\n")
    print(response)
