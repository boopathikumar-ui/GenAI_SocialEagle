import os
import re
import certifi
import requests
import streamlit as st

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from neo4j import GraphDatabase

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

# Fix SSL certificate verification for Neo4j
os.environ["SSL_CERT_FILE"] = certifi.where()


# ============================================================
# 2. CONFIGURATION
# ============================================================

GOVERNMENT_URL = "https://www.tn.gov.in/scheme_list.php?dep_id=Mg=="

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")


# ============================================================
# 3. CHECK ENVIRONMENT VARIABLES
# ============================================================

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY is missing in .env")

if not NEO4J_URI:
    st.error("NEO4J_URI is missing in .env")

if not NEO4J_USERNAME:
    st.error("NEO4J_USERNAME is missing in .env")

if not NEO4J_PASSWORD:
    st.error("NEO4J_PASSWORD is missing in .env")

if not NEO4J_DATABASE:
    st.error("NEO4J_DATABASE is missing in .env")


# ============================================================
# 4. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Tamil Nadu Government Scheme Assistant",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ Tamil Nadu Government Scheme Assistant")

st.write(
    "Ask questions about Tamil Nadu Government schemes. "
    "Answers are generated using FAISS, Neo4j and GPT-4o-mini."
)


# ============================================================
# 5. CREATE NEO4J DRIVER
# ============================================================

@st.cache_resource
def create_neo4j_driver():

    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
    )

    # Verify connection
    driver.verify_connectivity()

    return driver


# ============================================================
# 6. LOAD GOVERNMENT WEBSITE
# ============================================================

def load_government_website():

    response = requests.get(
        GOVERNMENT_URL,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    # Remove unnecessary HTML
    for element in soup(
        ["script", "style", "noscript"]
    ):
        element.decompose()

    text = soup.get_text(
        separator="\n"
    )

    # Clean blank lines
    lines = []

    for line in text.splitlines():

        line = line.strip()

        if line:
            lines.append(line)

    clean_text = "\n".join(lines)

    return clean_text


# ============================================================
# 7. SPLIT TEXT INTO CHUNKS
# ============================================================

def create_chunks(text):

    document = Document(
        page_content=text,
        metadata={
            "source": GOVERNMENT_URL
        }
    )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )

    chunks = splitter.split_documents(
        [document]
    )

    return chunks


# ============================================================
# 8. BUILD FAISS VECTOR DATABASE
# ============================================================

def build_faiss(chunks):

    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=OPENAI_API_KEY
    )

    vector_db = FAISS.from_documents(
        chunks,
        embeddings
    )

    return vector_db


# ============================================================
# 9. BUILD NEO4J KNOWLEDGE GRAPH
# ============================================================

def build_knowledge_graph(chunks):

    driver = create_neo4j_driver()

    with driver.session(
        database=NEO4J_DATABASE
    ) as session:

        # Clear previous graph
        session.run(
            "MATCH (n) DETACH DELETE n"
        )

        # Create Government node
        session.run(
            """
            CREATE (:Government {
                name: 'Tamil Nadu Government'
            })
            """
        )

        # Create scheme nodes
        for index, chunk in enumerate(chunks):

            text = chunk.page_content

            session.run(
                """
                MATCH (g:Government)
                CREATE (s:Scheme {
                    id: $id,
                    text: $text
                })
                CREATE (g)-[:HAS_SCHEME]->(s)
                """,
                id=str(index),
                text=text
            )


# ============================================================
# 10. NEO4J KEYWORD SEARCH
# ============================================================

def neo4j_search(query):

    driver = create_neo4j_driver()

    results = []

    # Convert question into keywords
    keywords = re.findall(
        r"\b\w+\b",
        query.lower()
    )

    with driver.session(
        database=NEO4J_DATABASE
    ) as session:

        records = session.run(
            """
            MATCH (s:Scheme)
            RETURN s.text AS text
            """
        )

        for record in records:

            text = record["text"]

            text_lower = text.lower()

            # Count keyword matches
            match_count = 0

            for keyword in keywords:

                if len(keyword) > 2 and keyword in text_lower:
                    match_count += 1

            if match_count > 0:

                results.append(
                    (
                        match_count,
                        text
                    )
                )

    # Highest matching chunks first
    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return [
        text
        for score, text in results[:5]
    ]


