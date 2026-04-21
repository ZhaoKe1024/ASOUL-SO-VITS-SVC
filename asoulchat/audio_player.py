#!/user/culle/.conda/envs/llms
# -*- coding: utf_8 -*-
# @Time : 2026/04/19 23:58
# @Author: ZhaoKe
# @File : audio_player.py
# @Software: trae
import os
import sys
from PyQt5.QtCore import QThread, pyqtSignal


class AudioPlayerThread(QThread):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    
    def __init__(self, audio_path, parent=None):
        super().__init__(parent)
        self.audio_path = audio_path
        self._is_running = True
        self.duration = 0
        self.current_position = 0
    
    def run(self):
        try:
            import pygame
            pygame.mixer.init()
            
            pygame.mixer.music.load(self.audio_path)
            
            sound = pygame.mixer.Sound(self.audio_path)
            self.duration = int(sound.get_length() * 1000)
            
            pygame.mixer.music.play()
            
            clock = pygame.time.Clock()
            
            while pygame.mixer.music.get_busy() and self._is_running:
                self.current_position = pygame.mixer.music.get_pos()
                if self.duration > 0:
                    progress = int((self.current_position / self.duration) * 100)
                    self.progress.emit(min(progress, 100))
                clock.tick(10)
            
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        self._is_running = False
        try:
            import pygame
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except:
            pass


class AudioPlayer:
    def __init__(self):
        self.current_thread = None
        self.on_progress = None
        self.on_finished = None
        self.on_error = None
    
    def play(self, audio_path):
        if not os.path.exists(audio_path):
            if self.on_error:
                self.on_error(f"Audio file not found: {audio_path}")
            return
        
        self.stop()
        
        self.current_thread = AudioPlayerThread(audio_path)
        
        if self.on_progress:
            self.current_thread.progress.connect(self.on_progress)
        if self.on_finished:
            self.current_thread.finished.connect(self.on_finished)
        if self.on_error:
            self.current_thread.error.connect(self.on_error)
        
        self.current_thread.start()
    
    def stop(self):
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()
            self.current_thread.wait(2000)
            self.current_thread = None
    
    def is_playing(self):
        return self.current_thread is not None and self.current_thread.isRunning()
