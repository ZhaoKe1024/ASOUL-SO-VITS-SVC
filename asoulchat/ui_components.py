import os
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage, QIcon, QFont
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QComboBox, QLineEdit, QProgressBar, QMenu, QFileDialog,
    QFrame, QSizePolicy, QStyleOption, QStyle
)


class AvatarLabel(QLabel):
    avatar_changed = pyqtSignal(str)
    
    def __init__(self, parent=None, size=200):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 2px solid #ddd;
                border-radius: 10px;
                background-color: #f5f5f5;
            }
        """)
        self.current_avatar = None
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def set_avatar(self, image_path):
        if not os.path.exists(image_path):
            return False

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return False

        target_size = self.width() - 20
        scaled_pixmap = pixmap.scaled(
            target_size,
            target_size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self.setPixmap(scaled_pixmap)
        self.current_avatar = image_path
        self.avatar_changed.emit(image_path)
        return True
    
    def show_context_menu(self, position):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #ddd;
                padding: 5px;
            }
            QMenu::item {
                padding: 5px 20px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
            }
        """)
        
        change_action = menu.addAction("更换头像")
        action = menu.exec_(self.mapToGlobal(position))
        
        if action == change_action:
            self.change_avatar()
    
    def change_avatar(self):
        pictures_dir = os.path.expanduser("~/Pictures")
        if not os.path.exists(pictures_dir):
            pictures_dir = os.path.expanduser("~")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择头像图片",
            pictures_dir,
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)"
        )
        
        if file_path:
            self.set_avatar(file_path)


class SpeakerComboBox(QComboBox):
    speaker_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(100)
        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                min-height: 25px;
            }
            QComboBox:hover {
                border-color: #aaa;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #ddd;
                background-color: white;
                selection-background-color: #e0e0e0;
            }
            QComboBox QAbstractItemView::item {
                min-height: 25px;
                padding: 5px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #e0e0e0;
            }
        """)
        
        self.currentTextChanged.connect(self._on_speaker_changed)
    
    def set_speakers(self, speakers):
        self.clear()
        for speaker in speakers:
            self.addItem(speaker)
    
    def _on_speaker_changed(self, text):
        self.speaker_changed.emit(text)


class AudioPlayerWidget(QFrame):
    play_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    load_model_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
        """)

        # 先初始化状态变量，再设置UI
        self.is_playing = False
        self.model_loaded = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        self.speaker_combo = SpeakerComboBox()
        layout.addWidget(self.speaker_combo)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: white;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar, stretch=1)

        # 右侧按钮组 - 垂直布局
        button_container = QWidget()
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(4)

        # 加载模型按钮
        self.load_model_btn = QPushButton("加载模型")
        self.load_model_btn.setFixedSize(70, 32)
        self.load_model_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #4CAF50;
                border-radius: 4px;
                background-color: #4CAF50;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                border-color: #cccccc;
                color: #666666;
            }
        """)
        self.load_model_btn.clicked.connect(self._on_load_model_clicked)
        button_layout.addWidget(self.load_model_btn)

        # 播放按钮
        self.play_btn = QPushButton("播放")
        self.play_btn.setFixedSize(70, 32)
        self.play_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #2196F3;
                border-radius: 4px;
                background-color: #2196F3;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                border-color: #cccccc;
                color: #666666;
            }
        """)
        self.play_btn.clicked.connect(self._on_play_clicked)
        button_layout.addWidget(self.play_btn)

        layout.addWidget(button_container)

    def _on_load_model_clicked(self):
        self.load_model_clicked.emit()

    def _on_play_clicked(self):
        if self.is_playing:
            self.is_playing = False
            self.play_btn.setText("播放")
            self.stop_clicked.emit()
        else:
            self.is_playing = True
            self.play_btn.setText("停止")
            self.play_clicked.emit()

    def set_model_loaded(self, loaded):
        self.model_loaded = loaded
        if loaded:
            self.load_model_btn.setText("已加载")
            self.load_model_btn.setEnabled(False)
        else:
            self.load_model_btn.setText("加载模型")
            self.load_model_btn.setEnabled(True)

    def set_playing(self, playing):
        self.is_playing = playing
        if playing:
            self.play_btn.setText("停止")
        else:
            self.play_btn.setText("播放")

    def set_progress(self, value):
        self.progress_bar.setValue(value)

    def reset_progress(self):
        self.progress_bar.setValue(0)

    def set_speakers(self, speakers):
        self.speaker_combo.set_speakers(speakers)

    def get_current_speaker(self):
        return self.speaker_combo.currentText()

    def set_speaker(self, speaker):
        index = self.speaker_combo.findText(speaker)
        if index >= 0:
            self.speaker_combo.setCurrentIndex(index)

    def set_enabled(self, enabled):
        self.play_btn.setEnabled(enabled)
        if not enabled and self.is_playing:
            self.is_playing = False
            self.play_btn.setText("播放")
    
    def _set_play_icon(self):
        style = self.play_btn.style()
        if self.is_playing:
            icon = style.standardIcon(QStyle.SP_MediaPause)
        else:
            icon = style.standardIcon(QStyle.SP_MediaPlay)
        self.play_btn.setIcon(icon)
        self.play_btn.setIconSize(self.play_btn.size() * 0.6)
    
    def _on_play_clicked(self):
        if self.is_playing:
            self.is_playing = False
            self._set_play_icon()
            self.stop_clicked.emit()
        else:
            self.is_playing = True
            self._set_play_icon()
            self.play_clicked.emit()
    
    def _on_stop_clicked(self):
        if self.is_playing:
            self.is_playing = False
            self._set_play_icon()
        self.stop_clicked.emit()
    
    def set_playing(self, playing):
        self.is_playing = playing
        self._set_play_icon()
    
    def set_progress(self, value):
        self.progress_bar.setValue(value)
    
    def reset_progress(self):
        self.progress_bar.setValue(0)
    
    def set_speakers(self, speakers):
        self.speaker_combo.set_speakers(speakers)
    
    def get_current_speaker(self):
        return self.speaker_combo.currentText()
    
    def set_speaker(self, speaker):
        index = self.speaker_combo.findText(speaker)
        if index >= 0:
            self.speaker_combo.setCurrentIndex(index)
    
    def set_enabled(self, enabled):
        self.play_btn.setEnabled(enabled)
        if not enabled and self.is_playing:
            self.is_playing = False
            self._set_play_icon()
