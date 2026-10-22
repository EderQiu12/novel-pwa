#!/usr/bin/env python3
"""The Great Gatsby: 行内切句 + 句级 DP + 位置先验 -> [{en, zh}]"""
import re, json, sys

SRC = 'gatsby.txt'
OUT = 'gatsby_sentences.json'

with open(SRC, encoding='utf-8') as f:
    text = f.read().lstrip('\ufeff')

text = re.sub(r'(?m)^Chapter\s+\d+\s*$', '', text)

def classify(line):
    zh = sum(1 for c in line if '\u4e00' <= c <= '\u9fff')
    en = sum(1 for c in line if c.isascii() and c.isalpha())
    return 'zh' if zh > en else 'en'

def is_punct_only(s):
    return len(s) <= 2 and all(not c.isalnum() for c in s)

# ---------- 按行收集，合并孤立标点行 ----------
en_lines, zh_lines = [], []
for raw in text.split('\n'):
    line = raw.strip()
    if not line:
        continue
    if classify(line) == 'zh':
        if zh_lines and is_punct_only(line):
            zh_lines[-1] += line
        else:
            zh_lines.append(line)
    else:
        if en_lines and is_punct_only(line):
            en_lines[-1] += ' ' + line
        else:
            en_lines.append(line)

# ---------- 行内切句 ----------
ABBR = ['Mr.', 'Mrs.', 'Ms.', 'Dr.', 'St.', 'Jr.', 'Sr.', 'vs.', 'etc.',
        'e.g.', 'i.e.', 'a.m.', 'p.m.', 'U.S.', 'D.C.', 'H?tel']

def split_en(t):
    holders = {}
    for i, a in enumerate(ABBR):
        h = f'\x00{i}\x00'; holders[h] = a; t = t.replace(a, h)
    out = []
    for s in re.split(r'(?<=[.!?])\s+', t):
        for h, a in holders.items(): s = s.replace(h, a)
        s = s.strip()
        if s: out.append(s)
    return out

def split_zh(t):
    return [s.strip() for s in re.split(r'(?<=[。！？])', t) if s.strip()]

en_sents, zh_sents = [], []
for line in en_lines:
    en_sents.extend(split_en(line))
for line in zh_lines:
    zh_sents.extend(split_zh(line))

n, m = len(en_sents), len(zh_sents)
print(f"EN sents={n}  ZH sents={m}", file=sys.stderr)

# ---------- 成本函数 ----------
NAME_MAP = {
    'gatsby':'盖茨比','daisy':'黛西','tom':'汤姆','jordan':'乔丹','nick':'尼克',
    'wilson':'威尔逊','myrtle':'茉特尔','buchanan':'布坎南','carraway':'卡罗威',
    'wolfshiem':'沃尔夫山姆','cody':'科迪','klipspringer':'克利普斯普林格',
    'mckee':'麦基','catherine':'凯瑟琳','east egg':'东卵','west egg':'西卵',
}

def sent_cost(en, zh):
    we = max(1, len(en.split()))
    wz = max(1, len(zh))
    ratio = wz / we
    len_pen = abs(ratio - 1.8) / 1.8

    en_names = frozenset(v for k, v in NAME_MAP.items() if k in en.lower())
    zh_names = frozenset(v for v in NAME_MAP.values() if v in zh)
    if en_names == zh_names:
        name_pen = 0.0
    elif en_names & zh_names:
        name_pen = 0.3
    elif en_names or zh_names:
        name_pen = 0.6
    else:
        name_pen = 0.0

    ae = set(re.findall(r'\d+', en))
    az = set(re.findall(r'\d+', zh))
    num_pen = 0.0 if ae == az else 0.4

    p = 0.0
    if ('?' in en) != ('？' in zh): p += 0.3
    if ('!' in en) != ('！' in zh): p += 0.3

    return len_pen * 2 + name_pen + num_pen + p

POS_K = 3.0
SKIP = 1.5

def pos_pen(i, j):
    return POS_K * abs(j / m - i / n)

# ---------- 句级 DP ----------
INF = float('inf')
ops = [bytearray(m + 1) for _ in range(n + 1)]

dp_im1 = [INF] * (m + 1)
dp_im1[0] = 0.0
for j in range(1, m + 1):
    dp_im1[j] = dp_im1[j - 1] + SKIP
    ops[0][j] = 5

dp_im2 = None
for i in range(1, n + 1):
    cur = [INF] * (m + 1)
    cur[0] = dp_im1[0] + SKIP
    ops[i][0] = 4
    en_i = en_sents[i - 1]

    for j in range(1, m + 1):
        zh_j = zh_sents[j - 1]
        pp = pos_pen(i, j)

        best = dp_im1[j - 1] + sent_cost(en_i, zh_j) + pp
        d = 1

        if j >= 2:
            c = dp_im1[j - 2] + sent_cost(en_i, zh_sents[j - 2] + zh_sents[j - 1]) + pp + 0.5
            if c < best: best, d = c, 2

        if i >= 2 and dp_im2 is not None:
            c = dp_im2[j - 1] + sent_cost(en_sents[i - 2] + ' ' + en_i, zh_j) + pp + 0.5
            if c < best: best, d = c, 3

        c = dp_im1[j] + SKIP
        if c < best: best, d = c, 4

        c = cur[j - 1] + SKIP
        if c < best: best, d = c, 5

        cur[j] = best
        ops[i][j] = d

    dp_im2 = dp_im1
    dp_im1 = cur

# ---------- 回溯 ----------
pairs = []
i, j = n, m
while i > 0 or j > 0:
    d = ops[i][j]
    if d == 1:
        pairs.append(([en_sents[i - 1]], [zh_sents[j - 1]])); i -= 1; j -= 1
    elif d == 2:
        pairs.append(([en_sents[i - 1]], [zh_sents[j - 2] + zh_sents[j - 1]])); i -= 1; j -= 2
    elif d == 3:
        pairs.append(([en_sents[i - 2], en_sents[i - 1]], [zh_sents[j - 1]])); i -= 2; j -= 1
    elif d == 4:
        pairs.append(([en_sents[i - 1]], [])); i -= 1
    elif d == 5:
        pairs.append(([], [zh_sents[j - 1]])); j -= 1
    else:
        raise RuntimeError(f"bad op at ({i},{j})")
pairs.reverse()

# ---------- 输出 ----------
sentences = []
for en_list, zh_list in pairs:
    zh = ''.join(zh_list).strip()
    if not en_list:
        if sentences and zh:
            sentences[-1]['zh'] = (sentences[-1]['zh'] + zh).strip()
        continue
    sentences.append({'en': en_list[0], 'zh': zh})
    for extra in en_list[1:]:
        sentences.append({'en': extra, 'zh': ''})

empty = sum(1 for s in sentences if not s['zh'])
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(sentences, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(sentences)} sentences  (zh 为空: {empty}, {empty/len(sentences)*100:.1f}%)",
      file=sys.stderr)
