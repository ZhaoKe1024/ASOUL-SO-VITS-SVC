import json
import os
from openai import OpenAI

from .config import LLM_CONFIG_PATH


class LLMClient:
    def __init__(self, model_name="qwen", user_name="zk"):
        self.model_name = model_name
        self.user_name = user_name
        self.config = self._load_config()
        self.client = self._create_client()
    
    def _load_config(self):
        if not os.path.exists(LLM_CONFIG_PATH):
            raise FileNotFoundError(f"LLM config file not found: {LLM_CONFIG_PATH}")
        with open(LLM_CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    
    def _create_client(self):
        api_key = self.config[self.model_name]["api_key"]
        base_url = self.config[self.model_name]["base_url"]
        return OpenAI(api_key=api_key, base_url=base_url)
    
    def chat(self, prompt, system_prompt="你是一个智能语音助手，你会对我的对话进行回复，注意回复内容里不要有汉字或英文字母以外的字符，以免TTS程序无法识别。", **kwargs):
        print(f"Calling {self.model_name} of {self.user_name}")
        
        chat_completion = self.client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model=self.config[self.model_name]["model"],
            stream=False,
            temperature=kwargs.get("temperature", 0.2),
        )
        
        print(f"Prompt tokens: {chat_completion.usage.prompt_tokens}")
        print(f"Completion tokens: {chat_completion.usage.completion_tokens}")
        print(f"Total tokens: {chat_completion.usage.total_tokens}")
        
        result = chat_completion.choices[0].message.content
        return result


def llm_chat(prompt, system_prompt="You are a helpful assistant.", model_name="qwen", user_name="zk"):
    client = LLMClient(model_name=model_name, user_name=user_name)
    return client.chat(prompt, system_prompt=system_prompt)
