import sys, subprocess, numpy as np, json
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
def dur(f): return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
for d in sys.argv[1:]:
    raw=f'raw/{d}.mp3'; D=dur(raw); off=max(0,D-240)
    pcm=subprocess.run(["ffmpeg","-v","error","-ss",str(off),"-i",raw,"-f","s16le","-ac","1","-ar","16000","-"],capture_output=True).stdout
    a=np.frombuffer(pcm,np.int16).astype(np.float32)/32768
    segs,_=m.transcribe(a,language="zh",word_timestamps=True,initial_prompt="以下是繁體中文的句子。")
    words=[(round(w.start+off,2),round(w.end+off,2),w.word) for s in segs for w in s.words]
    json.dump(words,open(f'raw/{d}.words.json','w'),ensure_ascii=False)
    print(d,len(words),flush=True)
