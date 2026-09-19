from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def create_llm():
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0
    )

    return llm


def generate_answer(query, context):
    llm = create_llm()

    prompt = f"""
You are an AI assistant answering questions about a Spotify-like web application architecture.

Answer the user's question using only the provided context.

If the answer is not available in the context, say:
"I don't have enough information in the provided document."

Do not make up information.

Context:
{context}

User Question:
{query}

Answer:
"""

    response = llm.invoke(prompt)

    return response.content