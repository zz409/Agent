import llm.llm
import mcp_client
import agent.agent_loop
import json

def sse(event_type,data):
    return(
        f"event:{event_type}\n"
        f"data:{json.dumps(data,ensure_ascii=False)}\n\n"
    )

async def main(user_input,conversation_id):

    yield sse(
        "status",
        {"message":"正在处理用户请求"}
    )

    try:
        tools=await mcp_client.get_mcp_tools()

        client=llm.llm.get_client()

        async for event in agent.agent_loop.loop(
            client,
            conversation_id,
            user_input,
            tools
        ):
            yield sse(
                event["type"],
                event["data"]
            )

        yield sse("done",{
            "message":"任务完成"
        })

    except Exception as e:
        yield sse("error",{
            "message":str(e)
        })