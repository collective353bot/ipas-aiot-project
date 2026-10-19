#!/usr/bin/env python3
"""Build index.html (interactive, offline single file) and print.html (for PDF)."""
import json, re, sys, html, pathlib
import markdown
ROOT = pathlib.Path(__file__).parent
SRC = ROOT / 'src'

DAYS = json.loads((SRC / 'days.json').read_text(encoding='utf-8'))
REF_RE = re.compile(r'\{\{([^}｜|]+)(?:[｜|]([^}]+))?\}\}')

def ref_badges(m):
    ref = m.group(1).strip(); pg = (m.group(2) or '').strip()
    out = f'<span class="ref">{html.escape(ref)}</span>'
    if pg:
        cls = 'supp' if pg.startswith('補充') else 'pg'
        out += f'<span class="{cls}">{html.escape(pg)}</span>'
    return out

def md(text):
    stash = []
    def rep(m):
        stash.append(ref_badges(m)); return f'ZZREF{len(stash)-1}ZZ'
    text = REF_RE.sub(rep, text)
    h = markdown.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists'])
    return re.sub(r'ZZREF(\d+)ZZ', lambda m: stash[int(m.group(1))], h)

def parse_questions(path, day):
    qs = []
    if not path.exists():
        return qs
    blocks = re.split(r'\n\s*\n(?=@)', path.read_text(encoding='utf-8').strip())
    for i, b in enumerate(blocks, 1):
        lines = [l.rstrip() for l in b.strip().split('\n') if l.strip()]
        q = {'id': f'd{day}q{i}', 'n': i, 'opts': [], 'exp': '', 'origin': '原創練習題（依官方評鑑範圍撰寫）', 'stem': ''}
        head = lines[0][1:].strip()
        parts = [p.strip() for p in re.split(r'[｜|]', head)]
        q['ref'] = parts[0]; q['src'] = parts[1] if len(parts) > 1 else ''
        stem = []
        for l in lines[1:]:
            m = re.match(r'^([ABCD])\. (.*)$', l)
            if m and len(q['opts']) == 'ABCD'.index(m.group(1)):
                q['opts'].append(m.group(2)); continue
            if l.startswith('='):
                q['ans'] = 'ABCD'.index(l[1:].strip()[0]); continue
            if l.startswith('>'):
                q['exp'] += (('\n' if q['exp'] else '') + l[1:].strip()); continue
            if l.startswith('%'):
                q['origin'] = l[1:].strip(); continue
            if not q['opts']:
                stem.append(l)
            else:
                raise SystemExit(f'Unparsed line in {path} q{i}: {l}')
        q['stem'] = '\n'.join(stem)
        assert len(q['opts']) == 4, (path, i, q)
        assert 'ans' in q, (path, i)
        assert q['exp'], (path, i, 'no explanation')
        assert re.match(r'^考科[一二] \d[\.\-]\d$', q['ref']), (path, i, q['ref'])
        qs.append(q)
    return qs

def inline(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    return s.replace('\n', '<br>')

problems = []
total = 0
for d in DAYS['days']:
    n = d['id']
    lec = (SRC / f'd{n:02d}.md')
    text = lec.read_text(encoding='utf-8') if lec.exists() else '（尚未撰寫）'
    # every h2/h3 must carry a ref tag
    for line in text.split('\n'):
        if re.match(r'^##\s', line) and '{{' not in line:
            problems.append(f'D{n} heading without ref: {line}')
    d['lectureChars'] = len(re.sub(r'\s', '', text))
    d['lecture'] = md(text)
    mp3 = ROOT.parent / 'audio' / f'd{n:02d}.mp3'
    if mp3.exists():
        import subprocess
        dur = float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(mp3)],capture_output=True,text=True).stdout or 0)
        d['audio'] = {'src': f'audio/d{n:02d}.mp3', 'dur': round(dur)}
    else:
        problems.append(f'D{n} no audio')
    d['questions'] = parse_questions(SRC / f'q{n:02d}.txt', n)
    for q in d['questions']:
        q['stemH'] = inline(q['stem']); q['optsH'] = [inline(o) for o in q['opts']]; q['expH'] = inline(q['exp'])
    total += len(d['questions'])

cheat = md((SRC / 'cheat.md').read_text(encoding='utf-8')) if (SRC / 'cheat.md').exists() else ''
intro = md((SRC / 'intro.md').read_text(encoding='utf-8')) if (SRC / 'intro.md').exists() else ''
DAYS['cheat'] = cheat; DAYS['intro'] = intro

# official mapping: which days cover which official item (lecture refs + question refs)
cover = {}
for d in DAYS['days']:
    refs = set(re.findall(r'class="ref">([^<]+)<', d['lecture'])) | {q['ref'] for q in d['questions']}
    for r in refs:
        cover.setdefault(r.strip(), set()).add(d['id'])
qcount = {}
for d in DAYS['days']:
    for q in d['questions']:
        qcount[q['ref']] = qcount.get(q['ref'], 0) + 1
for item in DAYS['official']:
    item['days'] = sorted(cover.get(item['code'], []))
    item['qn'] = qcount.get(item['code'], 0)
    if not item['days']:
        problems.append('NOT COVERED: ' + item['code'])
unknown = set(cover) - {i['code'] for i in DAYS['official']}
if unknown:
    problems.append('Unknown refs: ' + ', '.join(sorted(unknown)))

tpl = (ROOT / 'template.html').read_text(encoding='utf-8')
data = json.dumps(DAYS, ensure_ascii=False).replace('</', '<\\/')
(ROOT / 'index.html').write_text(tpl.replace('/*__DATA__*/null', data), encoding='utf-8')
ptpl = (ROOT / 'print_template.html').read_text(encoding='utf-8')
(ROOT / 'print.html').write_text(ptpl.replace('/*__DATA__*/null', data), encoding='utf-8')
print('days:', [(d['id'], len(d['questions']), d['lectureChars']) for d in DAYS['days']])
print('total questions:', total)
for p in problems: print('PROBLEM:', p)
