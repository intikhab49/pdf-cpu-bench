"""Put every candidate's markdown next to olmOCR-bench's pdfs/ so the official checker finds it.

On a partial run (--limit) the PDFs nobody converted, and the tests on them, are removed first,
so the score covers exactly the converted pages. A page some other candidate converted but this
one did not (its job died or timed out) gets an empty file, so it scores as a failure.
"""

import argparse
import json
import pathlib
import shutil


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    data, out = pathlib.Path(args.data), pathlib.Path(args.out)

    candidates = [d for d in out.iterdir() if d.is_dir()]
    done = {}
    for cand in candidates:
        done[cand.name] = {md.relative_to(cand).as_posix() for md in cand.rglob("*.md")}
        shutil.copytree(cand, data / cand.name, dirs_exist_ok=True)

    all_md = set().union(*done.values()) if done else set()
    for name, mds in done.items():
        missing = all_md - mds
        for rel in missing:
            (data / name / rel).parent.mkdir(parents=True, exist_ok=True)
            (data / name / rel).write_text("")
        print(f"{name}: {len(mds)} pages, {len(missing)} missing (scored as failures)")

    converted = {md.rsplit("_pg", 1)[0] + ".pdf" for md in all_md}
    pdf_root = data / "pdfs"
    every = {p.relative_to(pdf_root).as_posix() for p in pdf_root.rglob("*.pdf")}
    if converted == every:
        print(f"{len(candidates)} candidates, all {len(every)} PDFs")
        return

    for rel in every - converted:
        (pdf_root / rel).unlink()
    kept = 0
    for jsonl in data.glob("*.jsonl"):
        tests = [line for line in jsonl.read_text(encoding="utf-8").splitlines()
                 if line.strip() and json.loads(line)["pdf"] in converted]
        jsonl.write_text("\n".join(tests) + ("\n" if tests else ""), encoding="utf-8")
        kept += len(tests)
    print(f"{len(candidates)} candidates, partial run: {len(converted)} of {len(every)} PDFs, {kept} tests")


if __name__ == "__main__":
    main()
