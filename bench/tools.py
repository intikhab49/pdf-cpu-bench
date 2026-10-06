"""One adapter per parser. Each takes a mode and returns convert(pdf_path) -> markdown.

Everything is the tool's documented default unless the mode says otherwise, so the numbers
show what a user gets from `pip install` and the README example.
"""

import pathlib
import subprocess
import tempfile


def markitdown(mode):
    from markitdown import MarkItDown

    md = MarkItDown()
    return lambda path: md.convert(path).text_content


def pymupdf4llm(mode):
    import pymupdf4llm as p4l

    return lambda path: p4l.to_markdown(path)


def liteparse(mode):
    from liteparse import LiteParse

    parser = LiteParse(output_format="markdown", ocr_enabled=mode != "no-ocr")
    return lambda path: parser.parse(path).text


def marker(mode):
    from marker.config.parser import ConfigParser
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.output import text_from_rendered

    # fast is marker's own default on CPU; fast-no-ocr is its "CPU-only / no VLM" recipe
    config = {"mode": "fast", "disable_tqdm": True}
    if mode == "fast-no-ocr":
        config["disable_ocr"] = True
    parser = ConfigParser(config)
    converter = PdfConverter(
        config=parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
        processor_list=parser.get_processors(),
        renderer=parser.get_renderer(),
        llm_service=parser.get_llm_service(),
    )

    def convert(path):
        text, _, _ = text_from_rendered(converter(path))
        return text

    return convert


def docling(mode):
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    return lambda path: converter.convert(path).document.export_to_markdown()


def mineru(mode):
    # MinerU 4's stateless CLI; tier "basic" is its ONNX, CPU-capable tier
    tier = mode if mode != "default" else "basic"

    def convert(path):
        with tempfile.TemporaryDirectory() as tmp:
            out = pathlib.Path(tmp) / "out.md"
            subprocess.run(
                ["mineru-kit", "parse", path, "-o", str(out), "--tier", tier],
                check=True,
                capture_output=True,
                text=True,
            )
            return out.read_text(encoding="utf-8")

    return convert


def unstructured(mode):
    from unstructured.partition.pdf import partition_pdf

    def convert(path):
        elements = partition_pdf(filename=path, strategy="hi_res", infer_table_structure=True)
        parts = []
        for el in elements:
            html = getattr(el.metadata, "text_as_html", None)
            if el.category == "Table" and html:
                parts.append(html)
            elif el.category == "Title":
                parts.append("# " + el.text)
            else:
                parts.append(el.text)
        return "\n\n".join(parts)

    return convert
