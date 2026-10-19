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

CHECK_RE = re.compile(r'^:::check[ \t]+(.+?)\n(.*?)\n:::[ \t]*$', re.M | re.S)

def md(text, checks=None):
    if checks is not None:
        def crep(m):
            checks.append(parse_check(m.group(1).strip(), m.group(2)))
            return f'\n\nZZCHK{len(checks)-1}ZZ\n\n'
        text = CHECK_RE.sub(crep, text)
    stash = []
    def rep(m):
        stash.append(ref_badges(m)); return f'ZZREF{len(stash)-1}ZZ'
    text = REF_RE.sub(rep, text)
    h = markdown.markdown(text, extensions=['tables', 'fenced_code', 'sane_lists'])
    return re.sub(r'ZZREF(\d+)ZZ', lambda m: stash[int(m.group(1))], h)

def parse_check(ref, body):
    q = {'ref': ref, 'opts': [], 'exp': '', 'stem': ''}
    assert re.match(r'^考科[一二] \d[\.\-]\d$', ref), ref
    stem = []
    for l in [x.rstrip() for x in body.strip().split('\n') if x.strip()]:
        m = re.match(r'^([ABCD])\. (.*)$', l)
        if m and len(q['opts']) == 'ABCD'.index(m.group(1)):
            q['opts'].append(m.group(2)); continue
        if l.startswith('='): q['ans'] = 'ABCD'.index(l[1:].strip()[0]); continue
        if l.startswith('>'): q['exp'] += (('\n' if q['exp'] else '') + l[1:].strip()); continue
        assert not q['opts'], ('check: unparsed line after options', l)
        stem.append(l)
    q['stem'] = '\n'.join(stem)
    assert len(q['opts']) == 4 and 'ans' in q and q['exp'], q
    return q

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

# ---------- glossary ----------
GLOSS = json.loads((SRC / 'glossary.json').read_text(encoding='utf-8'))
KEYMAP = {}
for gi, g in enumerate(GLOSS):
    for k in [g['term']] + g['aliases']:
        KEYMAP.setdefault(k, []).append(gi)
def _kpat(k):
    p = re.escape(k)
    if re.match(r'[A-Za-z0-9]', k): p = r'(?<![A-Za-z0-9])' + p
    if re.search(r'[A-Za-z0-9]$', k): p = p + r'(?![A-Za-z0-9])'
    return p
GL_RE = re.compile('|'.join(_kpat(k) for k in sorted(KEYMAP, key=len, reverse=True)))
def gl_pick(key, ref):
    for gi in KEYMAP[key]:
        c = GLOSS[gi].get('ctx')
        if c and c['alias'] == key:
            if 'only' in c and ref not in c['only']: continue
            if 'not' in c and ref in c['not']: continue
        return gi
    return None
def gl_find(text, ref):
    out = set()
    for m in GL_RE.finditer(html.unescape(re.sub(r'<[^>]+>', ' ', text))):
        gi = gl_pick(m.group(0), ref)
        if gi is not None: out.add(gi)
    return out
SKIP_TAGS = {'a', 'code', 'pre', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'button', 'summary'}
def gl_wrap(h, ref, used):
    """Wrap first occurrence (per `used` set) of each glossary term in text nodes outside skipped tags."""
    parts = re.split(r'(<[^>]+>)', h); depth = 0; out = []
    for p in parts:
        if p.startswith('<'):
            m = re.match(r'<(/?)([a-zA-Z0-9]+)', p)
            if m and m.group(2).lower() in SKIP_TAGS and not p.endswith('/>'):
                depth += -1 if m.group(1) else 1
            out.append(p); continue
        if depth > 0 or not p.strip():
            out.append(p); continue
        def rep(m):
            gi = gl_pick(m.group(0), ref)
            if gi is None or gi in used: return m.group(0)
            used.add(gi)
            return f'<span class="gl" data-g="{gi}" tabindex="0" role="button">{m.group(0)}</span>'
        out.append(GL_RE.sub(rep, p))
    return ''.join(out)
