import asyncio
import dotenv
import openai
import os
import json
import pathlib

from mcp_client import call_mcp_tool,get_mcp_tools


dotenv.load_dotenv()


# =========================================================
# 基础配置
# =========================================================

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model = os.getenv("MODEL")


client = openai.OpenAI(
    api_key=api_key,
    base_url=base_url
)


# =========================================================
# 工作目录
# =========================================================

WORKSPACE = pathlib.Path("generated_site")

WORKSPACE.mkdir(
    exist_ok=True
)


# =========================================================
# Tools list
# =========================================================

async def execute_tool(name,arguments):
    return await call_mcp_tool(
        name,
        arguments
    )


# =========================================================
# Messages
# =========================================================

messages = [

    {
        "role": "system",

        "content": """
        You are a Code Agent.

        When the user asks you to create or modify code or files,
        use the available file tools to actually perform the task.

        When the user asks a conceptual or informational question,
        answer the question directly.

        Use search_rag when information from the local knowledge base
        may help answer the user's question.

        The read_file, write_file and list_files tools operate only
        inside the generated_site workspace.

        Knowledge-base source names returned by search_rag are references
        only and must not be passed to read_file.
        """
    }

]


# =========================================================
# Agent Loop
# =========================================================

async def run_agent(user_request,tools):

    messages.append(
        {
            "role": "user",
            "content": user_request
        }
    )


    while True:

        # -------------------------------------------------
        # 请求 LLM
        # -------------------------------------------------

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools
        )


        message = response.choices[0].message


        # 保存 Assistant 消息
        messages.append(message)


        # -------------------------------------------------
        # 没有 Tool Call
        # -------------------------------------------------

        if not message.tool_calls:

            print(
                "\nAssistant:",
                message.content
            )

            break


        # -------------------------------------------------
        # 执行 Tool Call
        # -------------------------------------------------

        for tool_call in message.tool_calls:

            name = tool_call.function.name


            arguments = json.loads(
                tool_call.function.arguments
            )


            print(
                f"\nCalling tool: {name}"
            )


            # ---------------------------------------------
            # 调用工具
            # ---------------------------------------------

            success,result = await execute_tool(
                name,
                arguments
            )


            if success:
                print("\nTool call succeeded")
            else:
                print("\nTool call failed")
            


            # ---------------------------------------------
            # Tool 结果放回上下文
            # ---------------------------------------------

            messages.append(
                {
                    "role": "tool",

                    "tool_call_id": tool_call.id,

                    "content": result
                }
            )


# =========================================================
# Main
# =========================================================

async def main():

    tools=await get_mcp_tools()

    while True:

        user_input = input(
            "\nYou: "
        )


        if user_input == "exit":
            break


        await run_agent(
            user_input,
            tools
        )


if __name__ == "__main__":
    print("Starting agent...")
    asyncio.run(
        main()
    )