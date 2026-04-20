import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_AVATAR = os.path.join(BASE_DIR, "jiaran.jpg")
DEFAULT_AUDIO = os.path.join(BASE_DIR, "jiaran_sing_demo.mp3")

SPEAKERS = {
    "嘉然": "jiaran",
    "贝拉": "beila",
    "乃琳": "nailin",
    "心宜": "xinyi",
    "思诺": "sinuo"
}

SPEAKER_LIST = list(SPEAKERS.keys())

MODEL_PATHS = {
    "jiaran": os.path.join(BASE_DIR, "models", "44k_jiaran", "G_72000.pth"),
    "beila": os.path.join(BASE_DIR, "models", "44k_beilanailin", "G_65600.pth"),
    "nailin": os.path.join(BASE_DIR, "models", "44k_beilanailin", "G_65600.pth"),
    "xinyi": os.path.join(BASE_DIR, "models", "44k_xinyi", "G_92400.pth"),
    "sinuo": os.path.join(BASE_DIR, "models", "44k_sinuo", "G_74400.pth"),
}

CONFIG_PATHS = {
    "jiaran": os.path.join(BASE_DIR, "models", "44k_jiaran", "config.json"),
    "beila": os.path.join(BASE_DIR, "models", "44k_beilanailin", "config.json"),
    "nailin": os.path.join(BASE_DIR, "models", "44k_beilanailin", "config.json"),
    "xinyi": os.path.join(BASE_DIR, "models", "44k_xinyi", "config.json"),
    "sinuo": os.path.join(BASE_DIR, "models", "44k_sinuo", "config.json"),
}

LLM_CONFIG_PATH = os.path.join(BASE_DIR, "private", "llm_config.json")

RECORDING_DURATION = 10
RECORDING_SAMPLE_RATE = 16000

PREFERENCES_DIR = os.path.expanduser("~/.chatasoul")
if not os.path.exists(PREFERENCES_DIR):
    os.makedirs(PREFERENCES_DIR)

AVATAR_CACHE_PATH = os.path.join(PREFERENCES_DIR, "avatar_path.txt")