def gl_lecture(h):
    """Process lecture HTML section by section (split at <h2>)."""
    secs = re.split(r'(?=<h2[ >])', h); out = []
    for sec in secs:
        m = re.search(r'class="ref">([^<]+)<', sec[:600]) if sec.startswith('<h2') else None
        ref = m.group(1).strip() if m else ''
        out.append(gl_wrap(sec, ref, set()))
    return ''.join(out), secs
def sec_refs(h):
    """yield (ref, html) per section"""
    for sec in re.split(r'(?=<h2[ >])', h):
        m = re.search(r'class="ref">([^<]+)<', sec[:600]) if sec.startswith('<h2') else None
        yield (m.group(1).strip() if m else ''), sec

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
    checks = []
    raw = md(text, checks)
    gused = set()
    for ref, sec in sec_refs(raw): gused |= gl_find(sec, ref)
    lec, _ = gl_lecture(raw)
    for ci, c in enumerate(checks):
        c['id'] = f'd{n}c{ci+1}'; c['n'] = ci + 1
        c['stemH'] = inline(c['stem']); c['optsH'] = [inline(o) for o in c['opts']]
        c['expH'] = gl_wrap(inline(c['exp']), c['ref'], set())
        gused |= gl_find(c['stem'] + ' ' + ' '.join(c['opts']) + ' ' + c['exp'], c['ref'])
        cardh = (f'<div class="cp" id="cp_{c["id"]}" data-ans="{c["ans"]}"><div class="cph">🧩 隨堂小測 {c["n"]}'
                 f'<span class="ref">{html.escape(c["ref"])}</span><span class="cpn">不計分・原創練習</span></div>'
                 f'<div class="stem">{c["stemH"]}</div>'
                 + ''.join(f'<button class="opt cpo" data-k="{k}">{"ABCD"[k]}. {o}</button>' for k, o in enumerate(c['optsH']))
                 + f'<div class="cpfb" hidden><b class="cpr"></b><div>{c["expH"]}</div></div></div>')
        lec = re.sub(rf'<p>ZZCHK{ci}ZZ</p>', lambda m: cardh, lec)
        assert f'ZZCHK{ci}ZZ' not in lec, ('checkpoint placeholder left', n, ci)
    d['checks'] = checks
    d['lecture'] = lec
    d['_gused'] = gused
    # v2 recordings (ElevenLabs, scripts_v2) take precedence; ?v= busts browser caches
    AUDIO_VER = 2
    mp3 = ROOT.parent / 'audio' / 'v2' / f'd{n:02d}.mp3'
    if not mp3.exists():
        mp3 = ROOT.parent / 'audio' / f'd{n:02d}.mp3'
    if mp3.exists():
        import subprocess
        dur = float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(mp3)],capture_output=True,text=True).stdout or 0)
        d['audio'] = {'src': f'audio/d{n:02d}.mp3?v={AUDIO_VER}', 'dur': round(dur)}
    else:
        problems.append(f'D{n} no audio')
    d['questions'] = parse_questions(SRC / f'q{n:02d}.txt', n)
    for q in d['questions']:
        q['stemH'] = inline(q['stem']); q['optsH'] = [inline(o) for o in q['opts']]; q['expH'] = gl_wrap(inline(q['exp']), q['ref'], set())
        d['_gused'] |= gl_find(q['stem'] + ' ' + ' '.join(q['opts']) + ' ' + q['exp'], q['ref'])
    total += len(d['questions'])

for g in GLOSS: g['days'] = []
for d in DAYS['days']:
    d['gloss'] = sorted(d.pop('_gused'), key=lambda i: GLOSS[i]['term'].lower())
    for gi in d['gloss']: GLOSS[gi]['days'].append(d['id'])
DAYS['glossary'] = GLOSS
cheat = gl_lecture(md((SRC / 'cheat.md').read_text(encoding='utf-8')))[0] if (SRC / 'cheat.md').exists() else ''
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
print('glossary terms:', len(GLOSS), 'unused:', [g['term'] for g in GLOSS if not g['days']])
print('checkpoints:', [(d['id'], len(d['checks'])) for d in DAYS['days']])
for p in problems: print('PROBLEM:', p)
