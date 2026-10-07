#!/usr/bin/env bash
# marker's fast mode on CPU runs its VLM through llama.cpp's `llama-server`, which pip does not
# install. Fetch one pinned upstream CPU build and point surya at it (LLAMA_CPP_BINARY).
#   bench/install-llamacpp.sh <dest dir>   -> prints the binary path
set -euo pipefail

tag=b11457
asset=llama-$tag-bin-ubuntu-x64.tar.gz
dest=$1
mkdir -p "$dest"
curl -fsSL -o "$dest/$asset" "https://github.com/ggml-org/llama.cpp/releases/download/$tag/$asset"
sha256sum "$dest/$asset" >&2
tar -xzf "$dest/$asset" -C "$dest"
rm "$dest/$asset"
bin=$(find "$dest" -type f -name llama-server -print -quit)  # not `| head`: SIGPIPE under pipefail
"$bin" --version >&2
echo "$bin"
