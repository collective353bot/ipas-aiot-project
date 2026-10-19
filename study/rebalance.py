import re, sys, math
LET = re.compile(r'(?<![A-Za-z])[A-D](?![A-Za-z])')
for path in sys.argv[1:]:
    blocks = open(path, encoding='utf-8').read().strip().split('\n\n')
    qs = []
    for b in blocks:
        lines = b.split('\n')
        oi = [i for i,l in enumerate(lines) if re.match(r'^[A-D]\. ', l)]
        ai = [i for i,l in enumerate(lines) if l.startswith('= ')][0]
        exp = ' '.join(l for l in lines if l.startswith('>'))
        stem = ' '.join(lines[1:oi[0]])
        opts = ' '.join(lines[i] for i in oi)
        ok = not LET.search(exp) and not LET.search(stem) and '以上' not in opts
        qs.append([lines, oi, ai, ok])
    n = len(qs); cap = math.ceil(n/4)
    cnt = {c:0 for c in 'ABCD'}
    for q in qs: cnt[q[0][q[2]][2]] += 1
    swaps = 0
    for q in qs:
        lines, oi, ai, ok = q
        a = lines[ai][2]
        if not ok or cnt[a] <= cap: continue
        tgt = min('ABCD', key=lambda c: cnt[c])
        if cnt[tgt] >= cnt[a]-1: continue
        ia, it = oi['ABCD'.index(a)], oi['ABCD'.index(tgt)]
        ta, tt = lines[ia][3:], lines[it][3:]
        lines[ia] = f'{a}. {tt}'; lines[it] = f'{tgt}. {ta}'
        lines[ai] = f'= {tgt}'
        cnt[a] -= 1; cnt[tgt] += 1; swaps += 1
    open(path, 'w', encoding='utf-8').write('\n\n'.join('\n'.join(q[0]) for q in qs) + '\n')
    print(path, swaps, cnt)
