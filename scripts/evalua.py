"""Evalúa muestras: duración, naturalidad (UTMOS, 1-5) y pronunciación (WER con Whisper).
Uso: python scripts/evalua.py <cfg.json> <dir_wavs> <salida.json>"""
import glob, json, os, re, sys, unicodedata
import numpy as np, soundfile as sf, torch, torchaudio
C = json.load(open(sys.argv[1])); D = sys.argv[2]
torch.set_num_threads(os.cpu_count() or 4)
mos = torch.hub.load("tarepan/SpeechMOS:v1.2.0", "utmos22_strong", trust_repo=True)
from faster_whisper import WhisperModel
asr = WhisperModel("small", device="cpu", compute_type="int8")

def norm(t):
    t = unicodedata.normalize("NFKD", t.lower()); t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-zñ ]+", " ", t).split()
def wer(r, h):
    r, h = norm(r), norm(h); d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(len(r), 1)

res = {}
for f in sorted(glob.glob(f"{D}/*.wav")):
    n = os.path.basename(f)[:-4]
    w, sr = sf.read(f, dtype="float32")
    if w.ndim > 1: w = w.mean(1)
    x = torchaudio.functional.resample(torch.from_numpy(w), sr, 16000)
    s = []
    for i in range(0, len(x), 16000 * 10):
        seg = x[i:i + 16000 * 10]
        if len(seg) > 16000 * 2: s.append(float(mos(seg.unsqueeze(0), 16000)))
    segs, _ = asr.transcribe(f, language="es", beam_size=5)
    txt = " ".join(z.text for z in segs).strip()
    ref = C["ref_texto"] if n.startswith("ref_") else C["texto"]
    res[n] = {"dur": round(len(w) / sr, 1), "utmos": round(float(np.mean(s)), 2) if s else None,
              "wer": round(wer(ref, txt), 3), "trans": txt}
    print(n, res[n]["dur"], res[n]["utmos"], res[n]["wer"], flush=True)
json.dump(res, open(sys.argv[3], "w"), ensure_ascii=False, indent=1)
