from fastapi import FastAPI

from services.pdf_service import read_pdf
from services.chunk_service import split_text
from services.embedding_service import create_embeddings
from services.vector_service import create_vector_store, search_vector_store
from services.graph_service import (
    test_connection,
    create_test_node,
    create_chunk_graph,
    search_graph
)
from services.hybrid_service import hybrid_search
from services.llm_service import generate_answer
from services.guardrail_service import apply_guardrails


app = FastAPI(
    title="Hybrid RAG API",
    description="Backend API for the Hybrid RAG Buildathon application",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Hybrid RAG Backend is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/pdf")
def pdf_test():
    text = read_pdf()

    return {
        "status": "success",
        "characters": len(text),
        "preview": text[:500]
    }


@app.get("/chunks")
def chunks_test():
    text = read_pdf()

    chunks = split_text(text)

    return {
        "status": "success",
        "total_chunks": len(chunks),
        "first_chunk": chunks[0] if chunks else "",
        "second_chunk": chunks[1] if len(chunks) > 1 else ""
    }


@app.get("/embedding-test")
def embedding_test():
    embeddings = create_embeddings()

    test_text = "This is a test sentence for embeddings."

    vector = embeddings.embed_query(test_text)

    return {
        "status": "success",
        "vector_length": len(vector),
        "first_5_values": vector[:5]
    }


@app.get("/vector-test")
def vector_test():
    text = read_pdf()

    chunks = split_text(text)

    embeddings = create_embeddings()

    vector_store = create_vector_store(
        chunks,
        embeddings
    )

    return {
        "status": "success",
        "total_chunks": len(chunks),
        "message": "FAISS vector store created successfully"
    }


@app.get("/search")
def search_test(query: str):
    embeddings = create_embeddings()

    results = search_vector_store(
        query,
        embeddings,
        k=3
    )

    return {
        "status": "success",
        "query": query,
        "results": [
            result.page_content
            for result in results
        ]
    }


@app.get("/neo4j-test")
def neo4j_test():
    message = test_connection()

    return {
        "status": "success",
        "message": message
    }


@app.get("/neo4j-create-test")
def neo4j_create_test():
    name = create_test_node()

    return {
        "status": "success",
        "message": "Test node created successfully",
        "name": name
    }


@app.get("/neo4j-create-chunks")
def neo4j_create_chunks():
    text = read_pdf()

    chunks = split_text(text)

    total_chunks = create_chunk_graph(chunks)

    return {
        "status": "success",
        "total_chunks": total_chunks,
        "message": "PDF chunks stored in Neo4j successfully"
    }


@app.get("/graph-search")
def graph_search_test(query: str):
    results = search_graph(
        query,
        k=3
    )

    return {
        "status": "success",
        "query": query,
        "results": results
    }


@app.get("/hybrid-search")
def hybrid_search_test(query: str):
    embeddings = create_embeddings()

    results = hybrid_search(
        query,
        embeddings,
        k=3
    )

    return {
        "status": "success",
        "query": query,
        "results": results
    }


@app.get("/ask")
def ask_question(query: str):

    # Step 1: Create embeddings
    embeddings = create_embeddings()

    # Step 2: Hybrid retrieval
    results = hybrid_search(
        query,
        embeddings,
        k=3
    )

    # Step 3: Build context
    context = "\n\n".join(
        result["text"]
        for result in results
    )

    # Step 4: Generate answer using GPT-4o-mini
    answer = generate_answer(
        query,
        context
    )

    # Step 5: Apply guardrails
    guardrail_result = apply_guardrails(
        answer,
        context
    )

    # Step 6: Return final response
    return {
        "status": "success",
        "query": query,
        "answer": guardrail_result["answer"],
        "guardrail_allowed": guardrail_result["allowed"],
        "sources": results
    }