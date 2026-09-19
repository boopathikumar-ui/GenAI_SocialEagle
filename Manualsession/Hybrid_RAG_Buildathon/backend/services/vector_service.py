from pathlib import Path

from langchain_community.vectorstores import FAISS


VECTORSTORE_PATH = Path(__file__).resolve().parents[2] / "vectorstore"


def create_vector_store(chunks, embeddings):
    vector_store = FAISS.from_texts(
        texts=chunks,
        embedding=embeddings
    )

    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)

    vector_store.save_local(VECTORSTORE_PATH)

    return vector_store


def load_vector_store(embeddings):
    vector_store = FAISS.load_local(
        VECTORSTORE_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )

    return vector_store


def search_vector_store(query, embeddings, k=3):
    vector_store = load_vector_store(embeddings)

    results = vector_store.similarity_search(
        query,
        k=k
    )

    return results