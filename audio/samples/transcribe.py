import sys, subprocess, numpy as np
from faster_whisper import WhisperModel
m=WhisperModel("small",device="cpu",compute_type="int8")
for f in sys.argv[1:]:
    raw=subprocess.run(["ffmpeg","-v","error","-i",f,"-f","s16le","-ac","1","-ar","16000","-"],capture_output=True).stdout
    a=np.frombuffer(raw,np.int16).astype(np.float32)/32768
    segs,_=m.transcribe(a,language="zh",beam_size=5,initial_prompt="以下是繁體中文的句子。")
    print("==",f); print("".join(s.text for s in segs)); sys.stdout.flush()
