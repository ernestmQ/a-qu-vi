"""Pruebas de acento: Piper es_ES (voces de España) + conversión a la voz de referencia con kNN-VC, y Chatterbox con más referencia.
Uso: python scripts/prueba_voz2.py <frases.json> <ref.mp3> <salida_dir>"""
import json, os, subprocess, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numeros import para_voz
frases, ref, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True); F = [para_voz(f).replace("{", "").replace("}", "") for f in json.load(open(frases))]
M = os.path.expanduser("~/m"); HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES"
def sh(*a): subprocess.run(a, check=True)
# --- Piper (España) + kNN-VC ---
from piper import PiperVoice
for voz in ["davefx/medium/es_ES-davefx-medium", "sharvard/medium/es_ES-sharvard-medium", "carlfm/x_low/es_ES-carlfm-x_low"]:
    nom = voz.split("/")[-1]; p = f"{M}/{nom}.onnx"
    if not os.path.exists(p): sh("curl", "-sSL", "-o", p, f"{HF}/{voz}.onnx"); sh("curl", "-sSL", "-o", p + ".json", f"{HF}/{voz}.onnx.json")
    v = PiperVoice.load(p); trozos = []
    for i, f in enumerate(F):
        w = f"{out}/{nom}_{i}.wav"
        with wave.open(w, "wb") as wf:
            (v.synthesize_wav(f, wf) if hasattr(v, "synthesize_wav") else v.synthesize(f, wf))
        trozos.append(w)
    lista = f"{out}/{nom}.txt"; open(lista, "w").write("".join(f"file '{t}'\nfile '/tmp/silencio.wav'\n" for t in trozos))
    sh("ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono", "-t", "0.6", "/tmp/silencio.wav")
    sh("ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista, "-ar", "22050", "-ac", "1", f"{out}/{nom}_base.wav")
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{out}/{nom}_base.wav"], capture_output=True, text=True).stdout)
    json.dump({"segments": [{"id": "s01", "start": 0.0, "end": d}]}, open(f"{out}/{nom}_m.json", "w"))
    sh("python", os.path.join(os.path.dirname(os.path.abspath(__file__)), "vc.py"), "/tmp/r.pt", f"{out}/{nom}_base.wav", f"{out}/{nom}_m.json", f"{out}/{nom}_padre.wav", "8")
    print("ok", nom, flush=True)
