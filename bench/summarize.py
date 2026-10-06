"""Join per-page timings, memory, install size and the olmocr-bench scores into one table."""

import argparse
import collections
import json
import pathlib
import statistics


def load(out, pattern):
    rows = collections.defaultdict(list)
    for path in sorted(out.glob(pattern)):
        name = path.name.split(".shard")[0]
        if path.suffix == ".jsonl":
            rows[name] += [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        else:
            rows[name].append(json.loads(path.read_text()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out)

    pages, summaries, envs = load(out, "*.pages.jsonl"), load(out, "*.summary.json"), load(out, "*.env.json")
    score_text = (out / "olmocr-bench-score.txt").read_text() if (out / "olmocr-bench-score.txt").exists() else ""

    lines = ["| Candidate | Pages | Failed | Median s/page | Pages/s (1 stream) | Load s | Peak RAM MB | Install MB | Model downloads MB |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    results = {}
    for name in sorted(pages):
        p = pages[name]
        ok = [r["seconds"] for r in p if r["status"] == "ok"]
        secs = [r["seconds"] for r in p]
        s, e = summaries.get(name, []), envs.get(name, [])
        row = {
            "pages": len(p),
            "failed": sum(r["status"] != "ok" for r in p),
            "median_s": round(statistics.median(ok), 3) if ok else None,
            "pages_per_s": round(len(p) / sum(secs), 2) if secs and sum(secs) else None,
            "load_s": max((x["load_seconds"] for x in s), default=None),
            "peak_rss_mb": max((x["peak_rss_mb"] for x in s), default=None),
            "install_mb": max((x["install_mb"] for x in e), default=None),
            "downloads_mb": max((x["downloads_mb"] for x in e), default=None),
            "cpu": e[0]["cpu"] if e else None,
            "nproc": e[0]["nproc"] if e else None,
        }
        results[name] = row
        lines.append("| {} | {pages} | {failed} | {median_s} | {pages_per_s} | {load_s} | {peak_rss_mb} | {install_mb} | {downloads_mb} |".format(name, **row))

    cpus = {(r["cpu"], r["nproc"]) for r in results.values() if r["cpu"]}
    report = ["## Speed, memory and size", "", f"Runners: {', '.join(f'{c} x{n}' for c, n in sorted(cpus))}", "", *lines]
    tail = score_text[score_text.find("Final Summary"):] if "Final Summary" in score_text else score_text[-6000:]
    report += ["", "## olmocr-bench (official checker output)", "", "```", tail.strip(), "```"]
    (out / "results.md").write_text("\n".join(report) + "\n")
    (out / "results.json").write_text(json.dumps(results, indent=2))
    print("\n".join(report))


if __name__ == "__main__":
    main()