# ============================================================
# 11. HYBRID RETRIEVAL
# ============================================================

def hybrid_search(query, vector_db):

    # --------------------------------------------------------
    # FAISS semantic search
    # --------------------------------------------------------

    faiss_docs = vector_db.similarity_search(
        query,
        k=5
    )

    faiss_results = [
        doc.page_content
        for doc in faiss_docs
    ]

    # --------------------------------------------------------
    # Neo4j keyword search
    # --------------------------------------------------------

    neo4j_results = neo4j_search(
        query
    )

    # --------------------------------------------------------
    # Combine results
    # --------------------------------------------------------

    combined = []

    for text in faiss_results + neo4j_results:

        if text not in combined:

            combined.append(text)

    return combined


# ============================================================
# 12. INPUT GUARDRAIL
# ============================================================

def input_guardrail(question):

    if not question:
        return False

    if len(question.strip()) < 3:
        return False

    return True


# ============================================================
# 13. OUTPUT GUARDRAIL
# ============================================================

def output_guardrail(answer):

    if not answer:
        return False

    answer_lower = answer.lower()

    blocked_phrases = [
        "i could not find this information",
        "i couldn't find this information",
        "information is not available"
    ]

    for phrase in blocked_phrases:

        if phrase in answer_lower:
            return False

    if len(answer.strip()) < 20:
        return False

    return True


# ============================================================
# 14. GENERATE RAG ANSWER
# ============================================================

