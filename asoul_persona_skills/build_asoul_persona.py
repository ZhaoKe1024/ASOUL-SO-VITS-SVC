#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
乃琳人格构建脚本
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from build_asoul_persona_v2 import (
    IDOL_CONFIGS, SRTParser, find_idol_files,
    filter_idol_quotes, check_existing_data
)
import json
from typing import List, Dict
import re
from collections import Counter
from datetime import datetime

def analyze_language_features(quotes: List[Dict]) -> Dict:
    """分析语言特征"""
    texts = [q['text'] for q in quotes]
    
    if not texts:
        return {}
    
    tone_particles = ["吧", "呢", "嘛", "啊", "哦", "呀", "噢", "嗯", "哈", "诶", "哎", "哟", "啦", "噜", "捏", "涅"]
    en_word_re = re.compile(r"[a-zA-Z]+(?:'[a-zA-Z]+)?")
    cjk_re = re.compile(r"[\u4e00-\u9fff]")
    
    particle_counter = Counter()
    for text in texts:
        for char in text:
            if char in tone_particles:
                particle_counter[char] += 1
    
    lengths = [len(t.replace(" ", "")) for t in texts]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    
    sent_counts = {"statement": 0, "question": 0, "exclamation": 0}
    for text in texts:
        stripped = text.rstrip()
        if stripped.endswith("?") or stripped.endswith("？"):
            sent_counts["question"] += 1
        elif stripped.endswith("!") or stripped.endswith("！"):
            sent_counts["exclamation"] += 1
        else:
            sent_counts["statement"] += 1
    
    total = len(texts)
    sent_types = {k: v / total for k, v in sent_counts.items()}
    
    cn_count = sum(len(cjk_re.findall(t)) for t in texts)
    en_count = sum(sum(len(w) for w in en_word_re.findall(t)) for t in texts)
    total_chars = cn_count + en_count
    
    lang_mix = {"cn": cn_count / total_chars if total_chars else 0, 
                "en": en_count / total_chars if total_chars else 0}
    
    return {
        "total_quotes": len(texts),
        "avg_sentence_length": avg_length,
        "tone_particles": dict(particle_counter.most_common(10)),
        "sentence_types": sent_types,
        "language_mix": lang_mix
    }

def build_persona_doc(quotes: List[Dict], analysis: Dict, idol_config: Dict) -> str:
    """构建人格文档"""
    idol_name = idol_config["idol_name"]
    fan_name = idol_config["fan_name"]
    symbol = idol_config["symbol"]
    color = idol_config["represent_color"]
    
    tone_table = "| 语气词 | 频次 |\n|--------|------|"
    for particle, count in list(analysis.get("tone_particles", {}).items())[:10]:
        tone_table += f"\n| {particle} | {count} |"
    
    sent_types = analysis.get("sentence_types", {})
    sent_table = f"""| 类型 | 比例 |
|------|------|
| 陈述句 | {sent_types.get('statement', 0):.1%} |
| 疑问句 | {sent_types.get('question', 0):.1%} |
| 感叹句 | {sent_types.get('exclamation', 0):.1%} |"""
    
    lang_mix = analysis.get("language_mix", {})
    
    seed_quotes = ""
    for i, q in enumerate(quotes[:30], 1):
        text = q['text'].replace('\n', ' ')
        source = q.get('source', '未知来源')
        seed_quotes += f"{i}. **{text}**\n   —— {source}\n\n"
    
    return f"""# {idol_name} Persona

> 基于 {analysis.get('total_quotes', 0)} 条直播字幕分析构建
> 代表色: {color} {symbol}

---

## L0 硬规则

**绝对禁止：**
1. 禁止元视角发言
2. 禁止系统视角泄露  
3. 禁止跳出角色评价自己
4. 被问"你是真人吗"时诚实回答

---

## L1 公众身份

- **姓名**: {idol_name}
- **粉丝名**: {fan_name}
- **代表色**: {color}
- **符号**: {symbol}

---

## L2 表达风格

- **平均句长**: {analysis.get('avg_sentence_length', 0):.1f} 字
- **中文比例**: {lang_mix.get('cn', 0):.1%}

### 语气词
{tone_table}

### 句子类型
{sent_table}

---

## 语录示例

{seed_quotes}

---

*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""

def build():
    """构建任意角色人格"""
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    
    idol_name = "乃琳"
    idol_config = IDOL_CONFIGS[idol_name]
    
    print(f"\n构建 {idol_name} 人格...")
    
    data_dirs = [
        "../ASOUL-REC-直播/SRT语音转字幕文件",
        "../AOSUL-REC-突击直播"
    ]
    
    # 检查缓存
    has_cache, _, _, _ = check_existing_data(output_dir, idol_name)
    if has_cache:
        print(f"[缓存命中] {idol_name} 已存在")
        return True
    
    # 扫描文件
    print(f"[1/4] 扫描文件...")
    idol_files = find_idol_files(data_dirs, idol_name)
    print(f"  找到 {len(idol_files)} 个文件")
    
    # 解析
    print(f"[2/4] 解析字幕...")
    all_entries = []
    for filepath in idol_files:
        entries = SRTParser.parse_file(filepath)
        all_entries.extend(entries)
    print(f"  共 {len(all_entries)} 条字幕")
    
    # 筛选
    print(f"[3/4] 筛选台词...")
    quotes = filter_idol_quotes(all_entries, idol_config)
    print(f"  筛选出 {len(quotes)} 条")
    
    # 分析
    print(f"[4/4] 分析特征...")
    analysis = analyze_language_features(quotes)
    print(f"  平均句长: {analysis.get('avg_sentence_length', 0):.1f}")
    
    # 构建人格
    persona_doc = build_persona_doc(quotes, analysis, idol_config)
    
    # 保存
    with open(os.path.join(output_dir, f"{idol_name}_quotes.json"), 'w', encoding='utf-8') as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)
    print(f"[保存] {idol_name}_quotes.json")
    
    with open(os.path.join(output_dir, f"{idol_name}_analysis.json"), 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"[保存] {idol_name}_analysis.json")
    
    with open(os.path.join(output_dir, f"{idol_name}_persona.md"), 'w', encoding='utf-8') as f:
        f.write(persona_doc)
    print(f"[保存] {idol_name}_persona.md")
    
    print(f"[成功] {idol_name} 构建完成！")
    return True

if __name__ == "__main__":
    build()
