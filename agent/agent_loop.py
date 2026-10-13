
import context.prompt_builder
import mcp_client
import json


async def execute_tool(name, arguments):
    return await mcp_client.call_mcp_tool(name, arguments)


async def loop(client, conversation_id, user_input, tools):

    prompt = context.prompt_builder.build_prompt(conversation_id)

    prompt.append({
        "role": "user",
        "content": user_input
    })

    MAX_STEPS = 10

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

        # 第一阶段：接收模型流式输出
        async for chunk in stream:

            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            if choice.finish_reason:
                finish_reason = choice.finish_reason

            # 实时发送 content
            if delta.content:
                content += delta.content

                yield {
                    "type": "content",
                    "data": {
                        "text": delta.content
                    }
                }

            # 收集流式 tool_calls
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

        # 第二阶段：流式响应结束，整理工具调用
        collected_tools = [
            tool_calls[index]
            for index in sorted(tool_calls)
        ]

        if finish_reason == "length":
            raise RuntimeError("模型输出达到长度限制")

        # 将 assistant 消息加入上下文
        assistant_message = {
            "role": "assistant",
            "content": content or None
        }

        if collected_tools:
            assistant_message["tool_calls"] = collected_tools

        prompt.append(assistant_message)

        # 第三阶段：判断是否结束
        if not collected_tools:

            if finish_reason != "stop":
                raise RuntimeError(
                    f"模型意外结束: {finish_reason}"
                )

            return

        if finish_reason != "tool_calls":
            raise RuntimeError(
                f"工具调用结束状态异常: {finish_reason}"
            )

        # 如果模型没有提供行动说明，补充说明
        if not content.strip():
            yield {
                "type": "content",
                "data": {
                    "text": "我将使用相关工具处理这个请求。"
                }
            }

        # 第四阶段：执行工具
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

            # 将工具结果加入上下文
            prompt.append({
                "role": "tool",
                "tool_call_id": tool["id"],
                "content": tool_result
            })

    raise RuntimeError("Agent 已达到最大执行轮数")
