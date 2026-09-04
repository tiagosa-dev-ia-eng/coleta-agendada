#!/usr/bin/env bash
# Incrementa a versão interna do projeto (VERSION). Uso: bump-version.sh [patch|minor|major]
# REGRA GERAL: rode a cada mudança e envie VERSION/CHANGELOG ao GitHub.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILE="$ROOT/VERSION"
mode="${1:-patch}"

case "$mode" in
  major|minor|patch) ;;
  *) echo "Uso: $0 [patch|minor|major]" >&2; exit 2 ;;
esac

current="$(cat "$FILE")"
IFS='.' read -r maj min pat <<< "$current"
case "$mode" in
  major) maj=$((maj + 1)); min=0; pat=0 ;;
  minor) min=$((min + 1)); pat=0 ;;
  *)     pat=$((pat + 1)) ;;
esac
next="$maj.$min.$pat"
echo "versão: $current -> $next"
echo "$next" > "$FILE"
