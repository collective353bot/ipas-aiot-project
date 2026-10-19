import subprocess,re,numpy as np
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
for n in range(1,14):
    d=f'd{n:02d}'; f=f'{d}.mp3'
    D=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
    out=subprocess.run(["ffmpeg","-v","info","-i",f,"-af","silencedetect=n=-40dB:d=3.5","-f","null","-"],capture_output=True,text=True).stderr
    ends=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',out)]
    res=[]
    for e in ends:
        pcm=subprocess.run(["ffmpeg","-v","error","-ss",str(e-0.1),"-t","2.2","-i",f,"-f","s16le","-ac","1","-ar","16000","-"],capture_output=True).stdout
        a=np.frombuffer(pcm,np.int16).astype(np.float32)/32768
        segs,_=m.transcribe(a,language="zh",condition_on_previous_text=False)
        res.append(''.join(s.text for s in segs).strip()[:8])
    print(d, f'{D:.1f}s', f'{int(D//60)}:{int(D%60):02d}', 'pauses',len(ends), res, flush=True)
