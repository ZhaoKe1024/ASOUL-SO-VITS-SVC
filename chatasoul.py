#!/user/culle/.conda/envs/llms
# -*- coding: utf_8 -*-
# @Time : 2026/04/19 23:58
# @Author: ZhaoKe
# @File : chatasoul.py
# @Software: trae
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tempfile
import shutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from asoulchat.config import (
    DEFAULT_AVATAR, DEFAULT_AUDIO, SPEAKERS, SPEAKER_LIST,
    AVATAR_CACHE_PATH, BASE_DIR
)
from asoulchat.llm_client import LLMClient
from asoulchat.asr_client import ASRClient
from asoulchat.audio_player import AudioPlayer
from asoulchat.tts_service import TTSService
from asoulchat.recorder import AudioRecorder
from asoulchat.ui_components import AvatarLabel, AudioPlayerWidget


class ModelLoaderThread(QThread):
    """模型加载线程，避免UI卡顿"""
    load_finished = pyqtSignal(bool, str)
    
    def __init__(self, tts_service, speaker, parent=None):
        super().__init__(parent)
        self.tts_service = tts_service
        self.speaker = speaker
    
    def run(self):
        try:
            success, message = self.tts_service.load_model_for_speaker(self.speaker)
            self.load_finished.emit(success, message)
        except Exception as e:
            self.load_finished.emit(False, str(e))

def text_cleaning(text):
    """清理文本，确保只包含汉字、基本标点符号、英文字母，不要出现奇怪的字符"""
    import re
    
    # 允许的字符范围：
    # \u4e00-\u9fff: 汉字
    # a-zA-Z: 英文字母
    # 0-9: 数字
    # \u3000-\u303f: 中文标点
    # \uff00-\uffef: 全角符号
    # !"#$%&'()*+,-./:;<=>?@[\]^_`{|}~: 基本英文标点
    # \s: 空白字符
    allowed_pattern = r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef!"#$%&\'()*+,-./:;<=>?@\[\\\]^_`{|}~\sa-zA-Z0-9]'
    
    # 删除不允许的字符
    cleaned = re.sub(allowed_pattern, '', text)
    
    # 标准化空白字符：将多个连续空白合并为一个空格
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # 去除首尾空白
    cleaned = cleaned.strip()
    cleaned = cleaned.replace(" ", ",")
    return cleaned

