#!/user/culle/.conda/envs/llms
# -*- coding: utf_8 -*-
# @Time : 2026/04/19 23:58
# @Author: ZhaoKe
# @File : asr_client.py
# @Software: trae
import os
import sys
import json
import time
import signal
import tempfile
from http import HTTPStatus
from typing import Optional, Callable, Dict, Any, Tuple
from dashscope.audio.asr import Recognition, RecognitionResult, RecognitionCallback
import dashscope


def get_audio_info(audio_file_path: str) -> Tuple[int, int, int]:
    """
    获取音频文件信息（采样率、通道数、位深度）
    
    Args:
        audio_file_path: 音频文件路径
        
    Returns:
        元组 (sample_rate, channels, bit_depth)
    """
    try:
        # 尝试使用 pydub 获取音频信息
        from pydub import AudioSegment
        audio = AudioSegment.from_file(audio_file_path)
        return audio.frame_rate, audio.channels, audio.sample_width * 8
    except ImportError:
        pass
    
    try:
        # 尝试使用 wave 获取WAV文件信息
        import wave
        with wave.open(audio_file_path, 'rb') as wav_file:
            return wav_file.getframerate(), wav_file.getnchannels(), wav_file.getsampwidth() * 8
    except Exception:
        pass
    
    try:
        # 尝试使用 soundfile 获取音频信息
        import soundfile as sf
        info = sf.info(audio_file_path)
        return info.samplerate, info.channels, info.subtype_info
    except ImportError:
        pass
    
    # 如果都无法获取，返回默认值
    return 44100, 2, 16


def convert_audio_to_wav_16k(
    audio_file_path: str,
    target_sample_rate: int = 16000,
    target_channels: int = 1
) -> str:
    """
    将音频文件转换为符合 ASR 要求的格式（WAV, 16kHz, 单声道）
    
    Args:
        audio_file_path: 原始音频文件路径
        target_sample_rate: 目标采样率（默认16000）
        target_channels: 目标通道数（默认1单声道）
        
    Returns:
        转换后的临时WAV文件路径
    """
    try:
        from pydub import AudioSegment
    except ImportError:
        raise ImportError(
            "音频转换需要 pydub，请运行: pip install pydub\n"
            "同时需要安装 ffmpeg，可从 https://ffmpeg.org/download.html 下载"
        )
    
    # 加载音频文件
    audio = AudioSegment.from_file(audio_file_path)
    
    # 转换为单声道（如果需要）
    if audio.channels != target_channels:
        audio = audio.set_channels(target_channels)
    
    # 重采样到目标采样率（如果需要）
    if audio.frame_rate != target_sample_rate:
        audio = audio.set_frame_rate(target_sample_rate)
    
    # 创建临时文件
    temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
    os.close(temp_fd)
    
    # 导出为 WAV 格式
    audio.export(temp_path, format='wav')
    
    return temp_path


