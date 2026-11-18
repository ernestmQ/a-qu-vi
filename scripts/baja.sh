#!/usr/bin/env bash
# Descarga y descifra una rama de salida. Uso: baja.sh <rama> <carpeta>
set -euo pipefail
mkdir -p "$2"
git fetch -q --depth 1 origin "$1" && git show FETCH_HEAD:out.bin > /tmp/baja.bin
openssl enc -d -aes-256-cbc -pbkdf2 -iter 200000 -pass env:K1 -in /tmp/baja.bin | tar -xz -C "$2"
