import os
import json
import time
from http import HTTPStatus
from urllib import request
from dashscope.audio.asr import Transcription
import dashscope


class ASRClient:
    def __init__(self, api_key=None):
        if api_key:
            dashscope.api_key = api_key
        else:
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        
        if not dashscope.api_key:
            raise ValueError("DashScope API key is required. Please set DASHSCOPE_API_KEY environment variable.")
    
    def recognize(self, audio_file_path, language_hints=None):
        if language_hints is None:
            language_hints = ['zh', 'en']
        
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        file_url = f"file://{audio_file_path}"
        
        task_response = Transcription.async_call(
            model='fun-asr',
            file_urls=[file_url],
            language_hints=language_hints
        )
        
        transcription_response = Transcription.wait(task=task_response.output.task_id)
        
        if transcription_response.status_code == HTTPStatus.OK:
            for transcription in transcription_response.output['results']:
                if transcription['subtask_status'] == 'SUCCEEDED':
                    url = transcription['transcription_url']
                    result = json.loads(request.urlopen(url).read().decode('utf8'))
                    
                    text_parts = []
                    if 'flash_result' in result and 'sentences' in result['flash_result']:
                        for sentence in result['flash_result']['sentences']:
                            if 'text' in sentence:
                                text_parts.append(sentence['text'])
                    
                    return " ".join(text_parts) if text_parts else result.get('text', '')
                else:
                    raise Exception(f"Transcription failed: {transcription}")
        else:
            raise Exception(f"Error: {transcription_response.output.message}")


def recognize_audio(audio_file_path, api_key=None):
    client = ASRClient(api_key=api_key)
    return client.recognize(audio_file_path)
