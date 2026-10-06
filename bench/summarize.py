"""Join the olmocr-bench scores, the quality run's failures and the one-runner speed table.

Speed, RAM and size come only from the speed job (every candidate on the same runner);
the sharded quality run lands on mixed CPU models, so its timings are not compared.
"""

import argparse
import collections
import json
import pathlib
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

    score_path = out / "olmocr-bench-score.txt"
    score_text = score_path.read_text() if score_path.exists() else "(no score output)"
    tail = score_text[score_text.find("Final Summary"):] if "Final Summary" in score_text else score_text[-6000:]
    report += ["", "## olmocr-bench (official checker output)", "", "```", tail.strip(), "```"]

    (out / "results.md").write_text("\n".join(report) + "\n")
    (out / "results.json").write_text(json.dumps(results, indent=2))
    print("\n".join(report))


if __name__ == "__main__":
    main()
