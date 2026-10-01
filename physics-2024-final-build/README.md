# Physics 2024 final Tilda build

Builds the interactive Physics 2024 v1.1 demo exclusively from the canonical FIPI 2024 PDF plus the reviewed 2024 scorer/layout evidence. Production task wording is rendered as exact source-page raster regions so `pdftotext` extraction artifacts cannot enter the Tilda content.

The v1.1 shell follows the frozen Physics technical reference for navigation, typography, task cards, timer, calculator, symbol keyboard, state restoration, finish flow and responsive behavior. No cross-year content is copied. Result DOM order is: Result, short-answer review 1-20, self-assessment 21-26, Sources.

The Tilda packer uses tightly packed, independently closed T123 scripts and enforces both the 42,500-byte per-block limit and a maximum of 48 ordered blocks. The verifier covers all five responsive widths, scorer rules, full and partial finish, state/result reload, storage isolation, calculator, symbol keyboard, focus return, source-image decode, bounded task 25/26 criteria regions, clean extraction and deterministic hashes.
