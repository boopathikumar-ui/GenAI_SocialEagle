from dotenv import load_dotenv
from neo4j import GraphDatabase
import os


load_dotenv()


def get_driver():
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    driver = GraphDatabase.driver(
        uri,
        auth=(username, password)
    )

    return driver


def test_connection():
    driver = get_driver()

    try:
        with driver.session() as session:

            result = session.run(
                "RETURN 'Neo4j connection successful' AS message"
            )

            record = result.single()

            return record["message"]

    finally:
        driver.close()


def create_test_node():
    driver = get_driver()

    try:
        with driver.session() as session:

            result = session.run(
                """
                CREATE (n:TestDocument {
                    name: 'Spotify Architecture'
                })
                RETURN n.name AS name
                """
            )

            record = result.single()

            return record["name"]

    finally:
        driver.close()


def create_chunk_graph(chunks):
    driver = get_driver()

    try:
        with driver.session() as session:

            # Remove previous Document and Chunk data
            session.run(
                """
                MATCH (n:Document)
                DETACH DELETE n
                """
            )

            # Create main document node
            session.run(
                """
                CREATE (d:Document {
                    name: 'Spotify Architecture'
                })
                """
            )

            # Create chunk nodes
            for index, chunk in enumerate(chunks):

                session.run(
                    """
                    MATCH (d:Document {
                        name: 'Spotify Architecture'
                    })

                    CREATE (c:Chunk {
                        id: $id,
                        text: $text
                    })

                    CREATE (d)-[:HAS_CHUNK]->(c)
                    """,
                    parameters={
                        "id": index + 1,
                        "text": chunk
                    }
                )

        return len(chunks)

    finally:
        driver.close()


def search_graph(search_text, k=3):
    driver = get_driver()

    try:
        # Convert question into individual words
        words = search_text.lower().split()

        # Words that are not useful for document searching
        stop_words = {
            "what",
            "which",
            "are",
            "is",
            "the",
            "a",
            "an",
            "in",
            "of",
            "to",
            "used",
            "for",
            "on",
            "and",
            "do",
            "does",
            "how",
            "why",
            "where",
            "when"
        }

        # Keep useful keywords
        keywords = [
            word.strip("?,.")
            for word in words
            if word.strip("?,.") not in stop_words
        ]

        with driver.session() as session:

            results = []

            # Search Neo4j using each keyword
            for keyword in keywords:

                result = session.run(
                    """
                    MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)

                    WHERE toLower(c.text) CONTAINS $keyword

                    RETURN c.id AS id,
                           c.text AS text

                    ORDER BY c.id

                    LIMIT $limit
                    """,
                    parameters={
                        "keyword": keyword,
                        "limit": k
                    }
                )

                for record in result:

                    item = {
                        "id": record["id"],
                        "text": record["text"]
                    }

                    # Avoid duplicate chunks
                    if item not in results:
                        results.append(item)

                    # Stop once we have enough results
                    if len(results) >= k:
                        break

                if len(results) >= k:
                    break

            return results

    finally:
        driver.close()