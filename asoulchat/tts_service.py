import os
import sys
import subprocess
import glob
import librosa
import soundfile

from .config import BASE_DIR, MODEL_PATHS, SPEAKERS

sys.path.insert(0, BASE_DIR)

try:
    from inference.infer_tool import Svc
except ImportError as e:
    print(f"Warning: Could not import Svc: {e}")
    Svc = None


class TTSService:
    def __init__(self):
        self.models = {}
        self.current_speaker = "嘉然"
        self.current_speaker_loaded = None
        # 不再在启动时自动加载模型
    
    def load_model_for_speaker(self, speaker):
        """为指定的说话人加载模型"""
        if Svc is None:
            print("Warning: Svc not available, TTS will not work")
            return False, "Svc not available"
        
        speaker_key = SPEAKERS.get(speaker)
        if not speaker_key:
            return False, f"Unknown speaker: {speaker}"
        
        # 如果已经加载了该模型，直接返回成功
        if speaker_key in self.models:
            self.current_speaker_loaded = speaker
            return True, f"Model for {speaker} already loaded"
        
        model_dir = MODEL_PATHS.get(speaker_key)
        if not model_dir or not os.path.exists(model_dir):
            return False, f"Model directory not found for {speaker}"
        
        try:
            model_files = glob.glob(os.path.join(model_dir, "*.pth"))
            config_files = glob.glob(os.path.join(model_dir, "*.json"))
            
            if not model_files or not config_files:
                return False, f"Model files not found for {speaker}"
            
            model_path = model_files[0]
            config_path = config_files[0]
            
            model = Svc(
                model_path,
                config_path,
                device=None,
                cluster_model_path="",
                nsf_hifigan_enhance=False,
                diffusion_model_path="",
                diffusion_config_path="",
                shallow_diffusion=False,
                only_diffusion=False,
                spk_mix_enable=False,
                feature_retrieval=False
            )
            
            self.models[speaker_key] = model
            self.current_speaker_loaded = speaker
            print(f"Loaded model for {speaker}")
            return True, f"Model for {speaker} loaded successfully"
            
        except Exception as e:
            error_msg = f"Failed to load model for {speaker}: {e}"
            print(error_msg)
            return False, error_msg
    
    def is_model_loaded(self, speaker):
        """检查指定说话人的模型是否已加载"""
        speaker_key = SPEAKERS.get(speaker)
        return speaker_key in self.models
    
    def unload_all_models(self):
        """卸载所有已加载的模型"""
        self.models.clear()
        self.current_speaker_loaded = None
        print("All models unloaded")
    
    def text_to_speech(self, text, speaker=None, output_path=None):
        if speaker is None:
            speaker = self.current_speaker
        
        speaker_key = SPEAKERS.get(speaker, "jiaran")
        
        if output_path is None:
            output_path = os.path.join(BASE_DIR, "temp_tts_output.wav")
        
        try:
            self._generate_tts(text, speaker_key, output_path)
            return output_path
        except Exception as e:
            print(f"TTS generation failed: {e}")
            return None
    
    def _generate_tts(self, text, speaker_key, output_path):
        import tempfile
        import numpy as np
        
        tts_wav = os.path.join(BASE_DIR, "temp_tts.wav")
        
        try:
            subprocess.run([
                sys.executable,
                os.path.join(BASE_DIR, "edgetts", "tts.py"),
                text,
                "zh",
                "+0%",
                "+0%"
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Edge TTS failed: {e}")
        
        if not os.path.exists(tts_wav):
            raise FileNotFoundError("TTS output file not created")
        
        y, sr = librosa.load(tts_wav, sr=None)
        target_sr = 44100
        if sr != target_sr:
            y = librosa.resample(y, orig_sr=sr, target_sr=target_sr)
        
        soundfile.write(tts_wav, y, target_sr, subtype="PCM_16")
        
        model = self.models.get(speaker_key)
        if model is None:
            os.rename(tts_wav, output_path)
            return
        
        try:
            audio = model.slice_inference(
                tts_wav,
                sid=speaker_key,
                vc_transform=0,
                slice_db=-40,
                cluster_ratio=0,
                auto_f0=False,
                noise_scale=0.4,
                pad_seconds=0.5,
                cl_num=0,
                lg_num=0,
                lgr_num=0.75,
                f0_predictor="pm",
                enhancer_adaptive_key=0,
                cr_threshold=0.05,
                k_step=100,
                use_spk_mix=False,
                second_encoding=False,
                loudness_envelope_adjustment=0
            )
            
            model.clear_empty()
            
            soundfile.write(output_path, audio, model.target_sample, format="wav")
            
        finally:
            if os.path.exists(tts_wav):
                try:
                    os.remove(tts_wav)
                except:
                    pass
    
    def set_speaker(self, speaker):
        if speaker in SPEAKERS:
            self.current_speaker = speaker
            return True
        return False
    
    def get_available_speakers(self):
        return list(SPEAKERS.keys())
