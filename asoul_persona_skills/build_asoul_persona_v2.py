#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A-SOUL 多角色人格构建与对话系统 V2
====================================
支持嘉然、贝拉、乃琳三个角色
自动检测缓存，支持快速启动

使用方法:
    python build_asoul_persona_v2.py [角色名]
    
    角色名可选: 嘉然(默认) | 贝拉 | 乃琳
"""

import os
import re
import sys
import json
import glob
from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime

# =============================================================================
# 角色配置
# =============================================================================

IDOL_CONFIGS = {
    "嘉然": {
        "idol_name": "嘉然",
        "idol_english_name": "Diana",
        "fan_name": "嘉心糖",
        "represent_color": "粉色",
        "symbol": "🍓",
        "markers": {
            "self_reference": ["然然", "嘉然", "我", "人家"],
            "fan_reference": ["嘉心糖", "糖糖"],
            "particles": ["呢", "呀", "啦", "吧", "嘛", "啊", "哦", "哟", "哈", "哼", "嘿嘿", "嘻嘻"],
            "emotions": ["呜呜", "555", "啊啊啊", "呜呜呜"],
        },
        "excluded_members": ["向晚", "贝拉", "乃琳", "珈乐"],
    },
    "贝拉": {
        "idol_name": "贝拉",
        "idol_english_name": "Bella",
        "fan_name": "贝极星",
        "represent_color": "蓝色",
        "symbol": "⭐",
        "markers": {
            "self_reference": ["贝拉", "我", "咱", "本小姐"],
            "fan_reference": ["贝极星", "星星"],
            "particles": ["呢", "啦", "吧", "啊", "哦", "哟", "嘛", "哼", "嘿嘿"],
            "emotions": ["哼", "哈哈", "嘿嘿"],
        },
        "excluded_members": ["向晚", "嘉然", "乃琳", "珈乐"],
    },
    "乃琳": {
        "idol_name": "乃琳",
        "idol_english_name": "Eileen",
        "fan_name": "奶淇琳",
        "represent_color": "紫色",
        "symbol": "🦊",
        "markers": {
            "self_reference": ["乃琳", "我", "人家", "本姑娘"],
            "fan_reference": ["奶淇琳", "淇琳"],
            "particles": ["呢", "呀", "啦", "吧", "啊", "哦", "哟", "嘛", "嘻嘻", "嘿嘿"],
            "emotions": ["嘻嘻", "哈哈", "嘿嘿"],
        },
        "excluded_members": ["向晚", "嘉然", "贝拉", "珈乐"],
    },
}

# =============================================================================
# 工具类
# =============================================================================

class SRTParser:
    """SRT 字幕文件解析器"""
    TIMESTAMP_RE = re.compile(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')
    
    @classmethod
    def parse_file(cls, filepath: str) -> List[Dict[str, Any]]:
        entries = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"[警告] 无法读取文件 {filepath}: {e}")
            return entries
        
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) < 2:
                continue
            try:
                index = int(lines[0].strip())
            except ValueError:
                continue
            
            if not cls.TIMESTAMP_RE.match(lines[1].strip()):
                continue
            
            time_parts = lines[1].strip().split(' --> ')
            start_time, end_time = time_parts[0], time_parts[1]
            
            text_lines = lines[2:]
            text = ' '.join(line.strip() for line in text_lines if line.strip())
            text = re.sub(r'<[^>]+>', '', text)
            
            if text:
                entries.append({
                    'index': index, 'start_time': start_time, 'end_time': end_time,
                    'text': text, 'source': os.path.basename(filepath)
                })
        return entries


def is_likely_idol(text: str, idol_config: Dict) -> tuple[bool, float]:
    """判断这句话是否可能是指定偶像说的"""
    if not text or len(text) < 3:
        return False, 0.0
    if len(text) > 200:
        return False, 0.0
    
    score = 0.0
    markers = idol_config["markers"]
    
    # 检查自我引用
    for ref in markers["self_reference"]:
        if ref in text:
            score += 0.2
    
    # 检查粉丝引用
    for ref in markers["fan_reference"]:
        if ref in text:
            score += 0.3
    
    # 检查语气词
    particle_count = 0
    for particle in markers["particles"]:
        if particle in text:
            particle_count += 1
    if particle_count >= 2:
        score += 0.15
    
    # 排除其他成员
    excluded = idol_config.get("excluded_members", [])
    for member in excluded:
        if member in text:
            score -= 0.2
    
    is_match = score >= 0.3
    return is_match, min(score, 1.0)


def filter_idol_quotes(all_entries: List[Dict], idol_config: Dict) -> List[Dict]:
    """筛选出可能是指定偶像说的台词"""
    idol_quotes = []
    idol_name = idol_config["idol_name"]
    print(f"\n[筛选] 正在使用启发式规则筛选{idol_name}的台词...")
    
    for entry in all_entries:
        text = entry['text']
        is_match, confidence = is_likely_idol(text, idol_config)
        if is_match:
            entry_copy = entry.copy()
            entry_copy['speaker'] = idol_name
            entry_copy['confidence'] = confidence
            idol_quotes.append(entry_copy)
    
    idol_quotes.sort(key=lambda x: x['confidence'], reverse=True)
    print(f"[完成] 筛选出 {len(idol_quotes)} 条{idol_name}的台词")
    return idol_quotes


# =============================================================================
# 主流程
# =============================================================================

def check_existing_data(output_dir: str, idol_name: str) -> tuple[bool, Optional[List], Optional[Dict], Optional[str]]:
    """检查是否已有处理好的数据"""
    quotes_file = os.path.join(output_dir, f"{idol_name}_quotes.json")
    analysis_file = os.path.join(output_dir, f"{idol_name}_analysis.json")
    persona_file = os.path.join(output_dir, f"{idol_name}_persona.md")
    
    if not os.path.exists(quotes_file):
        return False, None, None, None
    if not os.path.exists(analysis_file):
        return False, None, None, None
    if not os.path.exists(persona_file):
        return False, None, None, None
    
    try:
        with open(quotes_file, 'r', encoding='utf-8') as f:
            quotes = json.load(f)
        with open(analysis_file, 'r', encoding='utf-8') as f:
            analysis = json.load(f)
        with open(persona_file, 'r', encoding='utf-8') as f:
            persona_doc = f.read()
        
        print(f"\n[缓存命中] 发现已处理的{idol_name}数据，跳过构建流程")
        return True, quotes, analysis, persona_doc
    except Exception as e:
        print(f"[缓存检查] 读取缓存文件时出错: {e}")
        return False, None, None, None


def find_idol_files(data_dirs: List[str], idol_name: str) -> List[str]:
    """扫描目录，找出文件名中包含指定偶像名的 SRT 文件"""
    srt_files = []
    
    for data_dir in data_dirs:
        if not os.path.exists(data_dir):
            continue
        
        pattern = os.path.join(data_dir, "**", "*.srt")
        files = glob.glob(pattern, recursive=True)
        
        for f in files:
            basename = os.path.basename(f)
            if idol_name in basename:
                srt_files.append(f)
                print(f"[找到] {basename}")
    
    return srt_files


def simple_chatbot(quotes: List[Dict], idol_config: Dict):
    """简化版对话系统"""
    import random
    
    idol_name = idol_config["idol_name"]
    fan_name = idol_config["fan_name"]
    symbol = idol_config["symbol"]
    
    print(f"\n{'='*60}")
    print(f"      {symbol} {idol_name} AI 人格系统 {symbol}")
    print(f"{'='*60}")
    print(f"\n已加载 {len(quotes)} 条{idol_name}语录")
    print(f"\n{idol_name}: {fan_name}们好呀～我是{idol_name}！")
    print(f"         今天也要开开心心的哦～")
    print("\n[提示] 输入 'exit' 或 '拜拜' 结束对话\n")
    
    while True:
        user_input = input("你: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in ['exit', 'quit', 'bye', '拜拜', '再见', '晚安']:
            print(f"\n{idol_name}: 拜拜～{fan_name}们要记得想我哦！")
            print(f"\n{'='*60}")
            print(f"感谢和{idol_name}聊天～要记得想我哦！{symbol}")
            print(f"{'='*60}\n")
            break
        
        # 随机选择一条语录作为回复
        if quotes:
            quote = random.choice(quotes)
            response = quote['text']
            print(f"\n{idol_name}: {response}\n")
        else:
            print(f"\n{idol_name}: 嗯嗯！\n")


def main():
    """主函数"""
    
    # 角色选择
    available_idols = ["嘉然", "贝拉", "乃琳"]
    
    print("=" * 70)
    print("       A-SOUL 多角色人格构建与对话系统")
    print("=" * 70)
    print("\n可用角色:")
    for i, idol in enumerate(available_idols, 1):
        config = IDOL_CONFIGS[idol]
        print(f"  {i}. {idol} {config['symbol']} ({config['fan_name']})")
    
    # 选择角色
    choice = input("\n请选择角色 (1-3, 默认: 1-嘉然): ").strip()
    
    if choice == "2":
        selected_idol = "贝拉"
    elif choice == "3":
        selected_idol = "乃琳"
    else:
        selected_idol = "嘉然"
    
    idol_config = IDOL_CONFIGS[selected_idol]
    print(f"\n[已选择] {selected_idol} {idol_config['symbol']}")
    
    # 获取配置
    output_dir = "./output"
    data_dirs = [
        "../ASOUL-REC-直播/SRT语音转字幕文件",
        "../AOSUL-REC-突击直播"
    ]
    
    # 检查缓存
    has_cache, quotes, analysis, persona_doc = check_existing_data(output_dir, selected_idol)
    
    if has_cache:
        print(f"\n[加载完成] {selected_idol}语录: {len(quotes)} 条")
        simple_chatbot(quotes, idol_config)
    else:
        # 需要构建
        print(f"\n[构建模式] 未找到缓存，开始构建{selected_idol}的数据...")
        
        # 扫描文件
        print(f"\n[步骤 1/3] 扫描{selected_idol}的字幕文件...")
        idol_files = find_idol_files(data_dirs, selected_idol)
        print(f"[完成] 找到 {len(idol_files)} 个文件")
        
        if not idol_files:
            print(f"\n[错误] 没有找到包含'{selected_idol}'的 SRT 文件！")
            return
        
        # 解析
        print(f"\n[步骤 2/3] 解析字幕内容...")
        all_entries = []
        for filepath in idol_files:
            entries = SRTParser.parse_file(filepath)
            all_entries.extend(entries)
        print(f"[完成] 共解析 {len(all_entries)} 条字幕")
        
        # 筛选
        print(f"\n[步骤 3/3] 筛选{selected_idol}的台词...")
        quotes = filter_idol_quotes(all_entries, idol_config)
        
        if len(quotes) < 10:
            print(f"\n[警告] 筛选出的台词数量较少")
        
        # 保存
        os.makedirs(output_dir, exist_ok=True)
        
        with open(os.path.join(output_dir, f"{selected_idol}_quotes.json"), 'w', encoding='utf-8') as f:
            json.dump(quotes, f, ensure_ascii=False, indent=2)
        
        print(f"\n[保存] 数据已保存到 {output_dir}/")
        
        # 启动对话
        simple_chatbot(quotes, idol_config)


if __name__ == "__main__":
    main()
