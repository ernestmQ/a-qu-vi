"""Chatterbox con acento neutro: (1) referencia de tu padre con cfg bajo; (2) referencia neutra sintética y después conversión al timbre de tu padre (kNN-VC).
Uso: python scripts/prueba_voz3.py <frases.json> <ref_padre.wav> <ref_neutra.wav> <salida_dir>"""
import json, os, subprocess, sys
import torch, torchaudio as ta
_load = torch.load
torch.load = lambda *a, **k: _load(*a, **{**k, "map_location": "cpu"})
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numeros import para_voz
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
torch.set_num_threads(os.cpu_count() or 2)
frases, refp, refn, out = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
F = [para_voz(f).replace("{", "").replace("}", "") for f in json.load(open(frases))]
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
def gen(nom, ref, **kw):
    tr = []
    for f in F: tr += [m.generate(f, language_id="es", audio_prompt_path=ref, **kw), torch.zeros(1, int(0.6 * m.sr))]
    ta.save(f"{out}/{nom}.wav", torch.cat(tr, 1), m.sr); print("ok", nom, flush=True)
gen("padre_cfg0", refp, exaggeration=0.5, cfg_weight=0.0)
gen("padre_cfg02", refp, exaggeration=0.4, cfg_weight=0.2)
gen("neutra", refn, exaggeration=0.5, cfg_weight=0.5)
d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{out}/neutra.wav"], capture_output=True, text=True).stdout)
json.dump({"segments": [{"id": "s01", "start": 0.0, "end": d}]}, open(f"{out}/m.json", "w"))
subprocess.run(["python", os.path.join(os.path.dirname(os.path.abspath(__file__)), "vc.py"), "/tmp/r.pt", f"{out}/neutra.wav", f"{out}/m.json", f"{out}/neutra_padre.wav", "8"], check=True)
print("ok neutra_padre", flush=True)
