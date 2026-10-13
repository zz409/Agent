import db.db as db
import embedding

from sentence_transformers import CrossEncoder
from mcp.server import MCPServer

mcp = MCPServer("rag_server")

rerank_model = None

def get_rerank_model():
    global rerank_model
    if rerank_model is None:
        rerank_model = CrossEncoder("BAAI/bge-reranker-v2-m3")
    return rerank_model

def retrieve_documents(
    question,
    top_k=20
):

    question_vector = embedding.get_embedding(question)

    conn = db.get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT
                    id,
                    content,
                    source,
                    chunk_index,
                    embedding <=> %s::vector AS distance
                FROM documents
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (
                    question_vector,
                    question_vector,
                    top_k
                )
            )

            result = cur.fetchall()

            return result

    finally:

        conn.close()

def rerank_documents(
    question,
    documents,
    rerank_model,
    top_k=5
):

    pairs = []

    for document in documents:

        content = document[1]

        pairs.append(
            [question, content]
        )

    scores = rerank_model.predict(
        pairs
    )

    results = []

    for document, score in zip(
        documents,
        scores
    ):

        results.append(
            {
                "document": document,
                "rerank_score": float(score)
            }
        )

    results.sort(
        key=lambda x: x["rerank_score"],
        reverse=True
    )

    return results[:top_k]

def search_documents(
    question,
    retrieve_top_k=20,
    rerank_top_k=5
):

    documents = retrieve_documents(
        question,
        retrieve_top_k
    )

    model=get_rerank_model()

    results = rerank_documents(
        question,
        documents,
        model,
        rerank_top_k
    )

    return results

@mcp.tool()
def search_rag(
    question: str
) -> str:

    """
    Search the local knowledge base
    for information related to the question.
    """

    try:

        results = search_documents(question)

        if not results:

            return ("No relevant information was found in the local knowledge base.")

        context = ""

        for row in results:

            document = row["document"]

            context += (
                f"来源: {document[2]}\n"
                f"内容: {document[1]}\n\n"
            )

        return context

    except Exception as e:

        return (
            f"search_rag failed\n"
            f"{type(e).__name__}: {e}"
        )

if __name__ == "__main__":
    mcp.run()