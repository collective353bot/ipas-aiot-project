#!/usr/bin/env python3
# usage: tts.py dXX  -> scripts/dXX.txt -> dXX.mp3 ; "[停頓]" = 4s silence
import sys, subprocess, pathlib, re, asyncio, edge_tts
A = pathlib.Path(__file__).parent; VOICE='zh-TW-HsiaoChenNeural'; RATE='+5%'
async def say(text, out):
    for i in range(4):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(out)); return
        except Exception as e: print('retry', e); await asyncio.sleep(3)
    raise SystemExit('tts failed')
def chunks(seg, n=1200):
    paras=[p.strip() for p in seg.split('\n') if p.strip()]; cur=''
    for p in paras:
        if cur and len(cur)+len(p)>n: yield cur; cur=''
        cur+=p+'\n'
    if cur: yield cur
d=sys.argv[1]; tmp=A/'tmp'/d; tmp.mkdir(parents=True,exist_ok=True)
for f in tmp.glob('*'): f.unlink()
sil=tmp/'sil.mp3'
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','anullsrc=r=24000:cl=mono','-t','4','-c:a','libmp3lame','-b:a','64k',str(sil)],check=True)
text=(A/'scripts'/f'{d}.txt').read_text(encoding='utf-8')
parts=[]; k=0
for si,seg in enumerate(text.split('[停頓]')):
    if si: parts.append(sil)
    for c in chunks(seg):
        k+=1; o=tmp/f'{k:03d}.mp3'; asyncio.run(say(c,o)); parts.append(o)
lst=tmp/'list.txt'; lst.write_text(''.join(f"file '{p}'\n" for p in parts))
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(lst),'-ac','1','-ar','24000','-c:a','libmp3lame','-b:a','64k',str(A/f'{d}.mp3')],check=True)
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(A/f'{d}.mp3')],capture_output=True,text=True).stdout)
print(d, f'{dur/60:.1f} min', len(re.sub(r'\s','',text)),'chars')
