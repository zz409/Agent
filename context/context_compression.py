import memory.summary_db

async def compress_context(conversation_id,client):
    summary=memory.summary_db.load_latest_summary(conversation_id)
    recent_events=memory.summary_db.load_recent_events(conversation_id,summary["last_event_id"])
    prompt=[
    {
        "role":"system",
        "content":"我需要你总结对话内容并输出不超过50个字的历史摘要"
    }, 

    {
        "role":"user",
        "content":"以下是之前的历史对话摘要"+summary["summary"]
    },

    {
        "role":"system",
        "content":"以下是最近几轮对话"
    }
    ]
    for event in recent_events:
        if event["role"]=="user":
            prompt.append(
                {
                    "role":"user",
                    "content":event["content"]
                }
            )

        if event["role"]=="assistant":
            if event["tool_calls"]:
                prompt.append(
                    {
                        "role":"assistant",
                        "content":event["content"],
                        "tool_calls":event["tool_calls"]
                    }
                )

            else:
                prompt.append(
                    {
                        "role":"assistant",
                        "content":event["content"],
                    }
                )

        if event["role"]=="tool":
            prompt.append(
                {
                    "role":"tool",
                    "content":event["content"],
                    "tool_call_id":event["tool_call_id"]
                }
            )

    response=await client.chat.completions.create(
        model="deepseek-flash",
        messages=prompt
    )

    memory.summary_db.save_summary(
        conversation_id,
        response.choices[0].message.content,
        recent_events[-1]["id"]
    )