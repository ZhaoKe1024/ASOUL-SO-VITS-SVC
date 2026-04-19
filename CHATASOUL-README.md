# ChatASoul 开发文档

## 项目概述
ChatASoul 是一个基于 PyQt5 开发的桌面虚拟助手应用，支持语音对话、语音识别、大语言模型交互和语音合成功能。

## 新增文件列表

### 配置文件
1. `private/llm_config.json` - 大语言模型 API 配置文件

### 核心模块 (asoulchat/)
2. `asoulchat/__init__.py` - 模块初始化文件
3. `asoulchat/config.py` - 全局配置模块
4. `asoulchat/llm_client.py` - 大语言模型客户端
5. `asoulchat/asr_client.py` - 语音识别客户端 (DashScope)
6. `asoulchat/audio_player.py` - 音频播放模块
7. `asoulchat/tts_service.py` - 文本转语音服务
8. `asoulchat/recorder.py` - 麦克风录音模块
9. `asoulchat/ui_components.py` - UI 组件模块

### 主程序
10. `chatasoul.py` - 应用程序入口

## 功能特性

### 1. 头像显示
- 默认显示 `jiaran.jpg` 作为头像
- 支持右键菜单更换头像
- 头像路径缓存到本地配置

### 2. 语音播放条
- 支持选择说话人（嘉然、贝拉、乃琳、心宜、思诺）
- 显示播放进度条
- 支持播放默认音频和生成的回复音频

### 3. 输入模块
- 支持文字输入框输入
- 支持按住说话按钮进行语音输入
- 语音识别调用 DashScope API
- 用户输入后自动触发 LLM 生成回复并语音播放

## 依赖库

运行前需要安装以下 Python 库（部分库可能需要在 conda 环境 `torch-0` 中安装）：

```
PyQt5              # GUI 框架
openai             # 大语言模型 API 客户端
dashscope          # 阿里云语音识别服务
pyaudio              # 麦克风录音（Windows 需要特定安装方式）
pygame             # 音频播放
librosa            # 音频处理
soundfile          # 音频文件读写
numpy              # 数值计算
```

### 特殊依赖安装说明

**PyAudio (Windows):**
由于 PyAudio 在 Windows 上直接 pip 安装可能会失败，建议：
1. 下载预编译的 whl 文件：https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
2. 根据 Python 版本选择对应的 whl 文件
3. 使用 `pip install <path_to_whl>` 安装

## 环境配置

1. 确保已激活 conda 环境：`conda activate torch-0`
2. 安装缺失的依赖库（见上文）
3. 配置 `private/llm_config.json` 中的 API 密钥
4. 设置环境变量 `DASHSCOPE_API_KEY`（用于语音识别）

## 运行方式

```bash
python chatasoul.py
```

## 注意事项

1. 不要删除或修改现有文件，只能创建新文件
2. 所有功能模块放在 `asoulchat/` 目录下
3. 程序入口在 `chatasoul.py`
4. 需要预先配置好 API 密钥才能使用 LLM 和 ASR 功能
5. 语音合成需要加载 So-VITS 模型，确保模型文件存在