class ChatWorker(QThread):
    response_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, user_input, speaker, tts_service, llm_client, parent=None):
        super().__init__(parent)
        self.user_input = user_input
        self.speaker = speaker
        self.tts_service = tts_service
        self.llm_client = llm_client
    
    def run(self):
        try:
            system_prompt = "你是一个可爱、友善的虚拟助手，会用简短、温暖的话语回应用户。但是请注意不要生成汉字或英文字母以外的任何字符（逗号和句号除外）"
            
            response_text = self.llm_client.chat(
                prompt=self.user_input,
                system_prompt=system_prompt
            )
            # 确保回复内容里没有非中文或英文的字符
            clean_text = text_cleaning(response_text)
            print(clean_text)
            
            speaker_key = SPEAKERS.get(self.speaker, "jiaran")
            self.tts_service.current_speaker = self.speaker
            
            output_path = os.path.join(tempfile.gettempdir(), "chatasoul_response.wav")
            
            audio_path = self.tts_service.text_to_speech(
                text=clean_text,
                speaker=self.speaker,
                output_path=output_path
            )
            
            self.response_ready.emit(clean_text, audio_path or "")
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class ChataSoulWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatASoul - 虚拟助手")
        self.setFixedSize(400, 650)
        
        self.tts_service = TTSService()
        self.llm_client = LLMClient()
        self.asr_client = None
        self.audio_player = AudioPlayer()
        self.audio_recorder = AudioRecorder()
        
        self.current_audio_path = None
        self.is_processing = False
        
        try:
            self.asr_client = ASRClient()
        except Exception as e:
            print(f"ASR client initialization failed: {e}")
        
        self._setup_audio_player_callbacks()
        self._setup_recorder_callbacks()
        self._setup_ui()
        self._load_cached_avatar()
    
    def _setup_audio_player_callbacks(self):
        self.audio_player.on_progress = self._on_playback_progress
        self.audio_player.on_finished = self._on_playback_finished
        self.audio_player.on_error = self._on_playback_error
    
    def _setup_recorder_callbacks(self):
        self.audio_recorder.on_started = self._on_recording_started
        self.audio_recorder.on_finished = self._on_recording_finished
        self.audio_recorder.on_error = self._on_recording_error
    
    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        self.avatar_label = AvatarLabel(size=180)
        self.avatar_label.set_avatar(DEFAULT_AVATAR)
        self.avatar_label.avatar_changed.connect(self._on_avatar_changed)
        main_layout.addWidget(self.avatar_label, alignment=Qt.AlignCenter)
        
        self.audio_player_widget = AudioPlayerWidget()
        self.audio_player_widget.set_speakers(SPEAKER_LIST)
        self.audio_player_widget.speaker_combo.speaker_changed.connect(self._on_speaker_changed)
        self.audio_player_widget.play_clicked.connect(self._on_play_clicked)
        self.audio_player_widget.stop_clicked.connect(self._on_stop_clicked)
        self.audio_player_widget.load_model_clicked.connect(self._on_load_model_clicked)
        main_layout.addWidget(self.audio_player_widget)
        
        input_section = QWidget()
        input_layout = QVBoxLayout(input_section)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("输入消息...")
        self.input_field.setMinimumHeight(40)
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #4CAF50;
            }
        """)
        self.input_field.returnPressed.connect(self._on_send_clicked)
        input_layout.addWidget(self.input_field)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.voice_btn = QPushButton("按住说话")
        self.voice_btn.setMinimumHeight(40)
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.voice_btn.pressed.connect(self._on_voice_pressed)
        self.voice_btn.released.connect(self._on_voice_released)
        button_layout.addWidget(self.voice_btn)
        
        self.send_btn = QPushButton("发送")
        self.send_btn.setMinimumHeight(40)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.send_btn.clicked.connect(self._on_send_clicked)
        button_layout.addWidget(self.send_btn)
        
        input_layout.addLayout(button_layout)
        main_layout.addWidget(input_section)
        
        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
            }
        """)
        main_layout.addWidget(self.status_label)
    
    def _load_cached_avatar(self):
        if os.path.exists(AVATAR_CACHE_PATH):
            try:
                with open(AVATAR_CACHE_PATH, 'r', encoding='utf-8') as f:
                    cached_avatar = f.read().strip()
                    if os.path.exists(cached_avatar):
                        self.avatar_label.set_avatar(cached_avatar)
            except Exception as e:
                print(f"Failed to load cached avatar: {e}")
    
    def _on_avatar_changed(self, path):
        try:
            with open(AVATAR_CACHE_PATH, 'w', encoding='utf-8') as f:
                f.write(path)
        except Exception as e:
            print(f"Failed to cache avatar path: {e}")
    
    def _on_speaker_changed(self, speaker):
        self.tts_service.set_speaker(speaker)
        # 切换说话人时，重置模型加载状态
        is_loaded = self.tts_service.is_model_loaded(speaker)
        self.audio_player_widget.set_model_loaded(is_loaded)

    def _on_load_model_clicked(self):
        """处理加载模型按钮点击"""
        speaker = self.audio_player_widget.get_current_speaker()
        self.status_label.setText(f"正在加载 {speaker} 的模型...")

        # 使用线程加载模型以避免界面卡顿
        self.model_loader = ModelLoaderThread(self.tts_service, speaker)
        self.model_loader.load_finished.connect(self._on_model_load_finished)
        self.model_loader.start()

    def _on_model_load_finished(self, success, message):
        """模型加载完成的回调"""
        if success:
            self.audio_player_widget.set_model_loaded(True)
            self.status_label.setText(f"模型加载成功")
        else:
            self.status_label.setText(f"模型加载失败: {message}")
            QMessageBox.warning(self, "加载失败", f"无法加载模型:\n{message}")

    def _on_play_clicked(self):
        """处理播放按钮点击"""
        # 播放默认音频不需要模型
        if not self.current_audio_path or not os.path.exists(self.current_audio_path):
            # 如果没有当前音频，播放默认音频
            if os.path.exists(DEFAULT_AUDIO):
                self.audio_player.play(DEFAULT_AUDIO)
                self.audio_player_widget.set_playing(True)
            else:
                self.status_label.setText("没有可播放的音频")
            return

        # 播放当前音频（可能是TTS生成的）
        self.audio_player.play(self.current_audio_path)
        self.audio_player_widget.set_playing(True)

    def _on_stop_clicked(self):
        self.audio_player.stop()
        self.audio_player_widget.set_playing(False)
    
    def _on_playback_progress(self, progress):
        self.audio_player_widget.set_progress(progress)
    
    def _on_playback_finished(self):
        self.audio_player_widget.set_playing(False)
        self.audio_player_widget.reset_progress()
    
    def _on_playback_error(self, error_msg):
        self.status_label.setText(f"播放错误: {error_msg}")
        self.audio_player_widget.set_playing(False)
    
    def _on_voice_pressed(self):
        if self.is_processing:
            return
        self.voice_btn.setText("松开结束")
        self.status_label.setText("正在录音...")
        self.audio_recorder.start_recording(duration=10)
    
    def _on_voice_released(self):
        self.voice_btn.setText("按住说话")
        self.status_label.setText("处理中...")
        self.audio_recorder.stop_recording()
    
    def _on_recording_started(self):
        pass
    
    def _on_recording_finished(self, audio_path):
        if not self.asr_client:
            self.status_label.setText("语音识别服务不可用")
            return
        
        try:
            self.status_label.setText("正在识别语音...")
            text = self.asr_client.recognize_file(audio_path)
            
            try:
                os.remove(audio_path)
            except:
                pass
            
            if text:
                self.input_field.setText(text)
                self._process_user_input(text)
            else:
                self.status_label.setText("未能识别语音，请重试")
                
        except Exception as e:
            self.status_label.setText(f"语音识别失败: {str(e)}")
            try:
                os.remove(audio_path)
            except:
                pass
    
    def _on_recording_error(self, error_msg):
        self.status_label.setText(f"录音错误: {error_msg}")
        self.voice_btn.setText("按住说话")
    
    def _on_send_clicked(self):
        text = self.input_field.text().strip()
        if text:
            self._process_user_input(text)
            self.input_field.clear()
    
    def _process_user_input(self, text):
        if self.is_processing:
            return
        
        self.is_processing = True
        self.send_btn.setEnabled(False)
        self.voice_btn.setEnabled(False)
        self.status_label.setText("正在生成回复...")
        
        speaker = self.audio_player_widget.get_current_speaker()
        
        self.chat_worker = ChatWorker(
            user_input=text,
            speaker=speaker,
            tts_service=self.tts_service,
            llm_client=self.llm_client
        )
        self.chat_worker.response_ready.connect(self._on_response_ready)
        self.chat_worker.error_occurred.connect(self._on_response_error)
        self.chat_worker.start()
    
    def _on_response_ready(self, text, audio_path):
        self.is_processing = False
        self.send_btn.setEnabled(True)
        self.voice_btn.setEnabled(True)
        
        if audio_path and os.path.exists(audio_path):
            self.current_audio_path = audio_path
            self.audio_player.play(audio_path)
            self.audio_player_widget.set_playing(True)
            self.status_label.setText("正在播放...")
        else:
            self.status_label.setText("回复生成完成（无音频）")
    
    def _on_response_error(self, error_msg):
        self.is_processing = False
        self.send_btn.setEnabled(True)
        self.voice_btn.setEnabled(True)
        self.status_label.setText(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", f"处理请求时出错:\n{error_msg}")
    
    def closeEvent(self, event):
        self.audio_player.stop()
        self.audio_recorder.stop_recording()
        
        if self.current_audio_path and os.path.exists(self.current_audio_path):
            try:
                os.remove(self.current_audio_path)
            except:
                pass
        
        event.accept()


def main():
    import ctypes
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ChatASoul")
    except:
        pass
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    
    window = ChataSoulWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
