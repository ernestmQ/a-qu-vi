#!/usr/bin/env bash
# Un vídeo: descifra el paquete, genera la voz, la convierte, renderiza y sube el resultado cifrado.
# Variables: RAMA (rama c-* con el paquete), I (índice del vídeo), K1 (clave).
set -euo pipefail
M=${M:-$HOME/m}; W=/tmp/w; mkdir -p $W
dec() { openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:K1 -in "$1"; }
enc() { openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:K1 -out "$2" -in "$1"; }
git fetch -q --depth 1 origin "$RAMA" base
git show "origin/$RAMA:p.bin" > $W/p.bin; dec $W/p.bin | tar -xz -C $W
VOZ=$(cat $W/voz.txt 2>/dev/null || echo padre)
cp -r $W/src/. src/
read -r N COMP MOD EXP < <(python3 -c "import json;e=json.load(open('$W/lista.json'))[$I];print(e['n'],e['comp'],e['mod'],e['exp'])")
V=$W/v; mkdir -p $V
if [ -f "$W/vc/$N.flac" ]; then
  # voz ya generada antes con el mismo texto: se reutiliza (solo cambian las escenas)
  F="$W/vc/$N.flac"; [ -f "$W/vc/$N.cruda.flac" ] && F="$W/vc/$N.cruda.flac"
  ffmpeg -loglevel error -y -i "$F" -ar 48000 $V/voiceover.wav
  cp "$W/vc/$N.json" $V/manifest.json; REUSO=1
elif [ "$VOZ" = padre ]; then
  git show origin/base:r.bin > $W/r.bin; dec $W/r.bin > $W/r.pt
  python scripts/voz.py "$W/g/$N.json" $V >/dev/null
  python scripts/vc.py $W/r.pt $V/crudo.wav $V/manifest.json $V/conv.wav 8 >/dev/null
else
  mkdir -p $W/rq; git show "origin/base:v-$VOZ.bin" > $W/rq.bin; dec $W/rq.bin | tar -xz -C $W/rq
  if [ -f "$W/vp/$N.flac" ]; then export AQ_PREVIA="$W/vp/$N.flac" AQ_PREVIA_MAN="$W/vp/$N.json"; fi
  python scripts/voz_qwen.py "$W/g/$N.json" $V $W/rq/ref.wav $W/rq/ref.txt
  cp $V/crudo.wav $V/conv.wav
fi
[ -n "${REUSO:-}" ] || ffmpeg -loglevel error -y -i $V/conv.wav -ar 48000 $V/voiceover.wav
if [ -z "${REUSO:-}" ]; then python scripts/qa_voz.py $V/voiceover.wav $V/manifest.json $V/qa.json || echo '{"error":"qa"}' > $V/qa.json; else echo '{"reutilizada":true}' > $V/qa.json; fi
mkdir -p public/voz/x && cp $V/voiceover.wav public/voz/x/voiceover.wav
cp $V/manifest.json src/pk/m.json
printf 'import React from "react";\nimport { %s } from "../%s";\nimport m from "./m.json";\nexport const COMPS: { id: string; component: React.FC<any>; manifest: unknown }[] = [{ id: "%s", component: %s, manifest: m }];\n' "$EXP" "$MOD" "$COMP" "$EXP" > src/pk/index.ts
python3 -c "import json;json.dump({'manifest':json.load(open('$V/manifest.json')),'audio':'voz/x/voiceover.wav','etiqueta':'portada'},open('$V/props.json','w'))"
npx remotion render "$COMP" $V/bruto.mp4 --props=$V/props.json --log=error >/dev/null
ffmpeg -loglevel error -y -i $V/bruto.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a 160k -movflags +faststart $V/final.mp4
T0=$(python3 -c "import json;print(round(json.load(open('$V/manifest.json'))['segments'][0]['start']+0.7,2))")
ffmpeg -loglevel error -y -ss $T0 -i $V/final.mp4 -frames:v 1 -vf scale=960:-1 -q:v 3 $V/poster.jpg
# voz cruda (sin normalizar) para la caché por frase; si la voz se reutilizó sin cruda, no se guarda (estaría normalizada)
if [ -f "$W/vc/$N.cruda.flac" ]; then cp "$W/vc/$N.cruda.flac" $V/voz.flac; elif [ -z "${REUSO:-}" ]; then ffmpeg -loglevel error -y -i $V/conv.wav -ar 24000 -ac 1 -c:a flac $V/voz.flac; fi
tar -czf $V/r.tgz -C $V final.mp4 poster.jpg manifest.json qa.json $( [ -f $V/voz.flac ] && echo voz.flac )
enc $V/r.tgz $V/out-$I.bin
O="o-${RAMA#c-}-$I"
B=$(git hash-object -w $V/out-$I.bin); T=$(printf '100644 blob %s\tout.bin\n' "$B" | git mktree)
C=$(git -c user.name=r -c user.email=r@r commit-tree "$T" -m o); git push -q -f origin "$C:refs/heads/$O"
echo "ok $I $(du -h $V/final.mp4 | cut -f1)"
