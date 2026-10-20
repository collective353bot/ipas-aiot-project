#!/usr/bin/env python3
"""Align a narration script (ground-truth text) to the final narration mp3.

Usage:
  python align.py --audio ../audio/v2/d02.mp3 --script ../audio/scripts_v2/d02.txt --out d02/ [--model small]
  python align.py --asr d02/asr_words.json ...   # reuse a cached ASR word list

Pipeline: faster-whisper (word timestamps) -> OpenCC s2t -> char-level
SequenceMatcher between normalized script and ASR chars -> each subtitle chunk
gets start = time of its first matched char, end = last matched char
(unmatched chars interpolated from neighbours). Output text is always the
SCRIPT wording (cleaned for display), never ASR text.
Writes <out>/<day>.srt, <out>/<day>.segments.json, <out>/asr_words.json, <out>/align_report.json
"""
import argparse, json, re, os, sys, difflib, subprocess, tempfile

DISPLAY_FIX = [  # TTS-spelled forms -> display forms (applied after letter joining)
    ("i PAS", "iPAS"), ("HCSR 501", "HC-SR501"), ("HCSR 04", "HC-SR04"), ("DHT 11", "DHT11"),
    ("ADXL 345", "ADXL345"), ("MPU 6050", "MPU6050"), ("MQ 2", "MQ-2"), ("MQ2", "MQ-2"), ("I 平方 C", "I²C"),
    ("802 點 11 n", "802.11n"), ("802 點 15 點 4", "802.15.4"), ("ESP 32", "ESP32"),
    ("NB IoT", "NB-IoT"), ("Sub 1G", "Sub-1G"), ("Sub 1 G", "Sub-1G"), ("e SIM", "eSIM"), ("i SIM", "iSIM"),
    ("LTE Cat 1", "LTE Cat.1"), ("Cat 4", "Cat.4"), ("40 千赫茲", "40 kHz"),
]

def display(s):
    s = s.strip()
    prev = None
    while prev != s:  # join runs of single ASCII letters/digits spaced for TTS: "O S I" -> "OSI"
        prev = s
        s = re.sub(r'(?<![A-Za-z0-9.])([A-Za-z0-9]) (?=[A-Za-z0-9](?![A-Za-z0-9]))', r'\1', s)
    for a, b in DISPLAY_FIX:
        s = s.replace(a, b)
    return s

def norm_chars(s):
    return [c.lower() for c in s if c.isalnum()]

def chunk_script(text, maxlen=30):
    chunks = []
    for line in text.splitlines():
        line = line.strip()
        if not line: continue
        sents = [x for x in re.split(r'(?<=[。！？!?])|(?<=……)', line) if x.strip()]
        for s in sents:
            chunks.extend(split_long(s.strip(), maxlen))
    return chunks

def split_long(s, maxlen):
    if len(display(s)) <= maxlen: return [s]
    # split at the comma-like mark nearest the middle
    marks = [m.end() for m in re.finditer(r'[，、：；,]', s) if 4 < m.end() < len(s) - 3]
    if not marks:
        return [s]
    mid = len(s) / 2
    k = min(marks, key=lambda x: abs(x - mid))
    return split_long(s[:k].strip(), maxlen) + split_long(s[k:].strip(), maxlen)

def run_asr(audio, model):
    from faster_whisper import WhisperModel
    import soundfile as sf
    wav = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', audio, '-ac', '1', '-ar', '16000', wav], check=True)
    aud, _ = sf.read(wav, dtype='float32')
    m = WhisperModel(model, device='cpu', compute_type='int8')
    segs, _ = m.transcribe(aud, language='zh', word_timestamps=True, vad_filter=True, condition_on_previous_text=False, initial_prompt='以下是繁體中文的課程。')
    return [{'w': w.word, 's': round(w.start, 3), 'e': round(w.end, 3)} for s in segs for w in s.words]

