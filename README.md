A-SOUL SVC Project

This is a model open-source repository of SO-VITS-SVC4.1 for A-SOUL and members of Shining Stage (Zhijiang Entertainment).

For the complete code project, please refer to SO-VITS-SVC4.1: [https://github.com/svc-develop-team/so-vits-svc](https://github.com/svc-develop-team/so-vits-svc).

## Model Open-Source

🤗Model_on_Huggingface: [https://huggingface.co/CullenZhao/ASOUL-SVC](https://huggingface.co/CullenZhao/ASOUL-SVC)

♦ Model_on_Modelscope: [https://www.modelscope.cn/models/ZhaoKe1024/ASOUL-SVC](https://www.modelscope.cn/models/ZhaoKe1024/ASOUL-SVC)

## Inference

**Step 1: Download video from bilibili**:

[Downkyi github link: https://github.com/leiurayer/downkyi/releases](https://github.com/leiurayer/downkyi/releases)

**Step 2: mp4 to wav**:

Because the ffmpeg can not support space in filename, so we rename it first.
```python
os.rename(fname, fname.replace(" ", "_"))
# audioprocess.py: ffmpeg_mp4_to_wav_separate()
```

```shell
ffmpeg -i input.mp4 -ar 44100 -f wav output.wav
```

**Step 3: Remove bgm from wav**:

Use software UVR5:

[https://ultimatevocalremover.com/](https://ultimatevocalremover.com/)

**Step 4: Inference script**:

For the complete project, please refer to SO-VITS-SVC4.1: [https://github.com/svc-develop-team/so-vits-svc](https://github.com/svc-develop-team/so-vits-svc).

Setting the basic information, and then modify the code in the script inference_main.py main() as follows:
```python
model_root_dir = "D:/A-SOUL-SVC/jiaran/"  # your model root directory
wav_root_dir = "D:/music/vocals/"  # your wav root directory
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

**Step 5: Run the inference script**:

```shell
python inference_main.py
```

## Dataset
The training set is sourced from Baidu Net Disk of "奶粉_day0" (bilibili id: 5273959).

Guideline video: [【AI翻唱】SO-VITS-SVC4.1本地模型制作教程（整合包教程）](https://www.bilibili.com/video/BV1ydVLzTENC)

**Directly use the Jiaran training corpus that I have processed**:

FULL_Dataset_on_Huggingface: [https://huggingface.co/datasets/CullenZhao/JiaranDianaVioceCorpus](https://huggingface.co/datasets/CullenZhao/JiaranDianaVioceCorpus)

Github Link: [https://github.com/ZhaoKe1024/JiaranDianaVoiceCorpus](https://github.com/ZhaoKe1024/JiaranDianaVoiceCorpus)

Due to the need for data preprocessing before training, chinese characters can not be used in the wav file names, so they need to be renamed:

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

## Training
SO-VITS-SVC4.1 is adopted from the project: https://github.com/svc-develop-team/so-vits-svc.

Thanks to the author, 羽毛布団 (bilibili id: 3493141443250876), for the project integration package [https://www.yuque.com/umoubuton/ueupp5](https://www.yuque.com/umoubuton/ueupp5).
