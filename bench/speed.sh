#!/usr/bin/env bash
# Speed, memory and size for every candidate on ONE runner, so the CPU is the same for all.
# GitHub hands out different CPU models per job, so timings from the sharded quality run are
# not comparable across tools; these are.
#
# Per candidate: fresh venv -> default install (size measured) -> warm-up pass on 1 PDF per
# category (model downloads land here, not in the timing) -> timed pass on $SPEED_LIMIT PDFs
# per category -> delete the venv and model cache before the next one.
#
#   bench/speed.sh <bench_data dir> <out dir> [only,names]
set -euo pipefail

data=$1 out=$2 only=${3:-}
limit=${SPEED_LIMIT:-10}
here=$(cd "$(dirname "$0")" && pwd)
mkdir -p "$out"

python3 -c "
import json, sys
only = {s for s in sys.argv[1].split(',') if s}
for c in json.load(open('$here/candidates.json')):
    if not only or c['name'] in only:
        print(c['name'], c['tool'], c['mode'], c['pip'], sep='\t')
" "$only" | while IFS=$'\t' read -r name tool mode pip; do
  echo "::group::$name ($pip)"
  venv=$RUNNER_TEMP/speed-venv
  cache=$RUNNER_TEMP/speed-cache
  rm -rf "$venv" "$cache"
  mkdir -p "$cache"
  export XDG_CACHE_HOME=$cache HF_HOME=$cache/huggingface TORCH_HOME=$cache/torch

  python -m venv "$venv"
  "$venv/bin/pip" install --quiet --upgrade pip
  if ! "$venv/bin/pip" install --quiet "$pip"; then
    echo "{\"name\": \"$name\", \"install_failed\": true}" > "$out/$name.shard0.env.json"
    echo "::endgroup::"
    continue
  fi
  install_mb=$(du -sm "$venv" | cut -f1)
  "$venv/bin/pip" install --quiet psutil pypdf
  "$venv/bin/pip" freeze > "$out/$name.shard0.freeze.txt"
  home_before=$(du -sm --exclude=work "$HOME" | cut -f1)

  "$venv/bin/python" "$here/run.py" --tool "$tool" --mode "$mode" --name "$name" \
    --data "$data" --out "$RUNNER_TEMP/warmup" --limit 1 > /dev/null || true
  "$venv/bin/python" "$here/run.py" --tool "$tool" --mode "$mode" --name "$name" \
    --data "$data" --out "$out" --limit "$limit" || true

  home_after=$(du -sm --exclude=work "$HOME" | cut -f1)
  python3 - "$out/$name.shard0.env.json" <<EOF
import json, os, re, sys
json.dump({
    "name": "$name", "pip": "$pip", "install_mb": $install_mb,
    "downloads_mb": int(os.popen("du -sm '$cache' | cut -f1").read()) + ($home_after - $home_before),
    "cpu": re.search(r"model name\s*:\s*(.*)", open("/proc/cpuinfo").read()).group(1),
    "nproc": os.cpu_count(),
    "mem_gb": round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 2**30, 1),
}, open(sys.argv[1], "w"), indent=2)
EOF
  rm -rf "$venv" "$cache" "$RUNNER_TEMP/warmup" "$out/$name"
  "$(command -v pip)" cache purge > /dev/null 2>&1 || true
  echo "::endgroup::"
done