def generate_answer(question, context):

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=OPENAI_API_KEY
    )

    context_text = "\n\n".join(
        context
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
You are a Tamil Nadu Government scheme assistant.

Answer the user's question ONLY using the
provided government scheme context.

Do not invent information.

If the answer cannot be found in the context,
say exactly:

I could not find this information in the Tamil Nadu Government scheme data.

Keep the answer clear and concise.
"""
            ),
            (
                "human",
                """
Government Scheme Context:

{context}

Question:

{question}
"""
            )
        ]
    )

    chain = prompt | llm

    response = chain.invoke(
        {
            "context": context_text,
            "question": question
        }
    )

    return response.content


# ============================================================
# 15. IMPROVED EVALUATION
# ============================================================

def evaluate_answer(question, answer):

    if not answer:
        return "FAIL", "Empty answer"

    answer_lower = answer.lower().strip()

    # --------------------------------------------------------
    # Check whether chatbot explicitly says information
    # could not be found.
    # --------------------------------------------------------

    not_found_phrases = [
        "i could not find this information",
        "i couldn't find this information",
        "information is not available",
        "cannot find this information",
        "not found in the tamil nadu government scheme data"
    ]

    for phrase in not_found_phrases:

        if phrase in answer_lower:

            return (
                "FAIL",
                "The chatbot could not find relevant information."
            )

    # --------------------------------------------------------
    # Check answer length
    # --------------------------------------------------------

    if len(answer.strip()) < 50:

        return (
            "FAIL",
            "The answer is too short."
        )

    # --------------------------------------------------------
    # Check whether answer contains useful content
    # --------------------------------------------------------

    useful_indicators = [
        "scheme",
        "programme",
        "program",
        "training",
        "subsidy",
        "employment",
        "farmers",
        "youth",
        "benefit",
        "support",
        "government"
    ]

    indicator_found = False

    for word in useful_indicators:

        if word in answer_lower:

            indicator_found = True
            break

    if not indicator_found:

        return (
            "FAIL",
            "The answer does not appear to contain relevant scheme information."
        )

    # --------------------------------------------------------
    # If all checks passed
    # --------------------------------------------------------

    return (
        "PASS",
        "The answer contains relevant government scheme information."
    )


# ============================================================
# 16. EVALUATION QUESTIONS
# ============================================================

evaluation_questions = [

    "What government schemes are available?",

    "What is the purpose of the schemes?",

    "Who can benefit from the schemes?",

    "How can I apply for a government scheme?"
]


# ============================================================
# 17. SESSION STATE
# ============================================================

if "chunks" not in st.session_state:
    st.session_state.chunks = None

if "vector_db" not in st.session_state:
    st.session_state.vector_db = None


# ============================================================
# 18. SIDEBAR
# ============================================================

st.sidebar.header("⚙️ RAG Pipeline")

# ------------------------------------------------------------
# Button 1 - Load Website
# ------------------------------------------------------------

if st.sidebar.button(
    "1️⃣ Load Government Website"
):

    try:

        with st.spinner(
            "Loading Tamil Nadu Government website..."
        ):

            text = load_government_website()

            chunks = create_chunks(
                text
            )

            st.session_state.chunks = chunks

        st.sidebar.success(
            f"Website loaded successfully! "
            f"{len(chunks)} chunks created."
        )

    except Exception as e:

        st.sidebar.error(
            f"Error loading website: {e}"
        )


# ------------------------------------------------------------
# Button 2 - Build Knowledge Graph
# ------------------------------------------------------------

if st.sidebar.button(
    "2️⃣ Build Knowledge Graph"
):

    if st.session_state.chunks is None:

        st.sidebar.warning(
            "Please load the government website first."
        )

    else:

        try:

            with st.spinner(
                "Building Neo4j Knowledge Graph..."
            ):

                build_knowledge_graph(
                    st.session_state.chunks
                )

            st.sidebar.success(
                "Neo4j Knowledge Graph created successfully."
            )

        except Exception as e:

            st.sidebar.error(
                f"Neo4j error: {e}"
            )


# ------------------------------------------------------------
# Button 3 - Build FAISS Vector DB
# ------------------------------------------------------------

if st.sidebar.button(
    "3️⃣ Build FAISS Vector DB"
):

    if st.session_state.chunks is None:

        st.sidebar.warning(
            "Please load the government website first."
        )

    else:

        try:

            with st.spinner(
                "Creating FAISS Vector Database..."
            ):

                st.session_state.vector_db = build_faiss(
                    st.session_state.chunks
                )

            st.sidebar.success(
                "FAISS Vector Database created successfully."
            )

        except Exception as e:

            st.sidebar.error(
                f"FAISS error: {e}"
            )


# ------------------------------------------------------------
# Button 4 - Run Evaluation
# ------------------------------------------------------------

if st.sidebar.button(
    "4️⃣ Run Evaluation"
):

    if st.session_state.vector_db is None:

        st.sidebar.warning(
            "Please build the FAISS Vector Database first."
        )

    else:

        st.subheader("📊 Evaluation Results")

        for question in evaluation_questions:

            st.markdown(
                f"**Question:** {question}"
            )

            try:

                context = hybrid_search(
                    question,
                    st.session_state.vector_db
                )

                answer = generate_answer(
                    question,
                    context
                )

                result, reason = evaluate_answer(
                    question,
                    answer
                )

                if result == "PASS":

                    st.success(
                        f"Result: {result}"
                    )

                else:

                    st.error(
                        f"Result: {result}"
                    )

                st.markdown(
                    f"**Answer:** {answer}"
                )

                st.caption(
                    f"Evaluation: {reason}"
                )

            except Exception as e:

                st.error(
                    f"Evaluation error: {e}"
                )

            st.divider()


# ============================================================
# 19. CHAT INTERFACE
# ============================================================

st.subheader("💬 Ask about Tamil Nadu Government Schemes")

question = st.text_input(
    "Enter your question:"
)

if st.button("Ask"):

    # --------------------------------------------------------
    # Input guardrail
    # --------------------------------------------------------

    if not input_guardrail(question):

        st.warning(
            "Please enter a valid question."
        )

    # --------------------------------------------------------
    # Check FAISS
    # --------------------------------------------------------

    elif st.session_state.vector_db is None:

        st.warning(
            "Please build the FAISS Vector Database first."
        )

    else:

        try:

            with st.spinner(
                "Searching government scheme data..."
            ):

                # ------------------------------------------------
                # Hybrid retrieval
                # ------------------------------------------------

                context = hybrid_search(
                    question,
                    st.session_state.vector_db
                )

                # ------------------------------------------------
                # Generate answer
                # ------------------------------------------------

                answer = generate_answer(
                    question,
                    context
                )

            # ----------------------------------------------------
            # Output guardrail
            # ----------------------------------------------------

            if not output_guardrail(answer):

                st.info(
                    answer
                )

            else:

                st.subheader("🤖 Answer")

                st.write(
                    answer
                )

        except Exception as e:

            st.error(
                f"Error: {e}"
            )