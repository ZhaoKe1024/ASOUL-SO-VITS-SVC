# -*- coding: utf-8 -*-
# @Author : ZhaoKe
# @Time : 2026-03-24 0:48
import os
import pdb
def ffmpeg_process():
    keywords = ["嘉然", "乃琳", "贝拉"]
    fname_list = []
    root_dir = "H:/videos/mp4files/"
    name_list = []
    for item in os.listdir(root_dir):
        if not item.endswith(".mp4"):
            continue
        for key in keywords:
            if key in item:
                name_list.append(os.path.join(root_dir, item[:-4].replace(".", "_")+".wav"))
                fname_list.append(os.path.join(root_dir, item))
                break
    for item in fname_list:
        print(item)
        # os.rename(item, item.replace(" ", "_"))
    for i in range(len(name_list)):
        # print()
        print("ffmpeg -i " + fname_list[i] + " -f wav -ar 44100 " + name_list[i])
        os.system("ffmpeg -i " + fname_list[i] + " -f wav -ar 44100 " + name_list[i])

def rename_clips():
    key = "xinyi"  # your speaker
    update_name_list = []
    for ind, item in enumerate(os.listdir(f"./dataset_raw/{key}/")):
        new_name = ("000"+str(ind))[-4:]+".wav"
        update_name_list.append((os.path.join(f"./dataset_raw/{key}/",item), os.path.join(f"./dataset_raw/{key}/",new_name)))
    pdb.set_trace()
    for item in update_name_list:
        os.rename(item[0], item[1])

def ffmpeg_mp4_to_wav_separate():
    """ffmpeg can not support space in filename, so we rename it first."""
    fname_list = []
    root_dir = "H:/videos/mp4files/"
    name_list = []
    cnt = 0
    for item in os.listdir(root_dir):
        # file_dir = os.path.join(root_dir, item)
        fname_list.append(os.path.join(root_dir, item))
        name_list.append(item)

    print(cnt, '/', len(fname_list))
    for item in fname_list:
        print(item)
    for ind, item in enumerate(name_list):
        if " " in name_list[ind]:
            # print(item, item.replace(" ", "_"))
            os.rename(os.path.join(root_dir, item), os.path.join(root_dir, item.replace(" ", "_")))
    
    # for i in range(len(fname_list)):
    #     # print()
    #     try:

    #         if os.path.exists(fname_list[i].replace(".mp4", ".wav")):
    #             continue
    #         print("ffmpeg -i " + fname_list[i] + " -f wav -ar 44100 " + fname_list[i].replace(".mp4", ".wav"))
    #         os.system("ffmpeg -i " + fname_list[i] + " -f wav -ar 44100 " + fname_list[i].replace(".mp4", ".wav"))
    #     except Exception as e:
    #         print(e)

if __name__ == '__main__':
    ffmpeg_mp4_to_wav_separate()
    # rename_clips()
