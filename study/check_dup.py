#!/usr/bin/env python3
"""Compare 隨堂小測 (:::check blocks in src/d*.md) against all question banks q01–q13.
Prints the closest bank question per checkpoint (char-bigram Jaccard + difflib ratio)."""
import re, glob, difflib, pathlib
SRC = pathlib.Path(__file__).parent / 'src'
norm = lambda s: re.sub(r'[\s，。、？！：；「」（）()`,.?:;/\-]', '', s)
big = lambda s: {norm(s)[i:i+2] for i in range(len(norm(s)) - 1)}
def split(b):
    L = [l for l in b.split('\n') if l.strip()]
    stem = ' '.join(l for l in L if not re.match(r'^([ABCD]\. |=|>|%|@)', l))
    opts = [l[3:] for l in L if re.match(r'^[ABCD]\. ', l)]
    a = [l for l in L if l.startswith('=')][0][1:].strip()[0]
    return stem, opts['ABCD'.index(a)]
bank = []
for f in sorted(SRC.glob('q*.txt')):
    for i, b in enumerate(re.split(r'\n\s*\n(?=@)', f.read_text(encoding='utf-8').strip()), 1):
        bank.append((f'{f.stem}#{i}',) + split(b))
worst = 0
for f in sorted(SRC.glob('d*.md')):
    for k, m in enumerate(re.finditer(r'^:::check[ \t]+(.+?)\n(.*?)\n:::', f.read_text(encoding='utf-8'), re.M | re.S), 1):
        stem, ans = split(m.group(2))
        best = max((max(len(big(stem) & big(s)) / max(1, len(big(stem) | big(s))),
                        len(big(stem + ans) & big(s + a)) / max(1, len(big(stem + ans) | big(s + a))),
                        difflib.SequenceMatcher(None, norm(stem), norm(s)).ratio()), i, s[:50]) for i, s, a in bank)
        worst = max(worst, best[0])
        print(f'{f.stem} 小測{k}: max={best[0]:.2f} vs {best[1]} {best[2]}')
print(f'bank={len(bank)} worst={worst:.2f}')
