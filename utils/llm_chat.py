from openai import OpenAI


api_config = {
    "qwen3-1.7b":{
        "api_key":"sk-edf6b8ed104c4850ac5539c7ba8bf607",
        "base_url":"https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model":"qwen3-1.7b"
    }
}

def llm_chat(prompt, system_prompt="You are a excellent assistant.", model_name="deepseek", user_name="zk"):
    """Official usage of Deepseek official website"""
    api_key = api_config[model_name]["api_key"]
    client = OpenAI(api_key=api_key, base_url=api_config[model_name]["base_url"])
    print(f"calling {model_name} of {user_name}")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=api_config[model_name]["model"],
        stream=False,
        temperature=0.2,
        extra_body={"enable_thinking": False}
    )
    # 获取 token 使用情况
    print(f"提示 tokens: {chat_completion.usage.prompt_tokens}")
    print(f"完成 tokens: {chat_completion.usage.completion_tokens}")  # 响应的tokens
    print(f"总 tokens: {chat_completion.usage.total_tokens}")

    # 响应内容
    # print(f"响应: {chat_completion.choices[0].message.content}")

    result = chat_completion.choices[0].message.content
    return result
