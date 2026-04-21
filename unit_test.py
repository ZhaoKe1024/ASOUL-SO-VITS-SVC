#!/user/culle/.conda/envs/llms
# -*- coding: utf_8 -*-
# @Time : 2026/04/21 23:02
# @Author: ZhaoKe
# @File : unit_test.py
# @Software: trae
import os
import json
from asoulchat.asr_client import recognize_audio, recognize_stream_mic, ASRClient

"""
我才用的实时语音识别方案在这个链接中：
https://help.aliyun.com/zh/model-studio/fun-asr-realtime-python-sdk

主要参考下面两个案例：

非流式调用：
from http import HTTPStatus
import dashscope
from dashscope.audio.asr import Recognition
import os

# 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
# 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY')

# 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference
dashscope.base_websocket_api_url='wss://dashscope.aliyuncs.com/api-ws/v1/inference'

recognition = Recognition(model='fun-asr-realtime',
                          format='wav',
                          sample_rate=16000,
                          callback=None)
result = recognition.call('asr_example.wav')
if result.status_code == HTTPStatus.OK:
    print('识别结果：')
    print(result.get_sentence())
else:
    print('Error: ', result.message)
    
print(
    '[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'
    .format(
        recognition.get_last_request_id(),
        recognition.get_first_package_delay(),
        recognition.get_last_package_delay(),
    ))

和流式调用：
import os
import signal  # for keyboard events handling (press "Ctrl+C" to terminate recording)
import sys

import dashscope
import pyaudio
from dashscope.audio.asr import *

mic = None
stream = None

# Set recording parameters
sample_rate = 16000  # sampling rate (Hz)
channels = 1  # mono channel
dtype = 'int16'  # data type
format_pcm = 'pcm'  # the format of the audio data
block_size = 3200  # number of frames per buffer


# Real-time speech recognition callback
class Callback(RecognitionCallback):
    def on_open(self) -> None:
        global mic
        global stream
        print('RecognitionCallback open.')
        mic = pyaudio.PyAudio()
        stream = mic.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=16000,
                          input=True)

    def on_close(self) -> None:
        global mic
        global stream
        print('RecognitionCallback close.')
        stream.stop_stream()
        stream.close()
        mic.terminate()
        stream = None
        mic = None

    def on_complete(self) -> None:
        print('RecognitionCallback completed.')  # recognition completed

    def on_error(self, message) -> None:
        print('RecognitionCallback task_id: ', message.request_id)
        print('RecognitionCallback error: ', message.message)
        # Stop and close the audio stream if it is running
        if 'stream' in globals() and stream.active:
            stream.stop()
            stream.close()
        # Forcefully exit the program
        sys.exit(1)

    def on_event(self, result: RecognitionResult) -> None:
        sentence = result.get_sentence()
        if 'text' in sentence:
            print('RecognitionCallback text: ', sentence['text'])
            if RecognitionResult.is_sentence_end(sentence):
                print(
                    'RecognitionCallback sentence end, request_id:%s, usage:%s'
                    % (result.get_request_id(), result.get_usage(sentence)))


def signal_handler(sig, frame):
    print('Ctrl+C pressed, stop recognition ...')
    # Stop recognition
    recognition.stop()
    print('Recognition stopped.')
    print(
        '[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'
        .format(
            recognition.get_last_request_id(),
            recognition.get_first_package_delay(),
            recognition.get_last_package_delay(),
        ))
    # Forcefully exit the program
    sys.exit(0)


# main function
if __name__ == '__main__':
    # 新加坡和北京地域的API Key不同。获取API Key：https://help.aliyun.com/zh/model-studio/get-api-key
    # 若没有配置环境变量，请用百炼API Key将下行替换为：dashscope.api_key = "sk-xxx"
    dashscope.api_key = os.environ.get('DASHSCOPE_API_KEY')

    # 以下为北京地域url，若使用新加坡地域的模型，需将url替换为：wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference
    dashscope.base_websocket_api_url='wss://dashscope.aliyuncs.com/api-ws/v1/inference'

    # Create the recognition callback
    callback = Callback()

    # Call recognition service by async mode, you can customize the recognition parameters, like model, format,
    # sample_rate
    recognition = Recognition(
        model='fun-asr-realtime',
        format=format_pcm,
        # 'pcm'、'wav'、'opus'、'speex'、'aac'、'amr', you can check the supported formats in the document
        sample_rate=sample_rate,
        # support 8000, 16000
        semantic_punctuation_enabled=False,
        callback=callback)

    # Start recognition
    recognition.start()

    signal.signal(signal.SIGINT, signal_handler)
    print("Press 'Ctrl+C' to stop recording and recognition...")
    # Create a keyboard listener until "Ctrl+C" is pressed

    while True:
        if stream:
            data = stream.read(3200, exception_on_overflow=False)
            recognition.send_audio_frame(data)
        else:
            break

    recognition.stop()

请你参考这两个方式，非流式调用用于处理本地音频文件，流式调用用于处理实时音频流（例如麦克风输入）。
请为我改写 ./asoulchat/asr_client.py 里面的代码，
然后在当前文件撰写非流式调用的测试示例
"""

