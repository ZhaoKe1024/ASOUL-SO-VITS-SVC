#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量构建 A-SOUL 偶像人格文件
直接构建贝拉和乃琳的人格，不启动对话
"""

import os
import re
import json
import glob
import sys
from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 从 build_asoul_persona_v2.py 导入配置
from build_asoul_persona_v2 import (
    IDOL_CONFIGS, SRTParser, is_likely_idol, 
    filter_idol_quotes, find_idol_files
)


def analyze_language_features(quotes: List[Dict]) -> Dict:
    """分析语言特征"""
    texts = [q['text'] for q in quotes]
    
    if not texts:
        return {}
    
    # 语气词列表
    tone_particles = ["吧", "呢", "嘛", "啊", "哦", "呀", "噢", "嗯", "哈", "诶", "哎", "哟", "啦", "噜", "捏", "涅"]
    en_word_re = re.compile(r"[a-zA-Z]+(?:'[a-zA-Z]+)?")
    cjk_re = re.compile(r"[\u4e00-\u9fff]")
    
    # 语气词统计
    particle_counter = Counter()
    for text in texts:
        for char in text:
            if char in tone_particles:
                particle_counter[char] += 1
    
    # 句长统计
    lengths = [len(t.replace(" ", "")) for t in texts]
    avg_length = sum(lengths) / len(lengths) if lengths else 0
    
    # 句子类型
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
    
    # 语言混合比
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
    
    # 准备语气词表格
    tone_table = "| 语气词 | 频次 |\n|--------|------|"
    for particle, count in list(analysis.get("tone_particles", {}).items())[:10]:
        tone_table += f"\n| {particle} | {count} |"
    
    # 句子类型表格
    sent_types = analysis.get("sentence_types", {})
    sent_table = f"""| 类型 | 比例 |
|------|------|
| 陈述句 | {sent_types.get('statement', 0):.1%} |
| 疑问句 | {sent_types.get('question', 0):.1%} |
| 感叹句 | {sent_types.get('exclamation', 0):.1%} |"""
    
    # 语言混合
    lang_mix = analysis.get("language_mix", {})
    
    # 语录示例
    seed_quotes = ""
    for i, q in enumerate(quotes[:30], 1):
        text = q['text'].replace('\n', ' ')
        source = q.get('source', '未知来源')
        seed_quotes += f"{i}. **{text}**\n   —— {source}\n\n"
    
    persona = f"""# {idol_name} {idol_config.get('idol_english_name', '')} Persona

> 基于 {analysis.get('total_quotes', 0)} 条直播字幕分析构建
> 分析时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
> 代表色: {color} {symbol}

---

## L0 硬规则 (Inviolable)

**绝对禁止：**

1. **禁止元视角发言** — 不能说"我的直播""视频里的我""我在采访中说过"
2. **禁止系统视角泄露** — 不能说"根据我的人设""按照语料""我被设定为"
3. **禁止跳出角色评价自己** — 不能说"我觉得我说话很像我""这个语气确实很像我"
4. **被直接问"你是真人吗"时诚实回答**，其余时候保持角色

**违反任何一条 = 最严重的 bug**

---

## L1 公众身份 (Public Identity)

**基本信息：**
- **姓名**：{idol_name} ({idol_config.get('idol_english_name', '')})
- **身份**：虚拟偶像女团 A-SOUL 成员
- **代表色**：{color}
- **粉丝名**：{fan_name}
- **代表符号**：{symbol}

---

## L2 表达风格 (Expression Style)

**基于 {analysis.get('total_quotes', 0)} 条语录统计分析：**

### 基础指标
- **平均句长**: {analysis.get('avg_sentence_length', 0):.1f} 字
- **语言混合比**: 中文 {lang_mix.get('cn', 0):.1%}, 英文 {lang_mix.get('en', 0):.1%}

### 语气词使用（Top 10）
{tone_table}

### 句子类型分布
{sent_table}

### 风格特征
1. 语气词丰富，表达自然亲切
2. 句子长度适中，符合直播口语特征
3. 情感表达直接，善用感叹句
4. 与{fan_name}互动性强

---

## L2.5 情绪表演 (Emotional Performance)

**情绪表达模式：**

- 开心时：语气上扬，用"嘿嘿/哈哈"
- 撒娇时：拉长音"呢～""啦～"
- 惊讶时："啊啊啊"，连续感叹
- 认真时：语速平稳，用词正式

---

## L3 话题反应 (Topic Response)

**擅长话题：**
- 与{fan_name}互动聊天
- 日常生活分享
- 游戏/直播内容
- 歌舞相关内容

**回避话题：**
- 成员间敏感比较
- 过于负面的内容
- 三次元私人生活

---

## L4 人际边界 (Interpersonal Boundaries)

- 对{fan_name}：亲昵称呼，关心体贴，像家人一样
- 对普通观众：礼貌热情，保持距离
- 对恶意评论：不直接回应，忽略或轻松带过
- 面对过度要求：委婉拒绝，保持边界

