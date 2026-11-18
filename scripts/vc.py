"""Conversión de voz con kNN-VC (WavLM-Large + HiFiGAN, CPU) frase a frase, conservando los tiempos.
Uso: python3 scripts/vc.py <rasgos_ref.pt> <origen.wav> <manifest.json> <salida.wav> [k=8]"""
import sys, types, json, os, subprocess, numpy as np, soundfile as sf
ta = types.ModuleType("torchaudio"); ta.transforms = types.ModuleType("torchaudio.transforms")
sys.modules["torchaudio"] = ta; sys.modules["torchaudio.transforms"] = ta.transforms
M = os.environ.get("M", os.path.expanduser("~/m")); sys.path.insert(0, f"{M}/knn-vc")
import torch
torch.set_num_threads(os.cpu_count() or 2)
from wavlm.WavLM import WavLM, WavLMConfig
from hifigan.models import Generator
from hifigan.utils import AttrDict
from matcher import KNeighborsVC
def a16k(p):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", p, "-ac", "1", "-ar", "16000", "/tmp/_16.wav"], check=True)
    return sf.read("/tmp/_16.wav", dtype="float32")[0]
ref, src, man, out = sys.argv[1:5]; k = int(sys.argv[5]) if len(sys.argv) > 5 else 8
h = AttrDict(json.load(open(f"{M}/knn-vc/hifigan/config_v1_wavlm.json")))
g = Generator(h); g.load_state_dict(torch.load(f"{M}/prematch_g_02500000.pt", map_location="cpu")["generator"]); g.eval(); g.remove_weight_norm()
ck = torch.load(f"{M}/WavLM-Large.pt", map_location="cpu"); w = WavLM(WavLMConfig(ck["cfg"])); w.load_state_dict(ck["model"]); w.eval()
vc = KNeighborsVC(w, g, h, "cpu"); mset = torch.load(ref)
y = a16k(src); m = json.load(open(man)); sal = np.zeros_like(y)
for s in m["segments"]:
    a, b = int(s["start"] * 16000), min(len(y), int(s["end"] * 16000) + 1600)
    q = vc.get_features(torch.from_numpy(y[a:b].copy()))
    z = vc.match(q, mset, topk=k, tgt_loudness_db=None).numpy(); n = min(len(z), b - a); sal[a:a + n] = z[:n]
sf.write(out, sal, 16000)