class ASRClient:
    """阿里云FunASR实时语音识别客户端
    
    支持两种调用方式：
    1. 非流式调用：处理本地音频文件
    2. 流式调用：处理实时音频流（如麦克风输入）
    """
    
    def __init__(self, api_key: Optional[str] = None, region: str = "beijing"):
        """
        初始化ASR客户端
        
        Args:
            api_key: DashScope API密钥，如未提供则从环境变量DASHSCOPE_API_KEY获取
            region: 服务地域，可选 "beijing" 或 "singapore"
        """
        if api_key:
            dashscope.api_key = api_key
        else:
            dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
        
        if not dashscope.api_key:
            raise ValueError(
                "DashScope API key is required. "
                "Please set DASHSCOPE_API_KEY environment variable or pass api_key parameter."
            )
        
        # 设置WebSocket API地址
        if region.lower() in ["singapore", "sg", "intl"]:
            dashscope.base_websocket_api_url = 'wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference'
        else:
            dashscope.base_websocket_api_url = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference'
        print(f"DashScope API key: {dashscope.api_key}")
        print(f"WebSocket API URL: {dashscope.base_websocket_api_url}")
    
    def recognize_file(
        self, 
        audio_file_path: str, 
        audio_format: str = 'wav',
        sample_rate: int = 16000,
        auto_convert: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        非流式调用：识别本地音频文件
        
        Args:
            audio_file_path: 音频文件路径
            audio_format: 音频格式，支持 'wav'、'pcm'、'opus'、'speex'、'aac'、'amr'
            sample_rate: 采样率，支持 8000 或 16000
            auto_convert: 是否自动转换不兼容的音频格式（默认True）
            
        Returns:
            识别结果字典，包含 text 字段，失败返回 None
        """
        if not os.path.exists(audio_file_path):
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # 临时文件路径（用于转换后的音频）
        temp_audio_path = None
        audio_file_to_use = audio_file_path
        actual_sample_rate = sample_rate
        
        # 自动检测和转换音频
        if auto_convert:
            try:
                # 获取音频文件信息
                detected_sample_rate, channels, bit_depth = get_audio_info(audio_file_path)
                print(f"检测到音频信息: 采样率={detected_sample_rate}Hz, 通道数={channels}, 位深度={bit_depth}bit")
                
                # 检查是否需要转换
                needs_conversion = (
                    detected_sample_rate != sample_rate or
                    channels != 1 or
                    audio_file_path.lower().endswith('.mp3')
                )
                
                if needs_conversion:
                    print(f"正在转换音频格式...")
                    temp_audio_path = convert_audio_to_wav_16k(
                        audio_file_path,
                        target_sample_rate=sample_rate,
                        target_channels=1
                    )
                    audio_file_to_use = temp_audio_path
                    audio_format = 'wav'
                    print(f"音频转换完成: {temp_audio_path}")
                    
            except Exception as e:
                print(f"音频自动转换失败: {e}")
                print("将尝试使用原始文件进行识别...")
        
        try:
            # 创建非流式识别对象
            recognition = Recognition(
                model='fun-asr-realtime',
                format=audio_format,
                sample_rate=sample_rate,
                callback=None  # 非流式调用不需要回调
            )
            
            # 调用识别
            result = recognition.call(audio_file_to_use)
            
            # 输出性能指标
            print(
                '[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'
                .format(
                    recognition.get_last_request_id(),
                    recognition.get_first_package_delay(),
                    recognition.get_last_package_delay(),
                )
            )
            
            # 处理结果
            if result.status_code == HTTPStatus.OK:
                sentence = result.get_sentence()
                print('识别结果：', sentence)
                # 确保返回的字典包含 'text' 键
                if isinstance(sentence, dict):
                    if 'text' in sentence:
                        return sentence
                    else:
                        # 如果字典中没有 'text' 键，但有其他文本字段，尝试适配
                        text_content = sentence.get('sentence', '') or str(sentence)
                        return {'text': text_content}
                elif isinstance(sentence, list):
                    # 如果返回的是列表，尝试取第一个元素
                    if sentence:
                        return {'text': sentence[0]["text"]}
                    else:
                        return {'text': ''}
                elif isinstance(sentence, str):
                    # 如果返回的是字符串，包装成字典格式
                    return {'text': sentence}
                else:
                    # 其他类型，转换为字符串
                    return {'text': str(sentence)}
            else:
                print('识别错误：', result.message)
                return None
                
        finally:
            # 清理临时文件
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    print(f"临时文件已清理: {temp_audio_path}")
                except Exception as e:
                    print(f"清理临时文件失败: {e}")
    
    def recognize_stream(
        self,
        audio_source: str = 'microphone',
        sample_rate: int = 16000,
        on_result: Optional[Callable[[str, bool], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        return_results: bool = True
    ) -> Optional[list]:
        """
        流式调用：识别实时音频流（如麦克风输入）
        
        Args:
            audio_source: 音频源，目前只支持 'microphone'
            sample_rate: 采样率，支持 8000 或 16000
            on_result: 识别结果回调函数，参数为 (text: str, is_final: bool)
            on_error: 错误回调函数，参数为 (error_message: str)
            return_results: 是否返回所有识别结果列表（默认True）
            
        Returns:
            如果 return_results=True，返回所有最终识别结果的列表
            如果 return_results=False，返回 None
        """
        try:
            import pyaudio
        except ImportError:
            raise ImportError("流式调用需要安装 pyaudio，请运行: pip install pyaudio")
        
        # 录音参数
        channels = 1  # 单声道
        dtype = 'int16'  # 数据类型
        block_size = 3200  # 每缓冲区帧数
        
        # 全局变量用于回调和信号处理
        recognition = None
        mic = None
        stream = None
        
        # 用于收集识别结果的列表
        all_results = []
        
        # 定义回调类
        class StreamCallback(RecognitionCallback):
            def on_open(self) -> None:
                nonlocal mic, stream
                print('语音识别已启动，开始录音...')
                mic = pyaudio.PyAudio()
                stream = mic.open(
                    format=pyaudio.paInt16,
                    channels=channels,
                    rate=sample_rate,
                    input=True
                )
            
            def on_close(self) -> None:
                nonlocal mic, stream
                print('语音识别已关闭。')
                if stream:
                    stream.stop_stream()
                    stream.close()
                if mic:
                    mic.terminate()
            
            def on_complete(self) -> None:
                print('语音识别任务完成。')
            
            def on_error(self, message) -> None:
                print(f'识别错误: {message.message}')
                if on_error:
                    on_error(message.message)
                # 停止录音
                nonlocal mic, stream
                if stream and stream.is_active():
                    stream.stop_stream()
                    stream.close()
                if mic:
                    mic.terminate()
                sys.exit(1)
            
            def on_event(self, result: RecognitionResult) -> None:
                sentence = result.get_sentence()
                if 'text' in sentence:
                    text = sentence['text']
                    is_final = RecognitionResult.is_sentence_end(sentence)
                    print(f'识别文本: {text} {"(最终)" if is_final else ""}')
                    if on_result:
                        on_result(text, is_final)
        
        # 信号处理函数
        def signal_handler(sig, frame):
            print('\n收到停止信号，正在停止识别...')
            recognition.stop()
            print('识别已停止。')
            # 输出性能指标
            print(
                '[Metric] requestId: {}, first package delay ms: {}, last package delay ms: {}'
                .format(
                    recognition.get_last_request_id(),
                    recognition.get_first_package_delay(),
                    recognition.get_last_package_delay(),
                )
            )
            sys.exit(0)
        
        # 创建回调实例
        callback = StreamCallback()
        
        # 创建识别对象
        # nonlocal recognition
        recognition = Recognition(
            model='fun-asr-realtime',
            format='pcm',
            sample_rate=sample_rate,
            semantic_punctuation_enabled=False,
            callback=callback
        )
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        
        # 启动识别
        recognition.start()
        print("按 Ctrl+C 停止录音和识别...")
        
        try:
            # 音频数据发送循环
            while True:
                if stream:
                    data = stream.read(block_size, exception_on_overflow=False)
                    recognition.send_audio_frame(data)
                else:
                    break
        except KeyboardInterrupt:
            print("\n检测到键盘中断...")
        finally:
            recognition.stop()
        
        # 返回收集的识别结果（如果启用）
        if return_results:
            return all_results
        return None


def recognize_audio(audio_file_path: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    便捷函数：识别音频文件（非流式调用）
    
    Args:
        audio_file_path: 音频文件路径
        api_key: DashScope API密钥
        
    Returns:
        识别文本，失败返回 None
    """
    client = ASRClient(api_key=api_key)
    result = client.recognize_file(audio_file_path)
    if result and 'text' in result:
        return result['text']
    return None


def recognize_stream_mic(
    api_key: Optional[str] = None,
    on_result: Optional[Callable[[str, bool], None]] = None,
    on_error: Optional[Callable[[str], None]] = None,
    return_results: bool = True
) -> Optional[list]:
    """
    便捷函数：从麦克风实时识别（流式调用）
    
    Args:
        api_key: DashScope API密钥
        on_result: 识别结果回调函数，参数为 (text: str, is_final: bool)
        on_error: 错误回调函数，参数为 (error_message: str)
        return_results: 是否返回所有识别结果列表（默认True）
        
    Returns:
        如果 return_results=True，返回所有最终识别结果的列表
        如果 return_results=False，返回 None
    """
    client = ASRClient(api_key=api_key)
    return client.recognize_stream(
        audio_source='microphone',
        on_result=on_result,
        on_error=on_error,
        return_results=return_results
    )


if __name__ == '__main__':
    import json
    
    # 从配置文件加载API密钥
    config_path = "./private/llm_config.json"
    if os.path.exists(config_path):
        config = json.load(open(config_path, "r", encoding="utf-8"))
        api_key = config.get("qwen-235b", {}).get("api_key")
    else:
        api_key = os.getenv("DASHSCOPE_API_KEY")
    
    # 测试非流式调用
    # result = recognize_audio("./jiaran_sing_demo.mp3", api_key=api_key)
    # print(f"识别结果: {result}")
    
    # 测试流式调用（从麦克风）
    print("开始实时语音识别，请说话...")
    recognize_stream_mic(
        api_key=api_key,
        on_result=lambda text, is_final: print(f"结果: {text} {'[final]' if is_final else ''}"),
        on_error=lambda msg: print(f"错误: {msg}")
    )
