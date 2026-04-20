# A-SOUL SVC 项目
[English](./README.md)| 简体中文

这是一个针对 A-SOUL（嘉然、贝拉、乃琳） 以及闪耀舞台（心宜&思诺） 成员的开源 SO-VITS-SVC4.1 模型仓库（不完整版）。
除了作为 AI-ASOUL歌手 功能之外，还有另一重点在于利用该模型开发“实时对话软件”，包含基于语音识别（目前采用API云服务）、大语言模型（API云服务）、和 TTS模型（+Voice Clone）的“电子宠物”。

关于SVC模型完整的代码项目请参考 SO-VITS-SVC4.1：[https://github.com/svc-develop-team/so-vits-svc](https://github.com/svc-develop-team/so-vits-svc)。

## 模型开源

🤗HuggingFace模型：[https://huggingface.co/CullenZhao/ASOUL-SVC](https://huggingface.co/CullenZhao/ASOUL-SVC)

♦ ModelScope模型：[https://www.modelscope.cn/models/ZhaoKe1024/ASOUL-SVC](https://www.modelscope.cn/models/ZhaoKe1024/ASOUL-SVC)

## SVC推理

**步骤 1：从哔哩哔哩下载视频**：

[Downkyi GitHub 链接：https://github.com/leiurayer/downkyi/releases](https://github.com/leiurayer/downkyi/releases)

**步骤 2：将 mp4 转换为 wav**：

由于 ffmpeg 不支持文件名中包含空格，因此我们先重命名文件。
```python
os.rename(fname, fname.replace(" ", "_"))
# audioprocess.py: ffmpeg_mp4_to_wav_separate()
```

```shell
ffmpeg -i input.mp4 -ar 44100 -f wav output.wav
```

**步骤 3：从 wav 中去除背景音乐**：

使用软件 UVR5：

[https://ultimatevocalremover.com/](https://ultimatevocalremover.com/)

**步骤 4：推理脚本**：

完整的项目请参考 SO-VITS-SVC4.1：[https://github.com/svc-develop-team/so-vits-svc](https://github.com/svc-develop-team/so-vits-svc)。

设置基本信息，然后按如下方式修改脚本 inference_main.py 中的 main() 代码：
```python
model_root_dir = "D:/A-SOUL-SVC/jiaran/"  # 您的模型根目录
wav_root_dir = "D:/music/vocals/"  # 您的 wav 根目录
wav_list = [
    "45_338-【洛天依x乐正绫】《三月雨2024》_“空余忆，良辰美景多可惜”【南北组】【原创PV付】-480P_标清-AVC_(Vocals).wav"
    "35_5-【ChiliChill】橙子汽水_Studio_Live-480P_标清-AVC_(Vocals).wav",
    "20_1-今天不卷了，屑屑-480P_标清-AVC_(Vocals).wav"
]

# ......
# ......

parser.add_argument('-m', '--model_path', type=str, default=os.path.join(model_root_dir, "G_72000.pth"), help='模型路径')
parser.add_argument('-c', '--config_path', type=str, default=os.path.join(model_root_dir, "config.json"), help='配置文件路径')
# ......
parser.add_argument('-n', '--clean_names', type=str, nargs='+', default=[os.path.join(wav_root_dir, wav) for wav in wav_list], help='wav文件名列表，放在raw文件夹下')

# ......
```

**步骤 5：运行推理脚本**：

```shell
python inference_main.py
```

## 数据集

训练集来源于哔哩哔哩用户"奶粉_day0"（哔哩哔哩 id：5273959）的百度网盘。

教程视频：[【AI翻唱】SO-VITS-SVC4.1本地模型制作教程（整合包教程）](https://www.bilibili.com/video/BV1ydVLzTENC)

**直接使用我已处理好的嘉然训练语料**：

HuggingFace 完整数据集：[https://huggingface.co/datasets/CullenZhao/JiaranDianaVioceCorpus](https://huggingface.co/datasets/CullenZhao/JiaranDianaVioceCorpus)

GitHub 链接：[https://github.com/ZhaoKe1024/JiaranDianaVoiceCorpus](https://github.com/ZhaoKe1024/JiaranDianaVoiceCorpus)

由于训练前需要对数据进行预处理，wav 文件名中不能使用中文字符，因此需要重命名：

```python
python audioprocess.py

def rename_clips():
    update_name_list = []
    for ind, item in enumerate(os.listdir("./dataset_raw/sinuo/")):
        ......
        raise NotImplementedError
    for item in update_name_list:
        os.rename(item[0], item[1])

if __name__ == '__main__':
    rename_clips()
```

## 训练

SO-VITS-SVC4.1 采用自项目：https://github.com/svc-develop-team/so-vits-svc。

感谢作者 羽毛布団（哔哩哔哩 id：3493141443250876）提供的项目整合包 [https://www.yuque.com/umoubuton/ueupp5](https://www.yuque.com/umoubuton/ueupp5)。

# Chat_with_ASOUL App
由于 so-vits-svc4.1 似乎无法直接作为 TTS (Text to Speech) 模型使用，因此要安装下面三个库：
```shell
pip install edge_tts langdetect praat-parselmouth
```
edge_tts 是一个用于将文本转换为语音的库，会将用户的输入文本通过公开API转换为语音。
langdetect 是一个用于检测文本语言的库，praat-parselmouth 是一个用于将 praat 封装为 Python 的解析语音文件的库。

实际执行的流程为：
1 用户输入文本，调用大模型，返回回答，然后调用 edge_tts 库，将回答转换为语音。
2 加载我们训练好的 SO-VITS-SVC 模型(./utils_infer.py slice_inference())，将语音转换为目标音色。
3 播放目标音色的回答

运行App：
```shell
python chatasoul.py
```

## 对原代码的修改
由于 so-vits-svc4.1 项目的 utils.py 中有一个 faiss库始终无法安装成功，于是我复制 utils.py并改名为 utils_infer.py，删去了里面如下两行的 导入和相关函数，
```python
import faiss
......
def train_index(spk_name,root_dir = "dataset/44k/"):  #from: RVC https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI
    ......
......
```
然后同步修改：
models.py & inference/infer_tool.py
```python
# import utils
import utils_infer as utils
```
