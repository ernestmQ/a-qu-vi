"""Prueba de voz clonada directamente (Chatterbox multilingüe, licencia MIT) a partir de la grabación de referencia.
Uso: python scripts/prueba_voz.py <frases.json> <ref.wav> <salida_dir>"""
import json, os, sys
import torch, torchaudio as ta
_load = torch.load
torch.load = lambda *a, **k: _load(*a, **{**k, "map_location": "cpu"})
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numeros import para_voz
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
torch.set_num_threads(os.cpu_count() or 2)
frases, ref, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
F = json.load(open(frases))
for nombre, kw in [("a", dict(exaggeration=0.5, cfg_weight=0.5)), ("b", dict(exaggeration=0.4, cfg_weight=0.3))]:
    trozos = []
    for f in F:
        w = m.generate(para_voz(f), language_id="es", audio_prompt_path=ref, **kw)
        trozos += [w, torch.zeros(1, int(0.6 * m.sr))]
    ta.save(f"{out}/{nombre}.wav", torch.cat(trozos, 1), m.sr)
    print("ok", nombre, flush=True)
