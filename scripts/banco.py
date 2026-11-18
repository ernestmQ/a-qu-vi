"""Banco de pruebas de voces. Uso: python scripts/banco.py <motor> <cfg.json> <salida_dir> [ref_dir]
Cada motor escribe <salida>/<motor>__<voz>.wav y un registro con tiempos."""
import json, os, re, sys, time, traceback
import numpy as np, soundfile as sf

motor, cfgp, out = sys.argv[1:4]
refdir = sys.argv[4] if len(sys.argv) > 4 else None
C = json.load(open(cfgp)); T = C["texto"]; RT = C["ref_texto"]
os.makedirs(out, exist_ok=True)
REG = open(f"{out}/registro_{motor}.txt", "a")
def log(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); REG.write(s + "\n"); REG.flush()

def frases(t): return [f.strip() for f in re.split(r"(?<=[.!?])\s+", t) if f.strip()]
def une(partes, sr, pausa=0.4):
    z = np.zeros(int(pausa * sr), dtype=np.float32); r = []
    for p in partes: r += [np.asarray(p, dtype=np.float32).reshape(-1), z]
    return np.concatenate(r[:-1])
def guarda(nom, wav, sr, t0):
    w = np.asarray(wav, dtype=np.float32).reshape(-1); sf.write(f"{out}/{nom}.wav", w, sr)
    d = len(w) / sr; g = time.time() - t0
    log(f"OK {nom} audio={d:.1f}s generacion={g:.0f}s x{g / max(d, 1e-6):.1f}")

def hilos():
    import torch; torch.set_num_threads(os.cpu_count() or 4); return torch

def qwen_diseno(sexo):
    torch = hilos(); from qwen_tts import Qwen3TTSModel
    m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign", device_map="cpu", dtype=torch.float32)
    langs = m.model.get_supported_languages(); log("idiomas", langs)
    lang = next((l for l in langs if l.lower().startswith("span")), "Spanish")
    ins = C["instr_qwen"][sexo]
    torch.manual_seed(7); t0 = time.time()
    w, sr = m.generate_voice_design(text=RT, language=lang, instruct=ins); guarda(f"ref_qwen_{sexo}", w[0], sr, t0)
    torch.manual_seed(7); t0 = time.time()
    w, sr = m.generate_voice_design(text=T, language=lang, instruct=ins); guarda(f"qwen_diseno_{sexo}", w[0], sr, t0)

def qwen_clon():
    torch = hilos(); from qwen_tts import Qwen3TTSModel
    m = Qwen3TTSModel.from_pretrained("Qwen/Qwen3-TTS-12Hz-1.7B-Base", device_map="cpu", dtype=torch.float32)
    lang = next((l for l in m.model.get_supported_languages() if l.lower().startswith("span")), "Spanish")
    for sexo in ("h", "m"):
        ref = f"{refdir}/ref_qwen_{sexo}.wav"
        if not os.path.exists(ref): log("falta", ref); continue
        p = m.create_voice_clone_prompt(ref_audio=ref, ref_text=RT)
        torch.manual_seed(7); t0 = time.time(); partes = []; sr = 24000
        for bloque in C["bloques"]:
            w, sr = m.generate_voice_clone(text=bloque, language=lang, voice_clone_prompt=p); partes.append(w[0])
        guarda(f"qwen_clon_{sexo}", une(partes, sr, 0.45), sr, t0)

def chatterbox_clon():
    torch = hilos()
    _l = torch.load; torch.load = lambda *a, **k: _l(*a, **{**k, "map_location": "cpu"})
    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    m = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    for sexo in ("h", "m"):
        ref = f"{refdir}/ref_qwen_{sexo}.wav"
        if not os.path.exists(ref): log("falta", ref); continue
        torch.manual_seed(7); t0 = time.time()
        partes = [m.generate(f, language_id="es", audio_prompt_path=ref, exaggeration=0.5, cfg_weight=0.5)[0].numpy() for f in frases(T)]
        guarda(f"chatterbox_clon_{sexo}", une(partes, m.sr), m.sr, t0)

