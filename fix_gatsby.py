#!/usr/bin/env python3
"""最终后处理：定点修正已知错位 + 清理开头引号残留"""
import json

with open('gatsby_sentences.json', encoding='utf-8') as f:
    d = json.load(f)

# ---- 1. 开头题词区（幂等）----
FIXED = {
    3: '我一定得把你要！',
    4: '托马斯•帕克•丹维里埃',
    5: '我年纪还轻，阅历不深的时候，我父亲教导过我一句话，我至今还念念不忘。',
}
ok = (len(d) > 5
      and d[3]['en'].startswith('I must have you')
      and d[4]['en'].startswith('--THOMAS'))
if ok and d[3]['zh'] != FIXED[3]:
    for i, zh in FIXED.items():
        d[i]['zh'] = zh
    print("✓ 修复开头题词区（#3~#5）")
else:
    print("✓ 开头题词区已正确，跳过")

# ---- 2. 定点修正已知错位（按 EN 内容匹配，幂等）----
KNOWN_FIXES = [
    ("He had to polish it from morning till night",
     "他从早擦到晚，后来他的鼻子就受不了啦……"),
    ('"Things went from bad to worse," suggested Miss Baker',
     '"后来情况越来越坏，"贝克小姐提了一句。'),
    ('"Yes. Things went from bad to worse until finally',
     '"是的。情况越来越坏，最后他只得辞掉不干。"'),
    ('"No, you\'re not."',
     '"不对，你不小心。"'),
    ('"Well, other people are," she said lightly',
     '"不要紧，反正别人很小心。"她轻巧地说。'),
]
n_fixed = 0
for s in d:
    en = s['en'].strip()
    for key, correct_zh in KNOWN_FIXES:
        if en.startswith(key):
            if s['zh'] != correct_zh:
                s['zh'] = correct_zh
                n_fixed += 1
                print(f"  ✓ {key[:45]}...")
            break
print(f"定点修正: {n_fixed} 处")

# ---- 3. 开头连续引号剥离（任意 4 种引号组合，保留 1 个）----
QUOTES = set('""""')
def clean_leading_quotes(zh):
    i = 0
    while i < len(zh) and zh[i] in QUOTES:
        i += 1
    if i > 1:
        return zh[i-1:]
    return zh

n_start = 0
for s in d:
    new_zh = clean_leading_quotes(s['zh'])
    if new_zh != s['zh']:
        s['zh'] = new_zh
        n_start += 1
print(f"剥离开头连续引号: {n_start} 处")

with open('gatsby_sentences.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)

empty = sum(1 for s in d if not s['zh'])
print(f"最终: {len(d)} 句, zh 为空 {empty} ({empty/len(d)*100:.1f}%)")
