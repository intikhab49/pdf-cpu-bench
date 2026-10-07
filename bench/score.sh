#!/usr/bin/env bash
# Score each candidate in its own olmocr-bench process, so one crash cannot hide the others'
# results, and fail the step if any candidate could not be scored.
# Math-heavy outputs are slow to check (every formula is rendered with KaTeX in a browser):
# MinerU takes 20+ minutes on its own, so do not mistake that for a hang.
#   bench/score.sh <bench_data dir> <out dir> [only,these,candidates]
set -uo pipefail

data=$1 out=$2 only=${3:-}
failed=()
for cand in $(find "$out" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort); do
  if [ -n "$only" ] && [[ ",$only," != *",$cand,"* ]]; then continue; fi
  echo "::group::score $cand"
  PYTHONUNBUFFERED=1 python -X faulthandler -m olmocr.bench.benchmark --dir "$data" --candidate "$cand" \
    > "$out/score-$cand.txt" 2>&1
  status=$?
  grep -E 'Average Score|^\s+\S+\.jsonl\s+:|^\s+baseline\s+:' "$out/score-$cand.txt" || true
  if [ $status -ne 0 ] || ! grep -q 'Average Score' "$out/score-$cand.txt"; then
    echo "::error::olmocr-bench failed for $cand (exit $status); last lines:"
    grep -v '\[FAIL\]' "$out/score-$cand.txt" | tail -n 40
    failed+=("$cand")
  fi
  echo "::endgroup::"
done
if [ ${#failed[@]} -gt 0 ]; then
  echo "::error::not scored: ${failed[*]}"
  exit 1
fi
