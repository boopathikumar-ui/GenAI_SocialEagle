from services.vector_service import search_vector_store
from services.graph_service import search_graph


def hybrid_search(query, embeddings, k=3):
    # Search using FAISS
    vector_results = search_vector_store(
        query,
        embeddings,
        k=k
    )

    # Search using Neo4j
    graph_results = search_graph(
        query,
        k=k
    )

    # Prepare combined results
    combined_results = []

    # Add FAISS results
    for result in vector_results:
        combined_results.append({
            "source": "FAISS",
            "text": result.page_content
        })

    # Add Neo4j results
    for result in graph_results:
        combined_results.append({
            "source": "Neo4j",
            "text": result["text"]
        })

    return combined_results