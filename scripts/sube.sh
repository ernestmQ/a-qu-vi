#!/usr/bin/env bash
# Cifra una carpeta y la sube como rama de salida. Uso: sube.sh <carpeta> <rama>
set -euo pipefail
tar -czf /tmp/sube.tgz -C "$1" .
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt -pass env:K1 -in /tmp/sube.tgz -out /tmp/out.bin
cd "$GITHUB_WORKSPACE"
B=$(git hash-object -w /tmp/out.bin); T=$(printf '100644 blob %s\tout.bin\n' "$B" | git mktree)
C=$(git -c user.name=r -c user.email=r@r commit-tree "$T" -m o); git push -q -f origin "$C:refs/heads/$2"
