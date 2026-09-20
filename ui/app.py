import sys
from pathlib import Path
from response_parser import validate_and_repair_response

# ---------------------------------------------------------
# Make the IncidentLens project root importable
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# Imports
# ---------------------------------------------------------

import streamlit as st

from agent.investigator import agent
from evidence.collector import EvidenceCollector


# ---------------------------------------------------------
# Page configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="IncidentLens",
    page_icon="🔎",
    layout="wide",
)


# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------

if "investigation_result" not in st.session_state:
    st.session_state.investigation_result = None

if "question" not in st.session_state:
    st.session_state.question = ""


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def get_latest_evidence(service="payment-api"):
    """
    Retrieve a small amount of real telemetry from OpenSearch
    so the UI can display evidence alongside the investigation.
    """

    try:
        collector = EvidenceCollector()

        recent = collector.get_recent_evidence(
            service=service,
            size=10,
        )

        failures = collector.get_failure_evidence(
            service=service,
            size=10,
        )

        latency = collector.get_latency_evidence(
            service=service,
            min_latency_ms=1000,
            size=10,
        )

        return {
            "recent": recent,
            "failures": failures,
            "latency": latency,
        }

    except Exception as error:
        return {
            "error": str(error),
        }


def response_to_text(response):
    """
    Convert the Strands response into text that Streamlit
    can display.

    Strands responses may not be plain strings, so converting
    explicitly prevents UI errors.
    """

    try:
        return str(response)
    except Exception:
        return "Unable to display investigation response."


def extract_section(text, section_name, next_sections):
    """
    Extract one section from the structured agent response.

    Example:

    OBSERVATIONS
    ...
    HYPOTHESES
    ...

    returns only the OBSERVATIONS content.
    """

    upper_text = text.upper()

    start_marker = section_name.upper()

    start = upper_text.find(start_marker)

    if start == -1:
        return "No information returned."

    start += len(start_marker)

    end = len(text)

    for next_section in next_sections:
        position = upper_text.find(
            next_section.upper(),
            start,
        )

        if position != -1 and position < end:
            end = position

    result = text[start:end].strip()

    if not result:
        return "No information returned."

    return result


def parse_investigation(text):
    """
    Convert the agent's structured text response into
    separate UI sections.
    """

    observations = extract_section(
        text,
        "OBSERVATIONS",
        [
            "HYPOTHESES",
            "TESTING",
            "CONCLUSION",
            "CONFIDENCE AND LIMITATIONS",
        ],
    )

    hypotheses = extract_section(
        text,
        "HYPOTHESES",
        [
            "TESTING",
            "CONCLUSION",
            "CONFIDENCE AND LIMITATIONS",
        ],
    )

    testing = extract_section(
        text,
        "TESTING",
        [
            "CONCLUSION",
            "CONFIDENCE AND LIMITATIONS",
        ],
    )

    conclusion = extract_section(
        text,
        "CONCLUSION",
        [
            "CONFIDENCE AND LIMITATIONS",
        ],
    )

    confidence = extract_section(
        text,
        "CONFIDENCE AND LIMITATIONS",
        [],
    )

    return {
        "observations": observations,
        "hypotheses": hypotheses,
        "testing": testing,
        "conclusion": conclusion,
        "confidence": confidence,
    }


# =========================================================
# SCREEN 1
# =========================================================

if st.session_state.investigation_result is None:

    st.title("🔎 IncidentLens")

    st.subheader("Evidence-based incident investigation")

    st.write(
        "Investigate production incidents using telemetry, "
        "OpenSearch evidence, correlation, and an AI investigation agent."
    )

    st.divider()

    # -----------------------------------------------------
    # Production status
    # -----------------------------------------------------

    st.subheader("Production Environment")

    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        st.metric(
            "Service",
            "payment-api",
        )

    with status_col2:
        st.metric(
            "Telemetry",
            "Live",
        )

    with status_col3:
        st.metric(
            "Evidence Store",
            "OpenSearch",
        )

    st.divider()

    # -----------------------------------------------------
    # Incident question
    # -----------------------------------------------------

    st.subheader("Investigate an Incident")

    question = st.text_area(
        "What would you like to investigate?",
        value=st.session_state.question,
        placeholder="Example: Why is payment-api failing?",
        height=100,
    )

    st.session_state.question = question

    st.write("")

    if st.button(
        "🔍 Investigate Incident",
        type="primary",
        use_container_width=True,
    ):

        if not question.strip():
            st.warning(
                "Please enter an incident question first."
            )

        else:

            with st.spinner(
                "IncidentLens is collecting evidence and investigating..."
            ):

                try:

                # -------------------------------------
                # Run the Strands investigation agent
                # -------------------------------------

                    response = agent(question)

                # Convert Strands response to plain text
                    result_text = response_to_text(response)

                # -------------------------------------
                # Validate / repair the agent response
                # -------------------------------------

                    try:
                        repaired_response = validate_and_repair_response(result_text)
                    except Exception as error:
                        st.error("The investigation response could not be repaired.")
                        st.exception(error)
                        st.stop()


                    # -------------------------------------
                    # Retrieve supporting evidence
                    # -------------------------------------

                    evidence = get_latest_evidence(
                        service="payment-api"
                    )

                    st.session_state.investigation_result = {
                        "question": question,
                        "response": result_text,
                        "sections": parse_investigation(
                            result_text
                        ),
                        "evidence": evidence,
                    }

                    st.rerun()

                except Exception as error:

                    st.error(
                        "IncidentLens could not complete the investigation."
                    )

                    st.exception(error)


