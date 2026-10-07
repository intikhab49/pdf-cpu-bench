## Quality run (full set, sharded)

| Candidate | Pages | Errors | Timeouts | Runner CPUs |
|---|---:|---:|---:|---|
| docling | 1403 | 0 | 0 | AMD EPYC 9V45 96-Core Processor; INTEL(R) XEON(R) PLATINUM 8573C; Intel(R) Xeon(R) 6973P-C |
| liteparse | 1403 | 0 | 0 | AMD EPYC 7763 64-Core Processor |
| liteparse-no-ocr | 1403 | 0 | 0 | Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz |
| marker-fast | 1403 | 0 | 130 | AMD EPYC 7763 64-Core Processor; AMD EPYC 9V45 96-Core Processor; AMD EPYC 9V74 80-Core Processor |
| marker-fast-no-ocr | 1403 | 0 | 0 | AMD EPYC 7763 64-Core Processor |
| markitdown | 1403 | 7 | 0 | Intel(R) Xeon(R) Platinum 8370C CPU @ 2.80GHz |
| mineru-basic | 1403 | 0 | 0 | AMD EPYC 7763 64-Core Processor; AMD EPYC 9V45 96-Core Processor; INTEL(R) XEON(R) PLATINUM 8573C |
| pymupdf4llm | 1403 | 0 | 0 | AMD EPYC 9V45 96-Core Processor |
| unstructured-hi-res | 1403 | 0 | 0 | AMD EPYC 7763 64-Core Processor; AMD EPYC 9V74 80-Core Processor; INTEL(R) XEON(R) PLATINUM 8573C |

## Speed, memory and size (one runner, same pages)

Runner: AMD EPYC 7763 64-Core Processor x4, 15.6 GB

| Candidate | Pages | Failed | Median s/page | Pages/s (1 stream) | Load s | Peak RAM MB | Install MB | Model downloads MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| docling | 70 | 0 | 4.281 | 0.14 | 5.29 | 4767 | 6303 | 506 |
| liteparse | 70 | 0 | 0.61 | 0.74 | 0.02 | 372 | 47 | 15 |
| liteparse-no-ocr | 70 | 0 | 0.007 | 149.09 | 0.02 | 65 | 47 | 1 |
| marker-fast | 70 | 14 | 24.161 | 0.01 | 7.34 | 12624 | 6204 | 1667 |
| marker-fast-no-ocr | 70 | 0 | 0.649 | 1.08 | 7.89 | 2432 | 6160 | 136 |
| markitdown | 70 | 0 | 0.183 | 4.88 | 0.36 | 129 | 251 | 1 |
| mineru-basic | 70 | 0 | 6.17 | 0.14 | 0.38 | 4678 | 1003 | 820 |
| pymupdf4llm | 70 | 0 | 0.846 | 0.57 | 0.59 | 422 | 292 | 2 |
| unstructured-hi-res | 70 | 0 | 7.471 | 0.12 | 4.75 | 4616 | 6856 | 318 |

## olmocr-bench score (official checker, macro-average of categories)

| Candidate | Score | ±95% | arxiv_math | old_scans_math | table_tests | old_scans | headers_footers | multi_column | long_tiny_text | baseline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mineru-basic | 74.6 | 1.0 | 76.9 | 63.1 | 72.7 | 27.4 | 96.2 | 76.9 | 86.4 | 97.6 |
| marker-fast | 58.3 | 1.1 | 20.2 | 66.6 | 61.0 | 31.7 | 93.9 | 59.6 | 43.0 | 90.7 |
| docling | 53.4 | 0.9 | 0.0 | 0.0 | 70.9 | 25.1 | 89.7 | 73.8 | 68.6 | 99.1 |
| marker-fast-no-ocr | 43.7 | 0.9 | 0.0 | 0.0 | 45.5 | 13.3 | 95.4 | 67.1 | 40.5 | 88.1 |
| liteparse | 40.6 | 1.0 | 0.0 | 0.0 | 56.3 | 13.9 | 51.2 | 65.8 | 37.3 | 99.9 |
| liteparse-no-ocr | 39.1 | 0.9 | 0.0 | 0.0 | 54.8 | 13.3 | 55.7 | 65.5 | 23.8 | 99.9 |
| unstructured-hi-res | 38.0 | 1.0 | 0.0 | 0.0 | 41.5 | 20.7 | 28.2 | 55.3 | 60.6 | 97.8 |
| pymupdf4llm | 37.5 | 1.0 | 0.0 | 0.0 | 61.2 | 13.3 | 38.0 | 66.6 | 33.7 | 87.2 |
| markitdown | 29.3 | 0.9 | 0.0 | 0.0 | 25.0 | 13.3 | 38.8 | 39.3 | 31.2 | 86.8 |
