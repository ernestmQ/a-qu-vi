"""Narración con Qwen3-TTS 1.7B Base clonando una voz fija, frase a frase, con pausas y manifiesto de tiempos.
Uso: python scripts/voz_qwen.py <guion.json> <dir_salida> <ref.wav> <ref.txt>"""
import json, os, re, sys, time
import numpy as np, soundfile as sf, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numeros import para_voz
from qwen_tts import Qwen3TTSModel

g, d, ref, reft = sys.argv[1:5]; os.makedirs(d, exist_ok=True)
PAUSA = float(os.environ.get("AQ_PAUSA", "0.85")); HUECO = 0.22
torch.set_num_threads(os.cpu_count() or 4)
m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
P = m.create_voice_clone_prompt(ref_audio=ref, ref_text=open(reft).read().strip())
SR = 24000

def recorta(a, u=0.01):
    i = np.where(np.abs(a) > u)[0]
    return a[max(0, i[0] - int(.03 * SR)): i[-1] + int(.06 * SR)] if len(i) else a

def frase(t):
    """Genera una frase; si la duración por carácter es anómala (cortes o divagaciones), reintenta con otra semilla."""
    global SR
    mejor = None
    for semilla in (7, 11, 23):
        torch.manual_seed(semilla)
        w, SR = m.generate_voice_clone(text=t, language="spanish", voice_clone_prompt=P)
        a = recorta(np.asarray(w[0], dtype=np.float32).reshape(-1)); r = len(a) / SR / max(len(t), 1)
        if mejor is None or abs(r - 0.064) < abs(mejor[1] - 0.064): mejor = (a, r)
        if 0.042 <= r <= 0.095: break
        print(f"  reintento ({r:.3f} s/car): {t[:60]}", flush=True)
    return mejor[0]

# Caché por frase: si hay voz anterior (cruda, sin normalizar) con su manifiesto, se reutilizan los segmentos cuyo texto no ha cambiado.
PREVIA = {}
if os.environ.get("AQ_PREVIA") and os.path.exists(os.environ["AQ_PREVIA"]):
    pa, psr = sf.read(os.environ["AQ_PREVIA"], dtype="float32")
    if pa.ndim > 1: pa = pa.mean(1)
    if psr != SR:
        import torchaudio.functional as AF
        pa = AF.resample(torch.from_numpy(pa), psr, SR).numpy()
    for s in json.load(open(os.environ["AQ_PREVIA_MAN"]))["segments"]:
        # clave: el texto HABLADO si el manifiesto lo guarda (así un cambio de pronunciación regenera la frase); si no, el escrito
        PREVIA[("voz", s["voz"]) if "voz" in s else ("txt", s.get("sub") or s["text"])] = pa[int(s["start"] * SR): int(s["end"] * SR)]
datos = json.load(open(g)); t0 = time.time(); reusadas = 0
pista, segs, t = [np.zeros(int(0.4 * SR), np.float32)], [], 0.4
for s in datos["segments"]:
    texto = para_voz(s.get("sub") or s["text"]).replace("{", "").replace("}", "")
    for a, b in ((r"\bMAD\b", "eme a de"), (r"\bcvxpy\b", "ce uve equis pai"), (r"\bHRP\b", "hache erre pe")): texto = re.sub(a, b, texto)
    clave = ("voz", texto) if ("voz", texto) in PREVIA else ("txt", s.get("sub") or s["text"])
    if clave in PREVIA and len(PREVIA[clave]) > SR // 2:
        a = PREVIA[clave]; reusadas += 1
    else:
        trozos = []
        for f in [x for x in re.split(r"(?<=[.!?])\s+", texto) if x.strip()]:
            trozos += [frase(f), np.zeros(int(HUECO * SR), np.float32)]
        a = np.concatenate(trozos[:-1])
    du = len(a) / SR
    segs.append({**s, "voz": texto, "start": round(t, 3), "duration": round(du, 3), "end": round(t + du, 3)})
    pista += [a, np.zeros(int(PAUSA * SR), np.float32)]; t += du + PAUSA
    print(f"{s['id']} {du:.1f}s ({time.time() - t0:.0f}s)", flush=True)
print(f"reutilizados {reusadas} de {len(datos['segments'])} segmentos", flush=True)
sf.write(f"{d}/crudo.wav", np.concatenate(pista), SR)
json.dump({"provider": "qwen3-tts-1.7b-base", "duration": round(segs[-1]["end"], 3), "segments": segs},
          open(f"{d}/manifest.json", "w"), ensure_ascii=False, indent=1)