# ==================== 非流式调用测试示例 ====================


def test_non_streaming_single_file():
    """
    测试示例1：识别单个音频文件
    """
    # 从配置文件加载API密钥
    config = json.load(open("./private/llm_config.json", "r", encoding="utf-8"))
    api_key = config.get("qwen-235b", {}).get("api_key")
    
    # 方法1：使用便捷函数
    print("=== 方法1：使用便捷函数 ===")
    text = recognize_audio("./jiaran_sing_demo.mp3", api_key=api_key)
    print(f"识别结果: {text}")
    
    # 方法2：使用ASRClient类（推荐，更多配置选项）
    print("\n=== 方法2：使用ASRClient类 ===")
    client = ASRClient(api_key=api_key, region="beijing")
    result = client.recognize_file(
        audio_file_path="./jiaran_sing_demo.mp3",
        audio_format="mp3",  # 支持 wav, pcm, mp3, opus, speex, aac, amr
        sample_rate=16000
    )
    if result:
        print(f"识别结果: {result}")


def test_non_streaming_batch_files():
    """
    测试示例2：批量识别多个音频文件
    """
    config = json.load(open("./private/llm_config.json", "r", encoding="utf-8"))
    api_key = config.get("qwen-235b", {}).get("api_key")
    
    audio_files = [
        "./audio/file1.wav",
        "./audio/file2.mp3",
        "./audio/file3.wav"
    ]
    
    client = ASRClient(api_key=api_key)
    results = []
    
    for audio_file in audio_files:
        if os.path.exists(audio_file):
            print(f"\n正在识别: {audio_file}")
            try:
                result = client.recognize_file(audio_file)
                results.append({
                    'file': audio_file,
                    'text': result.get('text', '') if result else ''
                })
            except Exception as e:
                print(f"识别失败 {audio_file}: {e}")
                results.append({'file': audio_file, 'text': '', 'error': str(e)})
        else:
            print(f"文件不存在: {audio_file}")
    
    # 输出汇总结果
    print("\n=== 批量识别结果汇总 ===")
    for r in results:
        print(f"文件: {r['file']}")
        print(f"文本: {r['text']}")
        print("-" * 50)


def test_non_streaming_with_error_handling():
    """
    测试示例3：带错误处理的完整示例
    """
    config = json.load(open("./private/llm_config.json", "r", encoding="utf-8"))
    api_key = config.get("qwen", {}).get("api_key")
    
    # 测试文件
    audio_file = "./jiaran_sing_demo.mp3"
    
    try:
        # 创建客户端
        client = ASRClient(api_key=api_key, region="beijing")
        
        # 检查文件
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        print(f"开始识别音频文件: {audio_file}")
        
        # 执行识别
        result = client.recognize_file(
            audio_file_path=audio_file,
            audio_format="mp3",
            sample_rate=16000
        )
        
        # 处理结果
        if result and 'text' in result:
            text = result['text']
            print(f"\n✓ 识别成功!")
            print(f"识别文本: {text}")
            return text
        else:
            print("\n✗ 识别失败: 返回结果为空")
            return None
            
    except FileNotFoundError as e:
        print(f"\n✗ 文件错误: {e}")
    except ValueError as e:
        print(f"\n✗ 配置错误: {e}")
    except Exception as e:
        print(f"\n✗ 识别异常: {e}")
    
    return None


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    """
    运行测试示例
    
    可用的测试函数:
    - test_non_streaming_single_file(): 单个文件识别测试
    - test_non_streaming_batch_files(): 批量文件识别测试
    - test_non_streaming_with_error_handling(): 带错误处理的完整示例
    """
    
    print("=" * 60)
    print("ASR 非流式调用测试")
    print("=" * 60)
    
    # 选择要运行的测试（取消注释相应的行）
    
    # 测试1: 单个文件识别
    # test_non_streaming_single_file()
    
    # 测试2: 批量文件识别
    # test_non_streaming_batch_files()
    
    # 测试3: 带错误处理的完整示例（推荐）
    test_non_streaming_with_error_handling()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
