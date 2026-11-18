#!/usr/bin/env bash
# Dependencias del trabajo: ffmpeg, Python (Kokoro, torch CPU), modelos y Node.
set -euo pipefail
M=${M:-$HOME/m}; mkdir -p "$M"
command -v ffmpeg >/dev/null || (sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg >/dev/null)
sudo apt-get install -y -qq sox libsox-fmt-all >/dev/null 2>&1 || true
python -m pip install -q --upgrade pip
python -m pip install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu
python -m pip install -q kokoro-onnx==0.6.1 soundfile numpy
python -m pip install -q qwen-tts
[ -f "$M/kokoro.onnx" ] || curl -sSL -o "$M/kokoro.onnx" https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
[ -f "$M/voices.bin" ] || curl -sSL -o "$M/voices.bin" https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin
[ -f "$M/WavLM-Large.pt" ] || curl -sSL -o "$M/WavLM-Large.pt" https://github.com/bshall/knn-vc/releases/download/v0.1/WavLM-Large.pt
[ -f "$M/prematch_g_02500000.pt" ] || curl -sSL -o "$M/prematch_g_02500000.pt" https://github.com/bshall/knn-vc/releases/download/v0.1/prematch_g_02500000.pt
[ -d "$M/knn-vc" ] || git clone -q --depth 1 https://github.com/bshall/knn-vc.git "$M/knn-vc"
md5sum "$M/kokoro.onnx" "$M/voices.bin" | awk '{print $1}' | tr '\n' ' '; echo
npm ci --silent --no-audit --no-fund