# =========================================================
# SCREEN 2
# =========================================================

else:

    result = st.session_state.investigation_result

    st.title("🔎 IncidentLens Investigation")

    st.caption(
        f"Question: {result['question']}"
    )

    st.divider()

    # -----------------------------------------------------
    # Incident status
    # -----------------------------------------------------

    status_col1, status_col2, status_col3 = st.columns(3)

    with status_col1:
        st.metric(
            "Service",
            "payment-api",
        )

    with status_col2:
        st.metric(
            "Status",
            "🔴 Investigating",
        )

    with status_col3:
        st.metric(
            "Evidence",
            "OpenSearch",
        )

    st.divider()

    sections = result["sections"]

    # -----------------------------------------------------
    # Observations
    # -----------------------------------------------------

    st.subheader("1. Observations")
    st.write(sections["observations"])

    # -----------------------------------------------------
    # Hypotheses
    # -----------------------------------------------------

    st.subheader("2. Hypotheses")
    st.write(sections["hypotheses"])

    # -----------------------------------------------------
    # Testing
    # -----------------------------------------------------

    st.header("3. Testing")
    st.write(sections["testing"])

    # -----------------------------------------------------
    # Conclusion
    # -----------------------------------------------------

    st.subheader("4. Conclusion")

    st.write(sections["conclusion"])

    # -----------------------------------------------------
    # Confidence
    # -----------------------------------------------------

    st.subheader("5. Confidence")

    st.write(sections["confidence"])

    st.divider()

    # =====================================================
    # Evidence
    # =====================================================

    st.header("📊 Retrieved Evidence")

    evidence = result["evidence"]

    if "error" in evidence:

        st.error(
            f"Could not retrieve evidence: {evidence['error']}"
        )

    else:

        recent = evidence["recent"]
        failures = evidence["failures"]
        latency = evidence["latency"]

        # ---------------------------------------------
        # Evidence metrics
        # ---------------------------------------------

        evidence_col1, evidence_col2, evidence_col3 = st.columns(3)

        with evidence_col1:
            st.metric(
                "Recent Records",
                len(recent),
            )

        with evidence_col2:
            st.metric(
                "Failures",
                len(failures),
            )

        with evidence_col3:
            st.metric(
                "High Latency",
                len(latency),
            )

        st.write("")

        # ---------------------------------------------
        # Evidence tabs
        # ---------------------------------------------

        tab1, tab2, tab3 = st.tabs(
            [
                "Recent Evidence",
                "Failures",
                "High Latency",
            ]
        )

        with tab1:

            if recent:
                st.dataframe(
                    recent,
                    use_container_width=True,
                )
            else:
                st.info(
                    "No recent evidence found."
                )

        with tab2:

            if failures:
                st.dataframe(
                    failures,
                    use_container_width=True,
                )
            else:
                st.info(
                    "No failure evidence found."
                )

        with tab3:

            if latency:
                st.dataframe(
                    latency,
                    use_container_width=True,
                )
            else:
                st.info(
                    "No high-latency evidence found."
                )

    st.divider()

    # -----------------------------------------------------
    # Raw agent response
    # -----------------------------------------------------

    with st.expander(
        "View raw investigation response"
    ):

        st.text(
            result["response"]
        )

    st.write("")

    # -----------------------------------------------------
    # New investigation
    # -----------------------------------------------------

    if st.button(
        "← Start New Investigation",
        use_container_width=True,
    ):

        st.session_state.investigation_result = None
        st.session_state.question = ""

        st.rerun()

