from datetime import datetime
import pathlib


# =====================================================
# 日志目录
# =====================================================

LOG_DIR = pathlib.Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# 完整 Agent 日志
LOG_FILE = LOG_DIR / "agent.log"

# 模型回复日志
MODEL_LOG_FILE = LOG_DIR / "model_response.log"

MESSAGE_LOG_FILE = LOG_DIR / "message.log"


# =====================================================
# 完整日志
# =====================================================

def write_log(title, content):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    try:

        with LOG_FILE.open(
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                f"\n[{timestamp}] {title}\n"
            )

            file.write(
                "=" * 150 + "\n"
            )

            file.write(str(content))

            file.write("\n")

    except Exception as e:

        print(
            f"Logger error: "
            f"{type(e).__name__}: {e}"
        )


def write_message_log(content):

    timestamp=datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    try:
        with MESSAGE_LOG_FILE.open(
            "a",
            encoding="utf-8"
        ) as file:
            file.write(
                f"\n[{timestamp}]MESSAGE\n"
            )
            
            file.write(
                "="*150+"\n"
            )

            for message in content:
                file.write(str(message).replace("\\n","\n")+"\n")

            file.write("\n")

    except Exception as e:
        print(
            f"Message logger error:"
            f"{type(e).__name__}:{e}"
        )        

# =====================================================
# 模型回复日志
# =====================================================

def write_model_log(response):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    try:

        choice = response.choices[0]

        message = choice.message


        # =================================================
        # 处理换行
        # =================================================

        def clean(value):

            if value is None:
                return "None"

            return str(value).replace(
                "\n",
                " "
            )

        text=str(message.content)

        # =================================================
        # 写入模型日志
        # =================================================

        with MODEL_LOG_FILE.open(
            "a",
            encoding="utf-8"
        ) as file:

            file.write(
                f"\n[{timestamp}] MODEL RESPONSE\n"
            )

            file.write(
                "=" * 80 + "\n"
            )

            file.write(
                f"content: {text}\n"
            )

            file.write(
                f"finish_reason: {clean(choice.finish_reason)}\n"
            )

            file.write(
                f"role: {clean(message.role)}\n"
            )



            # =================================================
            # Tool Calls
            # =================================================

            if message.tool_calls:

                for tool_call in message.tool_calls:

                    file.write(
                        f"name: "
                        f"{clean(tool_call.function.name)}\n"
                    )

                    file.write(
                        f"arguments: "
                        f"{clean(tool_call.function.arguments)}\n"
                    )

            else:

                file.write(
                    "name: None\n"
                )
                                
                file.write(
                    "arguments: None\n"
                )

            file.write("\n")

    except Exception as e:

        print(
            f"Model logger error: "
            f"{type(e).__name__}: {e}"
        )