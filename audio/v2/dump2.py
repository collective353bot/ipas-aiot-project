import sys, subprocess, numpy as np, re
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
def dur(f): return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
for d in sys.argv[1:]:
    raw=f'raw/{d}.mp3'; D=dur(raw); off=max(0,D-200)
    pcm=subprocess.run(["ffmpeg","-v","error","-ss",str(off),"-i",raw,"-f","s16le","-ac","1","-ar","16000","-"],capture_output=True).stdout
    a=np.frombuffer(pcm,np.int16).astype(np.float32)/32768
    segs,_=m.transcribe(a,language="zh",condition_on_previous_text=False,vad_filter=True,initial_prompt="以下是繁體中文的句子。")
    out=subprocess.run(["ffmpeg","-v","info","-ss",str(off),"-i",raw,"-af","silencedetect=n=-40dB:d=0.3","-f","null","-"],capture_output=True,text=True).stderr
    st=[float(x)+off for x in re.findall(r'silence_start: ([\d.]+)',out)]
    en=[float(x)+off for x in re.findall(r'silence_end: ([\d.]+)',out)]
    print('==',d)
    for s in segs: print(f'  {s.start+off:.2f}-{s.end+off:.2f} {s.text}')
    print('  SIL>=0.3:',[(round(a,2),round(b-a,2)) for a,b in zip(st,en)],flush=True)
