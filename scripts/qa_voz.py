"""Control de la voz: transcribe cada frase con Whisper y la compara con el guion.
Uso: python scripts/qa_voz.py <voiceover.wav> <manifest.json> <salida.json>
Marca las frases con más de un 15 % de palabras distintas (posible palabra mal dicha, cortada o inventada)."""
import json, os, re, sys, unicodedata
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numeros import para_voz
from faster_whisper import WhisperModel

wav, man, sal = sys.argv[1:4]
a, sr = sf.read(wav, dtype="float32")
if a.ndim > 1: a = a.mean(1)
m = json.load(open(man)); asr = WhisperModel("small", device="cpu", compute_type="int8")

def norm(t):
    t = para_voz(t).replace("{", "").replace("}", "")
    t = unicodedata.normalize("NFKD", t.lower()); t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-zñ ]+", " ", t).split()

def wer(r, h):
    d = list(range(len(h) + 1))
    for i in range(1, len(r) + 1):
        p, d[0] = d[0], i
        for j in range(1, len(h) + 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (r[i - 1] != h[j - 1]))
    return d[len(h)] / max(len(r), 1)

res = []
for s in m["segments"]:
    i0, i1 = int(max(0, s["start"] - 0.1) * sr), int((s["end"] + 0.15) * sr)
    x = a[i0:i1]
    if sr != 16000: x = np.interp(np.linspace(0, len(x), int(len(x) * 16000 / sr), endpoint=False), np.arange(len(x)), x).astype(np.float32)
    segs, _ = asr.transcribe(x, language="es", beam_size=5)
    h = " ".join(z.text for z in segs).strip()
    w = wer(norm(s.get("sub") or s["text"]), norm(h))
    res.append({"id": s["id"], "wer": round(w, 3), "oido": h, "guion": s.get("sub") or s["text"]})
mal = [r for r in res if r["wer"] > 0.15]
json.dump({"frases": len(res), "marcadas": mal, "wer_medio": round(sum(r["wer"] for r in res) / len(res), 3), "todas": res}, open(sal, "w"), ensure_ascii=False, indent=1)
print("qa voz:", len(mal), "frases marcadas de", len(res))
