#!/usr/bin/env bash
# Instala un motor del banco de voces en un runner Ubuntu (CPU).
set -euo pipefail
P="python -m pip install -q"
CPU="--index-url https://download.pytorch.org/whl/cpu"
sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg sox libsox-fmt-all >/dev/null
python -m pip install -q --upgrade pip
case "$1" in
  qwen_h|qwen_m|qwen_clon) $P torch torchaudio $CPU; $P qwen-tts soundfile ;;
  voxcpm_h|voxcpm_m)       $P torch torchaudio $CPU; $P voxcpm soundfile ;;
  magpie)                  $P torch torchaudio $CPU; ($P "nemo_toolkit[tts]" kaldialign && python -c "from nemo.collections.tts.models import MagpieTTSModel") \
                             || $P "nemo_toolkit[tts] @ git+https://github.com/NVIDIA/NeMo.git@main" kaldialign ;;
  pocket)                  $P torch $CPU; $P pocket-tts soundfile huggingface_hub ;;
  supertonic)              $P supertonic soundfile ;;
  kokoro)                  $P kokoro-onnx==0.6.1 soundfile numpy; mkdir -p ~/m
                           curl -sSL -o ~/m/kokoro.onnx https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx
                           curl -sSL -o ~/m/voices.bin https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin ;;
  chatterbox)              $P chatterbox-tts soundfile ;;
  eval)                    $P torch torchaudio $CPU; $P faster-whisper soundfile librosa numpy ;;
esac
