import json
import re


REQUIRED_FIELDS = [
    "observations",
    "hypotheses",
    "testing",
    "conclusion",
    "confidence",
    "limitations",
]


def _normalize(value):
    """Convert a section into a predictable list/string format."""

    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return []

        # Turn simple bullet lists into list items.
        lines = value.splitlines()

        items = []
        for line in lines:
            line = re.sub(r"^\s*[-*•]\s*", "", line).strip()
            if line:
                items.append(line)

        return items if len(items) > 1 else [value]

    return [str(value)]


def _extract_json(text):
    """Extract JSON even if Qwen wrapped it in markdown."""

    text = str(text).strip()

    # Direct JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # JSON inside ```json ... ```
    match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL,
    )

    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Find first {...} block
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def validate_and_repair_response(response):
    """
    Convert the investigator's response into the structure
    expected by the Streamlit UI.
    """

    data = _extract_json(response)

    # Qwen returned something that wasn't JSON.
    if not isinstance(data, dict):
        return {
            "observations": [],
            "hypotheses": [],
            "testing": [],
            "conclusion": "The investigation agent returned an invalid response.",
            "confidence": "Low",
            "limitations": [
                "The investigation response could not be parsed as JSON."
            ],
        }

    repaired = {}

    for field in REQUIRED_FIELDS:
        repaired[field] = data.get(field)

    # Normalize list-based sections.
    for field in [
        "observations",
        "hypotheses",
        "testing",
        "limitations",
    ]:
        repaired[field] = _normalize(repaired[field])

    # Normalize single-value sections.
    repaired["conclusion"] = (
        str(repaired["conclusion"]).strip()
        if repaired["conclusion"]
        else "No supported conclusion was returned."
    )

    repaired["confidence"] = (
        str(repaired["confidence"]).strip()
        if repaired["confidence"]
        else "Low"
    )

    return repaired
