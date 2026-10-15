import context.prompt_builder
import context.context_compression
import mcp_client
import json
import memory.conversation_db

async def execute_tool(name, arguments):
    return await mcp_client.call_mcp_tool(name, arguments)


async def loop(client, conversation_id, user_input, tools):

    prompt = context.prompt_builder.build_prompt(conversation_id)

    prompt.append(
        {
        "role": "user",
        "content": user_input
        }
    )

    memory.conversation_db.append_event(conversation_id,"user",user_input)

    MAX_STEPS = 10
    prompt_tokens=None

    for step in range(MAX_STEPS):

        yield {
            "type": "status",
            "data": {"message": "正在调用模型"}
        }

        stream = await client.chat.completions.create(
            model="deepseek-flash",
            messages=prompt,
            tools=tools,
            stream=True
        )

        content = ""
        tool_calls = {}
        finish_reason = None

        async for chunk in stream:

            if chunk.usage:
                prompt_tokens=chunk.usage.prompt_tokens

            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if choice.finish_reason:
                finish_reason = choice.finish_reason

            if delta.content:
                content += delta.content

                yield {
                    "type": "content",
                    "data": {
                        "text": delta.content
                    }
                }

            if delta.tool_calls:

                for tool in delta.tool_calls:

                    index = tool.index

                    if index not in tool_calls:
                        tool_calls[index] = {
                            "id": "",
                            "type": "function",
                            "function": {
                                "name": "",
                                "arguments": ""
                            }
                        }

                    current = tool_calls[index]

                    if tool.id:
                        current["id"] = tool.id

                    if tool.function:

                        if tool.function.name:
                            current["function"]["name"] += (
                                tool.function.name
                            )

                        if tool.function.arguments:
                            current["function"]["arguments"] += (
                                tool.function.arguments
                            )

        collected_tools = [
            tool_calls[index]
            for index in sorted(tool_calls)
        ]

        if finish_reason == "length":
            raise RuntimeError("模型输出达到长度限制")

        if finish_reason=="stop":

            memory.conversation_db.append_event(conversation_id,"assistant",content)

            if prompt_tokens is not None and prompt_tokens>50000:
                await context.context_compression(conversation_id,client)

            return

        if finish_reason=="tool_calls":

            prompt.append(
                {
                    "role":"assistant",
                    "content":content or None,
                    "tool_calls":collected_tools
                }
            )

            memory.conversation_db.append_event(
                conversation_id,
                "assistant",
                content,
                collected_tools
            )

            for tool in collected_tools:

                name = tool["function"]["name"]

                try:
                    arguments = json.loads(
                        tool["function"]["arguments"]
                    )

                    if not isinstance(arguments, dict):
                        raise ValueError("工具参数必须是 JSON 对象")

                    yield {
                        "type": "tool_start",
                        "data": {
                            "name": name,
                            "message": f"正在调用 {name}"
                        }
                    }

                    success, result = await execute_tool(
                        name,
                        arguments
                    )

                    tool_result = str(result)


                    yield {
                        "type": "tool_end",
                        "data": {
                            "name": name,
                            "success": success
                        }
                    }

                except Exception as e:

                    tool_result = f"工具调用失败: {e}"

                    yield {
                        "type": "tool_end",
                        "data": {
                            "name": name,
                            "success": False
                        }
                    }

                memory.conversation_db.append_event(
                    conversation_id,
                    "tool",
                    tool_result,
                    None,tool["id"]
                )

                prompt.append({
                    "role": "tool",
                    "tool_call_id": tool["id"],
                    "content": tool_result
                })

            continue

        raise RuntimeError(
            f"模型异常结束:{finish_reason}"
        )

    raise RuntimeError("Agent 已达到最大执行轮数")