def srt_ts(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--audio', required=True); ap.add_argument('--script', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--asr'); ap.add_argument('--model', default='small')
    ap.add_argument('--day'); ap.add_argument('--maxlen', type=int, default=30)
    a = ap.parse_args()
    day = a.day or os.path.splitext(os.path.basename(a.audio))[0]
    os.makedirs(a.out, exist_ok=True)
    asr_path = a.asr or os.path.join(a.out, 'asr_words.json')
    if os.path.exists(asr_path):
        words = json.load(open(asr_path))
    else:
        words = run_asr(a.audio, a.model); json.dump(words, open(asr_path, 'w'), ensure_ascii=False)
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.audio]))
    try:
        import opencc; cc = opencc.OpenCC('s2t')
    except Exception:
        cc = None
    # ASR char stream with per-char times (linear within a word)
    achars, atimes = [], []
    for w in words:
        t = cc.convert(w['w']) if cc else w['w']
        cs = norm_chars(t)
        for i, c in enumerate(cs):
            n = len(cs); achars.append(c)
            atimes.append((w['s'] + (w['e'] - w['s']) * i / n, w['s'] + (w['e'] - w['s']) * (i + 1) / n))
    chunks = chunk_script(open(a.script, encoding='utf-8').read(), a.maxlen)
    schars, owner = [], []
    for ci, ch in enumerate(chunks):
        for c in norm_chars(ch): schars.append(c); owner.append(ci)
    sm = difflib.SequenceMatcher(None, schars, achars, autojunk=False)
    smap = [None] * len(schars)
    for b in sm.get_matching_blocks():
        for k in range(b.size): smap[b.a + k] = b.b + k
    matched = sum(x is not None for x in smap)
    # interpolate times for unmatched script chars
    st = [None] * len(schars); en = [None] * len(schars)
    for i, j in enumerate(smap):
        if j is not None: st[i], en[i] = atimes[j]
    known = [i for i in range(len(schars)) if st[i] is not None]
    import bisect
    for i in range(len(schars)):
        if st[i] is None:
            k = bisect.bisect(known, i)
            lo = known[k - 1] if k > 0 else None; hi = known[k] if k < len(known) else None
            t0 = en[lo] if lo is not None else 0.0; t1 = st[hi] if hi is not None else dur
            i0 = lo if lo is not None else -1; i1 = hi if hi is not None else len(schars)
            f = (i - i0) / (i1 - i0); st[i] = en[i] = t0 + (t1 - t0) * f
    segs, report = [], []
    for ci, ch in enumerate(chunks):
        idx = [i for i in range(len(schars)) if owner[i] == ci]
        if not idx: continue
        cov = sum(smap[i] is not None for i in idx) / len(idx)
        segs.append({'start': round(st[idx[0]], 3), 'end': round(en[idx[-1]], 3), 'text': display(ch).rstrip('，、：；,'), 'match': round(cov, 2)})
    # tidy: monotonic, min duration, small lead/tail, fill short gaps so subtitles don't flicker
    for i, s in enumerate(segs):
        s['start'] = max(0.0, s['start'] - 0.08)
        if i and s['start'] < segs[i - 1]['end']: segs[i - 1]['end'] = s['start'] = max(segs[i - 1]['start'] + 0.3, s['start'])
    for i, s in enumerate(segs):
        nxt = segs[i + 1]['start'] if i + 1 < len(segs) else dur
        s['end'] = min(nxt, max(s['end'] + 0.25, s['start'] + 0.8))
        if nxt - s['end'] < 0.6: s['end'] = nxt
        s['start'], s['end'] = round(s['start'], 3), round(s['end'], 3)
    low = [dict(i=i, **s) for i, s in enumerate(segs) if s['match'] < 0.6]
    json.dump([{k: s[k] for k in ('start', 'end', 'text')} for s in segs], open(os.path.join(a.out, f'{day}.segments.json'), 'w'), ensure_ascii=False, indent=1)
    with open(os.path.join(a.out, f'{day}.srt'), 'w', encoding='utf-8') as f:
        for i, s in enumerate(segs, 1): f.write(f"{i}\n{srt_ts(s['start'])} --> {srt_ts(s['end'])}\n{s['text']}\n\n")
    json.dump({'audio_duration': dur, 'segments': len(segs), 'char_match_ratio': round(matched / len(schars), 3), 'low_match_segments': low},
              open(os.path.join(a.out, 'align_report.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'{len(segs)} segments, char match {matched/len(schars):.1%}, low-match {len(low)}; last end {segs[-1]["end"]:.2f}/{dur:.2f}s')

if __name__ == '__main__':
    main()
