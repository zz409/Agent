import context.prompt_builder
import memory.summary_db
import openai
import os
import dotenv
import json
import mcp_client
import asyncio

dotenv.load_dotenv()
deepseek_api_key=os.getenv("DEEPSEEK_API_KEY")

if __name__ == "__main__":
    client = openai.OpenAI(
        api_key=deepseek_api_key,
        base_url="https://api.deepseek.com"
    )

    tools=asyncio.run(mcp_client.get_mcp_tools())

    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {"role": "system", "content": "你是一个ReAct Agent,你可以调用工具来获取信息,并根据工具的结果生成最终的回答，并且回答必须输出中文content用来说明你接下来的行动。"},
            {"role": "user", "content": "帮我写一个网页"},
        ],
        tools=tools,
        stream=True
    )

    for chunk in response:
        print(chunk.model_dump_json(indent=2))