def voxcpm(sexo):
    torch = hilos(); from voxcpm import VoxCPM
    m = VoxCPM.from_pretrained("openbmb/VoxCPM2", load_denoiser=False, optimize=False, device="cpu")
    sr = m.tts_model.sample_rate; d = C["instr_vox"][sexo]
    torch.manual_seed(7); t0 = time.time()
    w = m.generate(text=f"({d}){RT}", cfg_value=2.0, inference_timesteps=10); guarda(f"ref_vox_{sexo}", w, sr, t0)
    t0 = time.time(); partes = []
    for bloque in C["bloques"]:
        partes.append(m.generate(text=bloque, prompt_wav_path=f"{out}/ref_vox_{sexo}.wav", prompt_text=RT,
                                 reference_wav_path=f"{out}/ref_vox_{sexo}.wav", cfg_value=2.0, inference_timesteps=10))
    guarda(f"voxcpm_{sexo}", une(partes, sr, 0.45), sr, t0)

def magpie():
    torch = hilos(); from nemo.collections.tts.models import MagpieTTSModel
    m = MagpieTTSModel.from_pretrained("nvidia/magpie_tts_multilingual_357m").eval()
    sr = int(getattr(m, "sample_rate", 0) or getattr(getattr(m, "cfg", None), "sample_rate", 22050))
    for nom, idx in (("sofia", 1), ("aria", 2), ("leo", 4), ("jason", 3)):
        t0 = time.time(); partes = []
        with torch.no_grad():
            for f in frases(T):
                a, n = m.do_tts(f, language="es", apply_TN=False, speaker_index=idx)
                partes.append(a[0, : int(n[0])].float().cpu().numpy())
        guarda(f"magpie_{nom}", une(partes, sr), sr, t0)

def pocket():
    hilos(); from pocket_tts import TTSModel; from huggingface_hub import list_repo_files
    fs = [f for f in list_repo_files("kyutai/pocket-tts-without-voice-cloning") if "/spanish_24l/" in f and f.endswith(".safetensors") and "/embeddings/" in f]
    voces = sorted({os.path.basename(f)[:-12] for f in fs}); log("voces", voces)
    if not voces:
        voces = sorted({os.path.basename(f)[:-12] for f in list_repo_files("kyutai/pocket-tts-without-voice-cloning") if "/spanish/" in f and "/embeddings/" in f})
    m = TTSModel.load_model(language="spanish_24l")
    for v in (["lola"] + [x for x in voces if x != "lola"])[:4]:
        try:
            t0 = time.time(); st = m.get_state_for_audio_prompt(v)
            a = m.generate_audio(st, T); guarda(f"pocket_{v}", a.numpy(), m.sample_rate, t0)
        except Exception: log(traceback.format_exc())

def supertonic():
    from supertonic import TTS
    m = TTS(model="supertonic-3", auto_download=True)
    for v in ["M1", "M2", "M3", "M4", "M5", "F1", "F2", "F3", "F4", "F5"]:
        t0 = time.time(); w, _ = m.synthesize(T, voice_style=m.get_voice_style(voice_name=v), speed=1.0, lang="es")
        guarda(f"supertonic_{v}", w, m.sample_rate, t0)

def kokoro():
    from kokoro_onnx import Kokoro
    m = Kokoro(os.path.expanduser("~/m/kokoro.onnx"), os.path.expanduser("~/m/voices.bin"))
    for v in ("em_alex", "ef_dora"):
        t0 = time.time(); partes = []
        for f in frases(T):
            a, sr = m.create(f, voice=v, speed=0.95, lang="es"); partes.append(a)
        guarda(f"kokoro_{v}", une(partes, sr), sr, t0)

F = {"qwen_h": lambda: qwen_diseno("h"), "qwen_m": lambda: qwen_diseno("m"), "qwen_clon": qwen_clon,
     "chatterbox": chatterbox_clon, "voxcpm_h": lambda: voxcpm("h"), "voxcpm_m": lambda: voxcpm("m"),
     "magpie": magpie, "pocket": pocket, "supertonic": supertonic, "kokoro": kokoro}
try: F[motor]()
except Exception: log(traceback.format_exc()); sys.exit(1)
