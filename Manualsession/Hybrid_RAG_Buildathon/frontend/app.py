
import streamlit as st
import requests

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Spotify Architecture - Hybrid RAG",
    page_icon="🎵",
    layout="wide"
)

# ============================================================
# BACKEND CONFIGURATION
# ============================================================

BACKEND_URL = "http://127.0.0.1:8000"

# ============================================================
# HEADER
# ============================================================

st.title("🎵 Spotify Architecture — Hybrid RAG Assistant")

st.markdown(
    """
    ### Ask questions about the application architecture

    This AI assistant uses **Hybrid RAG** with:

    - 🔎 **FAISS** — Vector Search
    - 🕸️ **Neo4j** — Knowledge Graph Search
    - 🤖 **GPT-4o-mini** — Answer Generation
    - 🛡️ **Guardrails** — Prevent unsupported answers
    """
)

st.info(
    "📄 Answers are generated only from the provided "
    "Spotify-like architecture document."
)

# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("🏗️ RAG Architecture")

    st.markdown(
        """
        **PDF Document**

        ↓

        **Text Chunks**

        ↓

        **FAISS + Neo4j**

        ↓

        **Hybrid Retrieval**

        ↓

        **GPT-4o-mini**

        ↓

        **Guardrails**

        ↓

        **Final Answer**
        """
    )

    st.divider()

    st.caption("Hybrid RAG Buildathon")
    st.caption("FastAPI + Streamlit + LangChain")

# ============================================================
# QUESTION INPUT
# ============================================================

st.subheader("💬 Ask Your Question")

query = st.text_input(
    "Enter your question",
    placeholder="Example: What databases are used in the application?"
)

# ============================================================
# ASK BUTTON
# ============================================================

if st.button("🚀 Ask", type="primary"):

    if not query.strip():

        st.warning("⚠️ Please enter a question.")

    else:

        with st.spinner(
            "🔎 Searching FAISS and Neo4j and generating answer..."
        ):

            try:

                response = requests.get(
                    f"{BACKEND_URL}/ask",
                    params={"query": query},
                    timeout=120
                )

                response.raise_for_status()

                data = response.json()

                # ====================================================
                # DISPLAY ANSWER
                # ====================================================

                st.markdown("## 🤖 Answer")

                st.write(data["answer"])

                # ====================================================
                # GUARDRAIL STATUS
                # ====================================================

                if data["guardrail_allowed"]:

                    st.success(
                        "✅ Answer passed the guardrails."
                    )

                else:

                    st.warning(
                        "⚠️ This question could not be answered "
                        "from the provided document."
                    )

                # ====================================================
                # DISPLAY SOURCES
                # ====================================================

                st.subheader("📚 Retrieved Sources")

                sources = data.get("sources", [])

                if sources:

                    for index, source in enumerate(
                        sources,
                        start=1
                    ):

                        source_name = source.get(
                            "source",
                            "Unknown"
                        )

                        source_text = source.get(
                            "text",
                            ""
                        )

                        with st.expander(
                            f"📄 Source {index} — {source_name}"
                        ):

                            st.write(source_text)

                else:

                    st.info(
                        "No retrieval sources were returned."
                    )

            # ====================================================
            # ERROR HANDLING
            # ====================================================

            except requests.exceptions.ConnectionError:

                st.error(
                    """
                    ❌ Could not connect to the FastAPI backend.

                    Make sure the backend is running at:

                    http://127.0.0.1:8000
                    """
                )

            except requests.exceptions.Timeout:

                st.error(
                    "❌ The request took too long. "
                    "Please try again."
                )

            except requests.exceptions.HTTPError as e:

                st.error(
                    f"❌ Backend returned an HTTP error: {e}"
                )

            except requests.exceptions.RequestException as e:

                st.error(
                    f"❌ Backend request failed: {e}"
                )

            except Exception as e:

                st.error(
                    f"❌ Unexpected error: {e}"
                )

# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "🎵 Hybrid RAG Buildathon | "
    "FAISS + Neo4j + GPT-4o-mini + FastAPI + Streamlit"
)

