import sys, subprocess, re, numpy as np, json
from faster_whisper import WhisperModel
V='/workspace/ipas_aiot/audio/v2'
m=WhisperModel("small",device="cpu",compute_type="int8")
def dur(f): return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
for d in sys.argv[1:]:
    raw=f'{V}/raw/{d}.mp3'; D=dur(raw); T=240.0; off=max(0,D-T)
    pcm=subprocess.run(["ffmpeg","-v","error","-ss",str(off),"-i",raw,"-f","s16le","-ac","1","-ar","16000","-"],capture_output=True).stdout
    a=np.frombuffer(pcm,np.int16).astype(np.float32)/32768
    segs,_=m.transcribe(a,language="zh",word_timestamps=True,initial_prompt="以下是繁體中文的句子。先想一想，好，答案是")
    words=[(w.start+off,w.end+off,w.word) for s in segs for w in s.words]
    pairs=[]
    for i,(s,e,w) in enumerate(words):
        if '想' in w:
            for j in range(i+1,min(i+5,len(words))):
                if '好' in words[j][2]:
                    if not pairs or s-pairs[-1][1]>3: pairs.append((e,words[j][0]))
                    break
    # silences
    out=subprocess.run(["ffmpeg","-v","info","-ss",str(off),"-i",raw,"-af","silencedetect=n=-40dB:d=0.12","-f","null","-"],capture_output=True,text=True).stderr
    st=[float(x)+off for x in re.findall(r'silence_start: ([\d.]+)',out)]
    en=[float(x)+off for x in re.findall(r'silence_end: ([\d.]+)',out)]
    sil=list(zip(st,en))
    cuts=[]
    for (e,s) in pairs:
        c=[(b-a_,a_,b) for a_,b in sil if b>e-0.4 and a_<s+0.2]
        cuts.append(round((max(c)[1]+max(c)[2])/2,2) if c else round(s-0.05,2))
    exp=open(f'/workspace/ipas_aiot/audio/scripts_v2/{d}.txt').read().count('先想一想')
    print(d,'raw',round(D,1),'expected',exp,'found',len(cuts),cuts,flush=True)
    if len(cuts)!=exp: print(d,'MISMATCH - skipped'); continue
    f=[];seq=''
    pts=[0]+cuts
    for i in range(len(cuts)+1):
        b=cuts[i] if i<len(cuts) else None
        f.append(f"[0:a]atrim=start={pts[i]}"+(f":end={b}" if b else "")+f",asetpts=PTS-STARTPTS[s{i}]")
        seq+=f"[s{i}]"
        if b: f.append(f"anullsrc=r=44100:cl=mono,atrim=duration=4[z{i}]"); seq+=f"[z{i}]"
    fc=";".join(f)+f";{seq}concat=n={2*len(cuts)+1}:v=0:a=1[out]"
    subprocess.run(["ffmpeg","-v","error","-y","-i",raw,"-filter_complex",fc,"-map","[out]","-ac","1","-ar","44100","-c:a","libmp3lame","-b:a","128k",f'{V}/{d}.mp3'],check=True)
    print(d,'final',round(dur(f'{V}/{d}.mp3'),1),flush=True)
