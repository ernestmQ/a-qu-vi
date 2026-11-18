#!/usr/bin/env bash
# Un vídeo: descifra el paquete, genera la voz, la convierte, renderiza y sube el resultado cifrado.
# Variables: TAG (etiqueta del paquete), I (índice del vídeo), K1 (clave), GH_TOKEN, GITHUB_REPOSITORY.
set -euo pipefail
M=${M:-$HOME/m}; W=/tmp/w; mkdir -p $W
dec() { openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:K1 -in "$1"; }
enc() { openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:K1 -out "$2" -in "$1"; }
gh release download "$TAG" -R "$GITHUB_REPOSITORY" -p p.bin -D $W --clobber
gh release download base -R "$GITHUB_REPOSITORY" -p r.bin -D $W --clobber
dec $W/p.bin | tar -xz -C $W; dec $W/r.bin > $W/r.pt
cp -r $W/src/. src/
read -r N COMP MOD EXP < <(python3 -c "import json;e=json.load(open('$W/lista.json'))[$I];print(e['n'],e['comp'],e['mod'],e['exp'])")
V=$W/v; mkdir -p $V
python scripts/voz.py "$W/g/$N.json" $V >/dev/null
python scripts/vc.py $W/r.pt $V/crudo.wav $V/manifest.json $V/conv.wav 8 >/dev/null
ffmpeg -loglevel error -y -i $V/conv.wav -ar 48000 $V/voiceover.wav
mkdir -p public/voz/x && cp $V/voiceover.wav public/voz/x/voiceover.wav
cp $V/manifest.json src/pk/m.json
printf 'import React from "react";\nimport { %s } from "../%s";\nimport m from "./m.json";\nexport const COMPS: { id: string; component: React.FC<any>; manifest: unknown }[] = [{ id: "%s", component: %s, manifest: m }];\n' "$EXP" "$MOD" "$COMP" "$EXP" > src/pk/index.ts
python3 -c "import json;json.dump({'manifest':json.load(open('$V/manifest.json')),'audio':'voz/x/voiceover.wav','etiqueta':'portada'},open('$V/props.json','w'))"
npx remotion render "$COMP" $V/bruto.mp4 --props=$V/props.json --log=error >/dev/null
ffmpeg -loglevel error -y -i $V/bruto.mp4 -c:v copy -af loudnorm=I=-16:TP=-1.5:LRA=11 -ar 48000 -c:a aac -b:a 160k -movflags +faststart $V/final.mp4
T0=$(python3 -c "import json;print(round(json.load(open('$V/manifest.json'))['segments'][0]['start']+0.7,2))")
ffmpeg -loglevel error -y -ss $T0 -i $V/final.mp4 -frames:v 1 -vf scale=960:-1 -q:v 3 $V/poster.jpg
tar -cz -C $V final.mp4 poster.jpg manifest.json -f $V/r.tgz
enc $V/r.tgz $V/out-$I.bin
gh release upload "$TAG" $V/out-$I.bin -R "$GITHUB_REPOSITORY" --clobber
echo "ok $I $(du -h $V/final.mp4 | cut -f1)"
