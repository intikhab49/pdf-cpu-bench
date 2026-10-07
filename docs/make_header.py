"""Generate the README header SVG (self-hosted: capsule-render dies through GitHub's camo proxy).

Scores on the right are read from results/results.json, so the header cannot drift from the data.
Validates as XML before writing - a bare '&' in SVG text breaks the image on GitHub silently.

    python docs/make_header.py
"""
import json
import pathlib
import xml.dom.minidom

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1200, 340
BG = "#0A0A14"
AMBER, CORAL, PINK = "#FFB020", "#FF6B4A", "#FF4E88"
LIME, BLUE, DIM = "#A3E635", "#5B9BFF", "#8B8BA7"
MONO = "ui-monospace,SFMono-Regular,Menlo,monospace"
SANS = "-apple-system,Segoe UI,Helvetica,sans-serif"

LABELS = {"mineru-basic": "mineru (CPU tier)", "marker-fast": "marker fast", "docling": "docling",
          "marker-fast-no-ocr": "marker, no OCR", "liteparse": "liteparse",
          "liteparse-no-ocr": "liteparse, no OCR", "unstructured-hi-res": "unstructured",
          "pymupdf4llm": "pymupdf4llm", "markitdown": "markitdown"}

scores = json.loads((ROOT / "results/results.json").read_text())["scores"]
rows = sorted(((LABELS[k], v["score"]) for k, v in scores.items()), key=lambda r: -r[1])


def bars_svg(x0, y0, w, h, gap=6, axis=80.0):
    """Horizontal score bars to scale against an 80% axis; the leader gets the gradient."""
    out, bh = [], (h - gap * (len(rows) - 1)) / len(rows)
    for i, (name, v) in enumerate(rows):
        y = y0 + i * (bh + gap)
        bw = w * v / axis
        lead = i == 0
        fill, op = ("url(#grad)", "1") if lead else (DIM, "0.35")
        out.append(f'<rect x="{x0}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" '
                   f'fill="{fill}" opacity="{op}"/>')
        out.append(f'<text x="{x0 + bw + 8:.1f}" y="{y + bh / 2 + 4:.1f}" font-family="{MONO}" '
                   f'font-size="12" fill="{"#FFFFFF" if lead else DIM}" '
                   f'font-weight="{"700" if lead else "400"}">{v:.1f}  {name}</text>')
    return "\n    ".join(out)


def pill(x, w, colour, text):
    return (f'<rect x="{x}" y="262" width="{w}" height="28" rx="14" fill="none" stroke="{colour}" '
            f'stroke-opacity="0.55"/>\n    <text x="{x + w / 2:.0f}" y="281" fill="{colour}" '
            f'text-anchor="middle">{text}</text>')


best = rows[0]
SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img"
     aria-label="pdf-cpu-bench: 9 PDF-to-Markdown parsers measured on a plain 4-core CPU with
     olmocr-bench. Best score {best[1]:.1f} percent, {best[0]}.">
  <defs>
    <linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="{AMBER}"/>
      <stop offset="55%" stop-color="{CORAL}"/>
      <stop offset="100%" stop-color="{PINK}"/>
    </linearGradient>
    <linearGradient id="fade" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{CORAL}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{BG}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse">
      <path d="M28 0 L0 0 0 28" fill="none" stroke="#FFFFFF" stroke-opacity="0.04" stroke-width="1"/>
    </pattern>
  </defs>

  <rect width="{W}" height="{H}" fill="{BG}"/>
  <rect width="{W}" height="{H}" fill="url(#grid)"/>
  <circle cx="{W - 160}" cy="70" r="240" fill="url(#fade)"/>

  <text x="64" y="86" font-family="{MONO}" font-size="13" letter-spacing="3.5" fill="{LIME}">OLMOCR-BENCH
        &#183; 1,403 PDFS &#183; ONE 4-CORE CPU</text>

  <text x="60" y="164" font-family="Georgia,'Times New Roman',serif" font-size="64"
        font-weight="700" fill="url(#grad)">pdf-cpu-bench</text>

  <text x="64" y="204" font-family="{SANS}" font-size="19" fill="#E8E8F0">9 PDF-to-Markdown parsers
        for RAG, on a plain CPU.</text>
  <text x="64" y="232" font-family="{SANS}" font-size="19" fill="{DIM}">Score, seconds per page, RAM
        and install size. Same machine, same pages.</text>

  <g font-family="{MONO}" font-size="12">
    {pill(64, 112, AMBER, "9 PARSERS")}
    {pill(188, 120, LIME, "1,403 PDFS")}
    {pill(320, 150, BLUE, "4 CORES &#183; 16 GB")}
    {pill(482, 164, PINK, "OFFICIAL CHECKER")}
  </g>

  <text x="790" y="62" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{DIM}">SCORE % &#183;
        8,413 tests</text>
  <g>
    {bars_svg(790, 78, 190, 236)}
  </g>
</svg>
"""

if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / "header.svg"
    xml.dom.minidom.parseString(SVG)
    out.write_text(SVG, encoding="utf-8")
    print(f"wrote {out} ({len(SVG)} bytes, valid XML)")