---

## L5 关系适配 (Relationship Adaptation)

**关系类型：**
- 女友粉：恋爱感、甜甜互动
- 妈粉：可爱女儿、撒娇求夸
- 唯粉：专注事业、舞台作品
- CP粉：分享日常、发糖互动

---

## 语录示例 (Seed Quotes)

{seed_quotes}

---

*生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
*数据来源: {analysis.get('total_quotes', 0)} 条直播字幕*
"""
    
    return persona


def build_idol_persona(idol_name: str, output_dir: str = "./output"):
    """构建单个偶像的人格"""
    
    print("\n" + "=" * 70)
    print(f"       构建 {idol_name} 的人格")
    print("=" * 70)
    
    if idol_name not in IDOL_CONFIGS:
        print(f"[错误] 未知角色: {idol_name}")
        return False
    
    idol_config = IDOL_CONFIGS[idol_name]
    
    data_dirs = [
        "../ASOUL-REC-直播/SRT语音转字幕文件",
        "../AOSUL-REC-突击直播"
    ]
    
    # 检查缓存
    quotes_file = os.path.join(output_dir, f"{idol_name}_quotes.json")
    analysis_file = os.path.join(output_dir, f"{idol_name}_analysis.json")
    persona_file = os.path.join(output_dir, f"{idol_name}_persona.md")
    
    if os.path.exists(quotes_file) and os.path.exists(analysis_file) and os.path.exists(persona_file):
        print(f"\n[缓存命中] {idol_name} 的人格文件已存在，跳过构建")
        print(f"  - {quotes_file}")
        print(f"  - {analysis_file}")
        print(f"  - {persona_file}")
        return True
    
    # 扫描文件
    print(f"\n[步骤 1/4] 扫描{idol_name}的字幕文件...")
    idol_files = find_idol_files(data_dirs, idol_name)
    print(f"[完成] 找到 {len(idol_files)} 个文件")
    
    if not idol_files:
        print(f"[错误] 未找到 {idol_name} 的字幕文件！")
        return False
    
    # 解析
    print(f"\n[步骤 2/4] 解析字幕内容...")
    all_entries = []
    for filepath in idol_files:
        entries = SRTParser.parse_file(filepath)
        all_entries.extend(entries)
    print(f"[完成] 共解析 {len(all_entries)} 条字幕")
    
    # 筛选
    print(f"\n[步骤 3/4] 筛选{idol_name}的台词...")
    quotes = filter_idol_quotes(all_entries, idol_config)
    
    if len(quotes) < 10:
        print(f"[警告] 筛选出的台词数量较少: {len(quotes)} 条")
    
    # 分析
    print(f"\n[步骤 4/4] 分析语言特征...")
    analysis = analyze_language_features(quotes)
    print(f"[完成] 语言分析:")
    print(f"  - 语录数: {analysis.get('total_quotes', 0)}")
    print(f"  - 平均句长: {analysis.get('avg_sentence_length', 0):.1f} 字")
    print(f"  - 语气词种类: {len(analysis.get('tone_particles', {}))}")
    
    # 构建人格文档
    persona_doc = build_persona_doc(quotes, analysis, idol_config)
    
    # 保存
    os.makedirs(output_dir, exist_ok=True)
    
    with open(quotes_file, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)
    print(f"\n[保存] {quotes_file}")
    
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    print(f"[保存] {analysis_file}")
    
    with open(persona_file, 'w', encoding='utf-8') as f:
        f.write(persona_doc)
    print(f"[保存] {persona_file}")
    
    print(f"\n[成功] {idol_name} 的人格构建完成！")
    return True


def main():
    """主函数 - 批量构建"""
    
    print("=" * 70)
    print("       A-SOUL 偶像人格批量构建工具")
    print("=" * 70)
    
    output_dir = "./output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 构建贝拉和乃琳
    idols_to_build = ["嘉然", "贝拉", "乃琳"]
    
    results = {}
    for idol_name in idols_to_build:
        success = build_idol_persona(idol_name, output_dir)
        results[idol_name] = success
    
    # 汇总
    print("\n" + "=" * 70)
    print("       构建结果汇总")
    print("=" * 70)
    
    for idol_name, success in results.items():
        status = "✓ 成功" if success else "✗ 失败"
        print(f"  {idol_name}: {status}")
    
    print("\n输出目录:", os.path.abspath(output_dir))
    print("\n文件列表:")
    for idol_name in idols_to_build:
        for ext in ["quotes.json", "analysis.json", "persona.md"]:
            filename = f"{idol_name}_{ext}"
            filepath = os.path.join(output_dir, filename)
            if os.path.exists(filepath):
                size = os.path.getsize(filepath)
                print(f"  - {filename} ({size:,} bytes)")


if __name__ == "__main__":
    main()
