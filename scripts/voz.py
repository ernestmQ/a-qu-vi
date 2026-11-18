"""Narración: Kokoro (voz em_alex) frase a frase, con pausas, y manifiesto de tiempos.
Uso: python3 scripts/voz.py <guion.json> <dir_salida>   (variables: M = carpeta de modelos)"""
import json, os, re, sys, numpy as np, soundfile as sf
from kokoro_onnx import Kokoro
M = os.environ.get("M", os.path.expanduser("~/m")); SR = 24000
K = Kokoro(f"{M}/kokoro.onnx", f"{M}/voices.bin")
PAUSA = float(os.environ.get("AQ_PAUSA", "0.85")); VEL = 0.95
EN = [r"\bSharpe\b", r"\bbacktesting\b", r"\brisk parity\b", r"\bshrinkage\b", r"\bmachine learning\b", r"\bbacktester\b", r"\bbacktest\b", r"\btrading\b", r"\bbootstrap\b", r"\bPython\b", r"\bQuant\b", r"\bquant\b", r"\bNumPy\b", r"\bdrawdown\b"]
def marca(t):
    for w in EN: t = re.sub(w, lambda m: "{" + m.group(0) + "}", t)
    return t
def fonemas(t):
    out = []
    for i, p in enumerate(re.split(r"\{([^}]+)\}", t)):
        if p.strip():
            ph = K.tokenizer.phonemize(p, "en-us" if i % 2 else "es").strip()
            if ph: out.append(ph)
    return " ".join(out)
def habla(t):
    trozos = []
    for s in [s for s in re.split(r"(?<=[.!?¿?])\s+", t) if s.strip()]:
        a, _ = K.create(fonemas(s), voice="em_alex", speed=VEL, lang="es", is_phonemes=True)
        trozos += [a.astype(np.float32), np.zeros(int(0.18 * SR), np.float32)]
    return np.concatenate(trozos[:-1])
def recorta(a, u=0.01):
    i = np.where(np.abs(a) > u)[0]
    return a[max(0, i[0] - int(.03 * SR)): i[-1] + int(.06 * SR)] if len(i) else a
g = json.load(open(sys.argv[1])); d = sys.argv[2]; os.makedirs(d, exist_ok=True)
pista, segs, t = [np.zeros(int(0.4 * SR), np.float32)], [], 0.4
for s in g["segments"]:
    a = recorta(habla(marca(s["text"]))); du = len(a) / SR
    segs.append({**s, "start": round(t, 3), "duration": round(du, 3), "end": round(t + du, 3)})
    pista += [a, np.zeros(int(PAUSA * SR), np.float32)]; t += du + PAUSA
sf.write(f"{d}/crudo.wav", np.concatenate(pista), SR)
json.dump({"provider": "kokoro-em_alex+0.0st", "duration": round(segs[-1]["end"], 3), "segments": segs}, open(f"{d}/manifest.json", "w"), ensure_ascii=False, indent=1)
