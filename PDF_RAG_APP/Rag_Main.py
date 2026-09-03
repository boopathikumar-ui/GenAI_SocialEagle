# ============================================================
# RAG PDF Question Answering App
# Technologies:
# Python + LangChain + Streamlit + FAISS + OpenAI
# ============================================================

import os

import streamlit as st
from dotenv import load_dotenv

# PDF loading
from langchain_community.document_loaders import PyPDFLoader

# Text splitting
from langchain_text_splitters import RecursiveCharacterTextSplitter

# FAISS vector database
from langchain_community.vectorstores import FAISS

# OpenAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

# LangChain prompt
from langchain_core.prompts import ChatPromptTemplate


# ============================================================
# 1. LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ============================================================
# 2. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PDF RAG Assistant",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# 3. PAGE TITLE
# ============================================================

st.title("📄 PDF RAG Assistant")

st.write(
    "Upload a PDF and ask questions about its contents."
)


# ============================================================
# 4. CHECK API KEY
# ============================================================

if not OPENAI_API_KEY:

    st.error(
        "OPENAI_API_KEY was not found. "
        "Please add it to your .env file."
    )

    st.stop()


# ============================================================
# 5. CREATE SESSION STATE
# ============================================================
#
# Streamlit reruns the Python file whenever the user interacts
# with the application.
#
# We use session_state to remember the vector database and
# uploaded PDF between reruns.
# ============================================================

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = None


# ============================================================
# 6. PDF UPLOADER
# ============================================================

uploaded_file = st.file_uploader(
    "Upload your PDF",
    type=["pdf"]
)


# ============================================================
# 7. PROCESS PDF
# ============================================================

if uploaded_file is not None:

    # Check whether this is a new PDF
    new_file = (
        st.session_state.uploaded_file_name
        != uploaded_file.name
    )

    # Process only when a new PDF is uploaded
    if new_file:

        # Reset the previous vector database
        st.session_state.vector_store = None

        st.session_state.uploaded_file_name = (
            uploaded_file.name
        )

        # ----------------------------------------------------
        # Processing status
        # ----------------------------------------------------

        with st.status(
            "Processing your PDF...",
            expanded=True
        ) as status:

            # ------------------------------------------------
            # STEP 1: Save uploaded PDF temporarily
            # ------------------------------------------------

            st.write("📄 Reading PDF...")

            pdf_path = "uploaded_file.pdf"

            with open(pdf_path, "wb") as file:

                file.write(
                    uploaded_file.getbuffer()
                )


            # ------------------------------------------------
            # STEP 2: Load PDF
            # ------------------------------------------------

            st.write("📖 Loading PDF pages...")

            loader = PyPDFLoader(pdf_path)

            documents = loader.load()


            # ------------------------------------------------
            # STEP 3: Check whether PDF contains text
            # ------------------------------------------------

            full_text = ""

            for document in documents:

                full_text += document.page_content.strip()


            if not full_text:

                status.update(
                    label="❌ PDF processing failed",
                    state="error"
                )

                st.error(
                    "This PDF does not contain readable text. "
                    "It may be a scanned/image-only PDF."
                )

                st.stop()


            # ------------------------------------------------
            # STEP 4: Split text into chunks
            # ------------------------------------------------

            st.write("✂️ Splitting PDF into chunks...")

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )

            chunks = text_splitter.split_documents(
                documents
            )


            st.write(
                f"Created {len(chunks)} text chunks."
            )


            # ------------------------------------------------
            # STEP 5: Create embeddings
            # ------------------------------------------------

            st.write(
                "🧠 Creating embeddings using OpenAI..."
            )

            embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small"
            )


            # ------------------------------------------------
            # STEP 6: Store embeddings in FAISS
            # ------------------------------------------------

            st.write(
                "🗄️ Building FAISS vector database..."
            )

            vector_store = FAISS.from_documents(
                chunks,
                embeddings
            )


            # ------------------------------------------------
            # STEP 7: Store vector database in session
            # ------------------------------------------------

            st.session_state.vector_store = vector_store


            # ------------------------------------------------
            # Processing completed
            # ------------------------------------------------

            status.update(
                label="✅ PDF is ready!",
                state="complete"
            )


        # Remove temporary PDF
        if os.path.exists(pdf_path):

            os.remove(pdf_path)


# ============================================================
# 8. CHECK WHETHER VECTOR DATABASE IS READY
# ============================================================

if st.session_state.vector_store is not None:

    st.success(
        f"✅ **{st.session_state.uploaded_file_name}** "
        "is ready for questions."
    )


    # ========================================================
    # 9. QUESTION INPUT
    # ========================================================

    question = st.text_input(
        "Ask a question about your PDF:",
        placeholder="Example: What is this document about?"
    )


    # ========================================================
    # 10. ASK QUESTION
    # ========================================================

    if question:

        with st.spinner("🔎 Searching the PDF..."):

            # ------------------------------------------------
            # Retrieve relevant chunks
            # ------------------------------------------------

            retriever = (
                st.session_state.vector_store
                .as_retriever(
                    search_kwargs={
                        "k": 4
                    }
                )
            )

            relevant_documents = retriever.invoke(
                question
            )


        # ====================================================
        # 11. CREATE CONTEXT
        # ====================================================

        context = "\n\n".join(
            document.page_content
            for document in relevant_documents
        )


        # ====================================================
        # 12. CREATE PROMPT
        # ====================================================

        prompt = ChatPromptTemplate.from_template(
            """
You are a helpful assistant answering questions
about a user's PDF.

Answer the question using ONLY the information
provided in the context below.

If the answer cannot be found in the context,
say:

"I couldn't find the answer in the uploaded PDF."

Do not make up information.

Context:
{context}

Question:
{question}

Answer:
"""
        )


        # ====================================================
        # 13. CREATE OPENAI CHAT MODEL
        # ====================================================

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )


        # ====================================================
        # 14. SEND QUESTION TO OPENAI
        # ====================================================

        final_prompt = prompt.invoke(
            {
                "context": context,
                "question": question
            }
        )

        response = llm.invoke(
            final_prompt
        )


        # ====================================================
        # 15. DISPLAY ANSWER
        # ====================================================

        st.subheader("🤖 Answer")

        st.write(
            response.content
        )


        # ====================================================
        # 16. SHOW SOURCE CHUNKS
        # ====================================================

        with st.expander(
            "📚 View source information"
        ):

            for index, document in enumerate(
                relevant_documents
            ):

                st.markdown(
                    f"**Source {index + 1}**"
                )

                st.write(
                    document.page_content
                )

                st.divider()


# ============================================================
# 17. WAITING MESSAGE
# ============================================================

else:

    st.info(
        "👆 Upload a PDF to start."
    )