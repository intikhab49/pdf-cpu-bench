"""Convert olmOCR-bench pages with one parser, one page at a time, logging time and memory.

Output follows the olmocr-bench layout: <out>/<name>/<category>/<pdf>_pg<N>_repeat1.md.
A failed or timed-out page is written as an empty file, so it scores as a failure, not a skip.
"""

import argparse
import json
import os
import pathlib
import signal
import sys
import tempfile
import threading
import time

import psutil
from pypdf import PdfReader, PdfWriter

sys.path.insert(0, os.path.dirname(__file__))
import tools  # noqa: E402


class PageTimeout(Exception):
    pass


def _on_alarm(signum, frame):
    raise PageTimeout()


class TreeMemory:
    """Samples the RSS of this process plus all its children (inference servers, worker pools)."""

    def __init__(self, interval=0.1):
        self.peak = 0
        self._stop = threading.Event()
        self._interval = interval
        self._me = psutil.Process()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _sample(self):
        total = 0
        for proc in [self._me] + self._me.children(recursive=True):
            try:
                total += proc.memory_info().rss
            except psutil.Error:
                pass
        self.peak = max(self.peak, total)

    def _run(self):
        while not self._stop.is_set():
            self._sample()
            self._stop.wait(self._interval)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()
        self._sample()


def select_pdfs(pdf_root, limit, shard, shards):
    pdfs = sorted(pdf_root.rglob("*.pdf"))
    if limit:
        by_category = {}
        for pdf in pdfs:
            by_category.setdefault(pdf.relative_to(pdf_root).parts[0], []).append(pdf)
        pdfs = [p for group in by_category.values() for p in group[:limit]]
    return pdfs[shard::shards]


def single_page(pdf, page, tmpdir):
    writer = PdfWriter()
    writer.add_page(PdfReader(pdf).pages[page - 1])
    path = pathlib.Path(tmpdir) / f"{pdf.stem}_pg{page}.pdf"
    with open(path, "wb") as f:
        writer.write(f)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tool", required=True)
    ap.add_argument("--mode", default="default")
    ap.add_argument("--name", required=True, help="candidate folder name")
    ap.add_argument("--data", required=True, help="olmOCR-bench bench_data dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--shards", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0, help="PDFs per category, 0 = all")
    ap.add_argument("--timeout", type=int, default=300, help="seconds per page")
    args = ap.parse_args()

    pdf_root = pathlib.Path(args.data) / "pdfs"
    out_root = pathlib.Path(args.out)
    cand_dir = out_root / args.name
    pdfs = select_pdfs(pdf_root, args.limit, args.shard, args.shards)
    signal.signal(signal.SIGALRM, _on_alarm)

    with TreeMemory() as mem, tempfile.TemporaryDirectory() as tmp, open(
        out_root / f"{args.name}.shard{args.shard}.pages.jsonl", "w"
    ) as log:
        start = time.perf_counter()
        convert = getattr(tools, args.tool)(args.mode)
        load_seconds = time.perf_counter() - start
        load_peak = mem.peak

        for pdf in pdfs:
            rel = pdf.relative_to(pdf_root).with_suffix("")
            pages = len(PdfReader(pdf).pages)
            for page in range(1, pages + 1):
                src = pdf if pages == 1 else single_page(pdf, page, tmp)
                status, text = "ok", ""
                t0 = time.perf_counter()
                signal.alarm(args.timeout)
                try:
                    text = convert(str(src)) or ""
                except PageTimeout:
                    status = "timeout"
                except Exception as e:  # noqa: BLE001 - every failure is recorded, none stops the run
                    status = f"error: {type(e).__name__}: {str(e)[:300]}"
                finally:
                    signal.alarm(0)
                seconds = time.perf_counter() - t0
                dest = cand_dir / f"{rel}_pg{page}_repeat1.md"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(text, encoding="utf-8")
                log.write(json.dumps({"pdf": str(rel), "page": page, "seconds": round(seconds, 4),
                                      "status": status, "chars": len(text)}) + "\n")
                log.flush()

    summary = {
        "name": args.name, "tool": args.tool, "mode": args.mode, "shard": args.shard,
        "shards": args.shards, "load_seconds": round(load_seconds, 2),
        "load_peak_rss_mb": round(load_peak / 2**20), "peak_rss_mb": round(mem.peak / 2**20),
    }
    (out_root / f"{args.name}.shard{args.shard}.summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
