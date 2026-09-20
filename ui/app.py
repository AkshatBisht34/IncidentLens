import streamlit as st

from agent.investigator import agent


st.set_page_config(
    page_title="IncidentLens",
    page_icon="🔎",
    layout="wide",
)


# -----------------------------
# Page styling
# -----------------------------

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 0;
    }

    .subtitle {
        font-size: 18px;
        color: #777;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 600;
        margin-top: 25px;
    }

    .confidence {
        font-size: 28px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------
# Header
# -----------------------------

st.markdown(
    '<div class="main-title">🔎 IncidentLens</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Evidence-driven production incident investigation"
    "</div>",
    unsafe_allow_html=True,
)


# -----------------------------
# Incident input
# -----------------------------

col1, col2 = st.columns([1, 3])

with col1:
    service = st.selectbox(
        "Service",
        ["payment-api"],
    )

with col2:
    question = st.text_input(
        "What would you like to investigate?",
        value=f"Why is {service} failing?",
    )


investigate = st.button(
    "🔍 Investigate Incident",
    type="primary",
    use_container_width=True,
)


# -----------------------------
# Investigation
# -----------------------------

if investigate:

    if not question.strip():
        st.warning("Please enter an investigation question.")
        st.stop()

    st.divider()

    st.markdown(
        '<div class="section-title">Investigation</div>',
        unsafe_allow_html=True,
    )

    with st.spinner("Collecting evidence and investigating..."):

        try:
            response = agent(question)

        except Exception as error:
            st.error(
                "Investigation failed. "
                "Check that Ollama and OpenSearch are running."
            )

            st.exception(error)
            st.stop()

    # Convert Strands response to text.
    result = str(response)

    # ---------------------------------
    # Display the agent's investigation
    # ---------------------------------

    st.markdown(result)

    st.divider()

    st.caption(
        "IncidentLens conclusions are generated from telemetry retrieved "
        "from the current production evidence store."
    )
