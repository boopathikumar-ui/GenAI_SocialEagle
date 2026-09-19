from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()


def create_embeddings():
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small"
    )

    return embeddings