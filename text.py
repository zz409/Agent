import asyncio
import dotenv
import openai
import os
import json
import pathlib

from logger import write_log, write_model_log,write_message_log
from mcp_client import call_mcp_tool,get_mcp_tools
from memory import short_term_memory


dotenv.load_dotenv()


# =========================================================
# 基础配置
# =========================================================

api_key = os.getenv("DEEPSEEK_API_KEY")

client = openai.OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
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

def normalize_message(message):
    result={
        "role":"assistant",
        "content":message.content or ""
    }

    if message.tool_calls:
        result["tool_calls"]=[]
        for tool_call in message.tool_calls:
            result["tool_calls"].append(
                {
                    "id":tool_call.id,
                    "type":"function",
                    "function":{
                        "name":tool_call.function.name,
                        "arguments":tool_call.function.arguments
                    }
                }
            )

    return result

# =========================================================
# Agent Loop
# =========================================================

async def run_agent(conversation,user_input,tools):

    messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    short_term_memory.add_message(
        conversation,
        {
            "role":"user",
            "content":user_input
        }
    )



    while True:

        # -------------------------------------------------
        # 请求 LLM
        # -------------------------------------------------
        
        write_log(
            "MESSAGES SENT TO MODEL",
            messages
        )

        write_message_log(messages)

        response = client.chat.completions.create(
            model="deepseek-flash",
            messages=messages,
            tools=tools
        )

        messages.append(
            normalize_message(response.choices[0].message)
        )

        write_model_log(response)

        write_log(
            "MODEL RESPONSE",
            response
        )

        # -------------------------------------------------
        # 没有 Tool Call
        # -------------------------------------------------

        if response.choices[0].finish_reason=="stop":

            print(
                "\nAssistant:",
                response.choices[0].message.content
            )

            short_term_memory.add_message(
                conversation,
                {
                    "role":"assistant",
                    "content":response.choices[0].message.content
                }
            )

            short_term_memory.save_conversation(conversation)

            break


        # -------------------------------------------------
        # 执行 Tool Call
        # -------------------------------------------------
        if response.choices[0].finish_reason=="tool_calls":

            for tool_call in response.choices[0].message.tool_calls:

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

    conversation=short_term_memory.select_conversation()

    messages.extend(conversation["messages"])

    for message in conversation["messages"]:
        print(message["role"],":",message["content"])

    while True:

        conversation=short_term_memory.load_conversation(conversation)

        user_input = input(
            "\nYou: "
        )


        if user_input == "exit":
            break


        await run_agent(
            conversation,
            user_input,
            tools
        )


if __name__ == "__main__":
    print("Starting agent...")
    asyncio.run(
        main()
    )