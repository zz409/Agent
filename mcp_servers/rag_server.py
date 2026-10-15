from mcp.server.mcpserver import MCPServer

from rag.retrieve import search_documents


mcp = MCPServer("rag_server")


@mcp.tool()
def search_rag(question: str) -> dict:
    """
    检索企业内部知识库中的相关文档内容。

    当用户询问企业内部制度、工作流程、
    公司规定、业务资料或其他内部文档信息时，
    应使用此工具进行检索。

    Args:
        question: 要检索的问题，尽量包含具体的检索主题。

    Returns:
        包含检索结果、文档来源及相关性分数的结构化数据。
    """

    try:

        results = search_documents(
            question=question,
            retrieve_top_k=20,
            rerank_top_k=5
        )

        return {
            "success": True,
            "query": question,
            "count": len(results),
            "documents": results
        }

    except Exception as e:

        return {
            "success": False,
            "query": question,
            "error": f"{type(e).__name__}: {e}",
            "documents": []
        }


if __name__ == "__main__":
    mcp.run()