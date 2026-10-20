#!/usr/bin/env python3
"""Build a HyperFrames composition (index.html) for one course day.

Usage: python build.py d02   (expects d02/d02.segments.json, d02/slides.html, ../audio/v2/d02.mp3)
Inputs : <day>/<day>.segments.json  (from align.py), <day>/slides.html (slide spec, see README)
Output : <day>/index.html + <day>/assets/{narration.mp3,fonts,gsap.min.js} (copied, git-ignored)
"""
import json, re, sys, os, shutil, html, subprocess

day = sys.argv[1].strip('/')
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), day)
HERE = os.path.dirname(os.path.abspath(__file__))
dnum = int(re.sub(r'\D', '', day))
segs = json.load(open(f'{D}/{day}.segments.json'))
spec = open(f'{D}/slides.html', encoding='utf-8').read()
spec = re.sub(r'<!--.*?-->', '', spec, flags=re.S)
audio_src = os.path.join(HERE, '..', 'audio', 'v2', f'{day}.mp3')
dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio_src]))
os.makedirs(f'{D}/assets/fonts', exist_ok=True)
shutil.copy(audio_src, f'{D}/assets/narration.mp3')
shutil.copy(f'{HERE}/shared/fonts/NotoSansTC.ttf', f'{D}/assets/fonts/NotoSansTC.ttf')
shutil.copy(f'{HERE}/shared/gsap.min.js', f'{D}/assets/gsap.min.js')

squash = lambda s: re.sub(r'\s+', '', s)
segtxt = [squash(s['text']) for s in segs]

def find(phrase, frm=0):
    p = squash(html.unescape(phrase))
    for i in range(frm, len(segs)):
        if p in segtxt[i]: return i
    # phrase spanning two segments
    for i in range(frm, len(segs) - 1):
        if p in segtxt[i] + segtxt[i + 1]: return i
    return None

sections = re.findall(r'<section([^>]*)>(.*?)</section>', spec, flags=re.S)
attr = lambda a, k: (re.search(k + r'="([^"]*)"', a) or [None, ''])[1]
slides, cursor, problems = [], 0, []
for a, body in sections:
    i = find(attr(a, 'data-anchor'), cursor)
    if i is None: problems.append('slide anchor not found: ' + attr(a, 'data-anchor')); continue
    cursor = i
    slides.append(dict(kind=attr(a, 'data-kind') or 'content', title=attr(a, 'data-title'), code=attr(a, 'data-code'), body=body, seg=i, start=0.0 if not slides else segs[i]['start']))
for k, s in enumerate(slides):
    s['end'] = slides[k + 1]['start'] if k + 1 < len(slides) else dur

tweens, uid = [], [0]
def nid():
    uid[0] += 1; return f'e{uid[0]}'

for k, s in enumerate(slides):
    def rep(m):
        phrase = m.group(1); i = find(phrase, s['seg'])
        t = segs[i]['start'] if i is not None else None
        if t is None or t >= s['end']:
            problems.append(f"slide {k} '{s['title']}': data-at '{phrase}' not found within slide"); t = s['start'] + 0.6
        t = max(t, s['start'] + 0.5)
        e = nid(); tweens.append((t, e)); return f'id="{e}" data-t="{t:.2f}"'
    s['body'] = re.sub(r'data-at="([^"]*)"', rep, s['body']).replace('<br/>', '<span class="brk"></span>')

# section ticks for progress bar (content slides with a number)
ticks = [(s['start'] / dur, re.match(r'(\d+)\.', s['title']).group(1)) for s in slides if re.match(r'\d+\.', s['title'])]

out = []
for k, s in enumerate(slides):
    sid = f's{k}'
    if s['kind'] == 'title':
        inner = f'<div class="title-wrap" id="{sid}-in">{s["body"]}</div>'
    else:
        code = f'<div class="code">評鑑項目　{html.escape(s["code"])}</div>' if s['code'] else ''
        inner = f'<div class="slide-in" id="{sid}-in"><div class="head"><h2>{html.escape(s["title"])}</h2>{code}</div><div class="body">{s["body"]}</div></div>'
    out.append(f'<section id="{sid}" class="clip slide" data-start="{s["start"]:.3f}" data-duration="{s["end"]-s["start"]:.3f}" data-track-index="1">{inner}</section>')
    tweens.append((s['start'] + 0.01, f'{sid}-in', 'slide'))

subs = '\n'.join(f'<div id="sub{i}" class="clip sub" data-start="{x["start"]:.3f}" data-duration="{x["end"]-x["start"]:.3f}" data-track-index="3"><span>{html.escape(x["text"])}</span></div>' for i, x in enumerate(segs))
tick_html = ''.join(f'<i style="left:{p*100:.3f}%"><b>{n}</b></i>' for p, n in ticks)

js = []
for tw in sorted(tweens):
    t, e = tw[0], tw[1]
    if len(tw) == 3:
        js.append(f'tl.fromTo("#{e}",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.6,ease:"power3.out"}},{t:.2f});')
    else:
        js.append(f'tl.fromTo("#{e}",{{opacity:0,y:18}},{{opacity:1,y:0,duration:0.5,ease:"power2.out"}},{t:.2f});')
        js.append(f'tl.fromTo("#{e}",{{boxShadow:"0 0 0 3px rgba(250,204,21,.9)"}},{{boxShadow:"0 0 0 3px rgba(250,204,21,0)",duration:2.2,ease:"power1.in"}},{t+0.3:.2f});')

css = open(f'{HERE}/shared/theme.css', encoding='utf-8').read()
doc = f'''<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1920, height=1080" />
<script src="assets/gsap.min.js"></script>
<style>
@font-face {{ font-family: "Noto Sans TC"; src: url("assets/fonts/NotoSansTC.ttf"); font-weight: 100 900; }}
{css}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{dur:.3f}" data-width="1920" data-height="1080">
  <div class="bg"></div>
  <div class="topbar"><span class="brand">iPAS AIoT 初級 · D{dnum}</span><span class="topic">物聯網架構、感測與無線通訊</span></div>
  {''.join(out)}
  <div class="subwrap">{subs}</div>
  <div class="progress"><div class="track">{tick_html}<div id="bar" class="bar"></div></div></div>
  <audio id="narration" src="assets/narration.mp3" data-start="0" data-duration="{dur:.3f}" data-track-index="0" data-volume="1"></audio>
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
tl.fromTo("#bar", {{scaleX: 0}}, {{scaleX: 1, duration: {dur:.3f}, ease: "none"}}, 0);
{chr(10).join(js)}
window.__timelines["main"] = tl;
</script>
</body>
</html>
'''
open(f'{D}/index.html', 'w', encoding='utf-8').write(doc)
json.dump([{k: s[k] for k in ('title', 'code', 'start', 'end')} for s in slides], open(f'{D}/slides.timing.json', 'w'), ensure_ascii=False, indent=1)
print(f'{len(slides)} slides, {len(segs)} subtitles, {len(tweens)} tweens, duration {dur:.2f}s')
for p in problems: print('WARN', p)
