"""Join the olmocr-bench scores, the quality run's failures and the one-runner speed table.

Speed, RAM and size come only from the speed job (every candidate on the same runner);
the sharded quality run lands on mixed CPU models, so its timings are not compared.
"""

import argparse
import collections
import json
import pathlib
import re
import statistics


def load(folder, pattern):
    rows = collections.defaultdict(list)
    for path in sorted(folder.glob(pattern)):
        name = path.name.split(".shard")[0]
        if path.suffix == ".jsonl":
            rows[name] += [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        else:
            rows[name].append(json.loads(path.read_text()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--speed", required=True)
    args = ap.parse_args()
    out, speed = pathlib.Path(args.out), pathlib.Path(args.speed)
    report, results = [], {"quality_run": {}, "speed": {}}

    # quality run: did every page convert?
    q_pages, q_envs = load(out, "*.pages.jsonl"), load(out, "*.env.json")
    report += ["## Quality run (full set, sharded)", "",
               "| Candidate | Pages | Errors | Timeouts | Runner CPUs |", "|---|---:|---:|---:|---|"]
    for name in sorted(q_pages):
        p = q_pages[name]
        row = {"pages": len(p),
               "errors": sum(r["status"].startswith("error") for r in p),
               "timeouts": sum(r["status"] == "timeout" for r in p),
               "cpus": sorted({e["cpu"] for e in q_envs.get(name, [])})}
        results["quality_run"][name] = row
        report.append(f"| {name} | {row['pages']} | {row['errors']} | {row['timeouts']} | {'; '.join(row['cpus'])} |")

    # speed run: one runner, same pages for everyone
    s_pages, s_sum, s_env = load(speed, "*.pages.jsonl"), load(speed, "*.summary.json"), load(speed, "*.env.json")
    cpus = sorted({f"{e['cpu']} x{e['nproc']}, {e['mem_gb']} GB" for es in s_env.values() for e in es if "cpu" in e})
    report += ["", "## Speed, memory and size (one runner, same pages)", "", f"Runner: {'; '.join(cpus) or 'n/a'}", "",
               "| Candidate | Pages | Failed | Median s/page | Pages/s (1 stream) | Load s | Peak RAM MB | Install MB | Model downloads MB |",
               "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name in sorted(set(s_pages) | set(s_env)):
        p, s, e = s_pages.get(name, []), s_sum.get(name, [{}])[0], s_env.get(name, [{}])[0]
        if e.get("install_failed"):
            report.append(f"| {name} | install failed | | | | | | | |")
            continue
        ok = [r["seconds"] for r in p if r["status"] == "ok"]
        total = sum(r["seconds"] for r in p)
        row = {"pages": len(p), "failed": sum(r["status"] != "ok" for r in p),
               "median_s": round(statistics.median(ok), 3) if ok else None,
               "pages_per_s": round(len(p) / total, 2) if total else None,
               "load_s": s.get("load_seconds"), "peak_rss_mb": s.get("peak_rss_mb"),
               "install_mb": e.get("install_mb"), "downloads_mb": e.get("downloads_mb")}
        results["speed"][name] = row
        report.append("| {} | {pages} | {failed} | {median_s} | {pages_per_s} | {load_s} | {peak_rss_mb} | {install_mb} | {downloads_mb} |".format(name, **row))

    # olmocr-bench scores, one file per candidate from bench/score.sh
    scores = {}
    for path in sorted(out.glob("score-*.txt")):
        name = path.stem.removeprefix("score-")
        text = path.read_text(errors="replace")
        # the "x% ± y%" summary line, not the "x% (95% CI: ...)" one above it
        m = re.search(r"Average Score:\s*([\d.]+)%[^\d(]+([\d.]+)%", text)
        cats = dict(re.findall(r"^\s+(\w+?)(?:\.jsonl)?\s+:\s+([\d.]+)% \(", text, re.M))
        scores[name] = {"score": float(m.group(1)) if m else None, "ci95": float(m.group(2)) if m else None,
                        "categories": {k: float(v) for k, v in cats.items()}}
    results["scores"] = scores
    cat_names = ["arxiv_math", "old_scans_math", "table_tests", "old_scans", "headers_footers",
                 "multi_column", "long_tiny_text", "baseline"]
    report += ["", "## olmocr-bench score (official checker, macro-average of categories)", "",
               "| Candidate | Score | ±95% | " + " | ".join(cat_names) + " |",
               "|---|---:|---:|" + "---:|" * len(cat_names)]
    for name, s in sorted(scores.items(), key=lambda kv: -(kv[1]["score"] or -1)):
        cells = [f"{s['categories'].get(c, float('nan')):.1f}" for c in cat_names]
        score = "not scored" if s["score"] is None else f"{s['score']:.1f}"
        ci = "" if s["ci95"] is None else f"{s['ci95']:.1f}"
        report.append(f"| {name} | {score} | {ci} | " + " | ".join(cells) + " |")

    (out / "results.md").write_text("\n".join(report) + "\n")
    (out / "results.json").write_text(json.dumps(results, indent=2))
    print("\n".join(report))


if __name__ == "__main__":
    main()
