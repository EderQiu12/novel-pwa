#!/usr/bin/env python3
"""合并 gatsby_sentences.json 到 novels.json（幂等，可重复跑）"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
NOVELS = os.path.join(BASE, 'novels.json')
GATSBY = os.path.join(BASE, 'gatsby_sentences.json')

print(f"工作目录: {BASE}")
print(f"读 novels.json: {os.path.exists(NOVELS)}")
print(f"读 gatsby_sentences.json: {os.path.exists(GATSBY)}")

if not os.path.exists(NOVELS):
    sys.exit(f"❌ 找不到 {NOVELS}")
if not os.path.exists(GATSBY):
    sys.exit(f"❌ 找不到 {GATSBY}")

with open(NOVELS, encoding='utf-8') as f:
    novels = json.load(f)
with open(GATSBY, encoding='utf-8') as f:
    sents = json.load(f)

print(f"原 novels: {len(novels)} 本")
print(f"gatsby_sentences: {len(sents)} 句")

gatsby = {
    "id": "the-great-gatsby",
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "cover": "📙",
    "sentences": sents
}

out, found = [], False
for n in novels:
    if n.get('id') == 'the-great-gatsby':
        out.append(gatsby); found = True
    else:
        out.append(n)
if not found:
    out.append(gatsby)

with open(NOVELS, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"✅ OK: {len(out)} 本, Gatsby {len(sents)} 句")
