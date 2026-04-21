#!/user/culle/.conda/envs/llms
# -*- coding: utf_8 -*-
# @Time : 2026/04/19 23:59
# @Author: ZhaoKe
# @File : recorder.py
# @Software: trae
import os
import wave
import tempfile
import time
from PyQt5.QtCore import QThread, pyqtSignal


class RecordingThread(QThread):
    started = pyqtSignal()
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, duration=10, sample_rate=16000, channels=1, parent=None):
        super().__init__(parent)
        self.duration = duration
        self.sample_rate = sample_rate
        self.channels = channels
        self._is_running = True
    
    def run(self):
        try:
            import pyaudio
            
            self.started.emit()
            
            audio = pyaudio.PyAudio()
            
            format = pyaudio.paInt16
            chunk = 1024
            
            stream = audio.open(
                format=format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            frames = []
            start_time = time.time()
            
            while self._is_running and (time.time() - start_time) < self.duration:
                try:
                    data = stream.read(chunk, exception_on_overflow=False)
                    frames.append(data)
                except Exception as e:
                    self.error.emit(f"Recording error: {str(e)}")
                    break
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            if frames:
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=".wav", delete=False, dir=tempfile.gettempdir()
                )
                temp_file.close()
                
                wf = wave.open(temp_file.name, 'wb')
                wf.setnchannels(self.channels)
                wf.setsampwidth(audio.get_sample_size(format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(b''.join(frames))
                wf.close()
                
                self.finished.emit(temp_file.name)
            else:
                self.error.emit("No audio recorded")
                
        except ImportError as e:
            self.error.emit(f"PyAudio not installed: {str(e)}")
        except Exception as e:
            self.error.emit(f"Recording failed: {str(e)}")
    
    def stop(self):
        self._is_running = False


class AudioRecorder:
    def __init__(self):
        self.recording_thread = None
        self.on_started = None
        self.on_finished = None
        self.on_error = None
    
    def start_recording(self, duration=10, sample_rate=16000):
        if self.recording_thread and self.recording_thread.isRunning():
            return False
        
        self.recording_thread = RecordingThread(duration, sample_rate)
        
        if self.on_started:
            self.recording_thread.started.connect(self.on_started)
        if self.on_finished:
            self.recording_thread.finished.connect(self.on_finished)
        if self.on_error:
            self.recording_thread.error.connect(self.on_error)
        
        self.recording_thread.start()
        return True
    
    def stop_recording(self):
        if self.recording_thread and self.recording_thread.isRunning():
            self.recording_thread.stop()
            self.recording_thread.wait(3000)
    
    def is_recording(self):
        return self.recording_thread is not None and self.recording_thread.isRunning()


def record_audio(duration=10, sample_rate=16000, output_path=None):
    try:
        import pyaudio
        import wave
        
        audio = pyaudio.PyAudio()
        format = pyaudio.paInt16
        channels = 1
        chunk = 1024
        
        stream = audio.open(
            format=format,
            channels=channels,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk
        )
        
        print(f"Recording for {duration} seconds...")
        frames = []
        
        for i in range(0, int(sample_rate / chunk * duration)):
            data = stream.read(chunk, exception_on_overflow=False)
            frames.append(data)
        
        print("Recording finished")
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        if output_path is None:
            output_path = tempfile.mktemp(suffix=".wav")
        
        wf = wave.open(output_path, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(format))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        return output_path
        
    except ImportError:
        raise RuntimeError("PyAudio is required for recording")
    except Exception as e:
        raise RuntimeError(f"Recording failed: {e}")
