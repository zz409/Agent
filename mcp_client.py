import sys
import pathlib
from mcp import Client,StdioServerParameters

BASE_DIR=pathlib.Path(__file__).resolve().parent

servers={
    "rag":StdioServerParameters(
        command=sys.executable,
        args=[
            "-m",
            "mcp_servers.rag_server"
        ],
        cwd=str(BASE_DIR)
    )
}

tool_servers={}

async def get_mcp_tools():
    tools = []

    for server_name, server_params in servers.items():


        async with Client(server_params) as client:


            result = await client.list_tools()

            for tool in result.tools:
                tool_servers[tool.name] = server_name

                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.input_schema
                    }
                })

    return tools

async def call_mcp_tool(name,arguments):

    server_name=tool_servers.get(name)

    if server_name is None:
        return False,f"MCP tool not found:{name}"

    server_params=servers[server_name]

    async with Client(server_params) as client:
        result=await client.call_tool(
            name,
            arguments
        )

        text=""

        for content in result.content:
            if hasattr(content,"text"):
                text+=content.text
        return True,text