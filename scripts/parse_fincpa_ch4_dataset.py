#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT_DIR / "data" / "raw" / "official" / "law_fincpa_main_2026-01-02.pdf"
OUTPUT_DIR = ROOT_DIR / "data" / "parsed" / "ch4_fincpa"
PAGE_FROM = 7
PAGE_TO = 16
SOURCE_ID = "law_fincpa_main_2026-01-02"
SOURCE_TITLE = "금융소비자 보호에 관한 법률"
CHAPTER_ID = "제4장"
CHAPTER_TITLE = "금융상품판매업자등의 영업행위 준수사항"
CHAPTER_START_MARKER = f"{CHAPTER_ID} {CHAPTER_TITLE}"
CHAPTER_END_MARKER = "제5장 금융소비자 보호"
ARTICLE_RE = re.compile(r"^(제\d+조(?:의\d+)?)(\([^)]+\))\s*(.*)$")
SECTION_RE = re.compile(r"^(제\d절)\s+(.+)$")
PARAGRAPH_RE = re.compile(r"(?m)^(?P<marker>[①②③④⑤⑥⑦⑧⑨⑩])\s*")
FOOTER_RE = re.compile(r"법제처\s*\n+\d+\s*\n+국가법령정보센\s*\n*터\s*", re.MULTILINE)


@dataclass
class ArticleBlock:
    section_id: str | None
    section_title: str | None
    article_id: str
    article_title: str
    page_start: int
    body_raw: str


def run_pdftotext(pdf_path: Path, page_from: int, page_to: int) -> str:
    proc = subprocess.run(
        [
            "pdftotext",
            "-f",
            str(page_from),
            "-l",
            str(page_to),
            str(pdf_path),
            "-",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout


def clean_page_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = FOOTER_RE.sub("", text)
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.rstrip()
        if stripped == SOURCE_TITLE:
            continue
        lines.append(stripped)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_chapter_scope(page_texts: list[tuple[int, str]]) -> tuple[str, list[tuple[int, str]]]:
    combined_parts: list[str] = []
    scoped_pages: list[tuple[int, str]] = []
    in_scope = False

    for page_no, text in page_texts:
        working = text
        if not in_scope:
            start_index = working.find(CHAPTER_START_MARKER)
            if start_index == -1:
                continue
            working = working[start_index:]
            in_scope = True

        end_index = working.find(CHAPTER_END_MARKER)
        if end_index != -1:
            working = working[:end_index]
            if working.strip():
                combined_parts.append(working.strip())
                scoped_pages.append((page_no, working.strip()))
            break

        if working.strip():
            combined_parts.append(working.strip())
            scoped_pages.append((page_no, working.strip()))

    if not combined_parts:
        raise RuntimeError("Could not locate Chapter 4 scope in the selected page range.")

    return "\n\n".join(combined_parts).strip(), scoped_pages


def build_page_lookup(scoped_pages: list[tuple[int, str]]) -> list[tuple[int, str]]:
    return [(page_no, page_text) for page_no, page_text in scoped_pages]


def find_page_start(page_lookup: list[tuple[int, str]], article_id: str) -> int:
    for page_no, page_text in page_lookup:
        if article_id in page_text:
            return page_no
    return page_lookup[0][0]


def collect_article_blocks(chapter_text: str, page_lookup: list[tuple[int, str]]) -> list[ArticleBlock]:
    current_section_id: str | None = None
    current_section_title: str | None = None
    current_article_id: str | None = None
    current_article_title: str | None = None
    current_article_lines: list[str] = []
    blocks: list[ArticleBlock] = []

    def flush_article() -> None:
        nonlocal current_article_id, current_article_title, current_article_lines
        if current_article_id is None or current_article_title is None:
            return
        body_raw = "\n".join(current_article_lines).strip()
        blocks.append(
            ArticleBlock(
                section_id=current_section_id,
                section_title=current_section_title,
                article_id=current_article_id,
                article_title=current_article_title,
                page_start=find_page_start(page_lookup, current_article_id),
                body_raw=body_raw,
            )
        )
        current_article_id = None
        current_article_title = None
        current_article_lines = []

    for raw_line in chapter_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == CHAPTER_START_MARKER:
            continue

        section_match = SECTION_RE.match(line)
        if section_match:
            flush_article()
            current_section_id = section_match.group(1)
            current_section_title = section_match.group(2).strip()
            continue

        article_match = ARTICLE_RE.match(line)
        if article_match:
            flush_article()
            current_article_id = article_match.group(1)
            current_article_title = article_match.group(2).strip("()")
            first_body = article_match.group(3).strip()
            current_article_lines = [first_body] if first_body else []
            continue

        if current_article_id is not None:
            current_article_lines.append(line)

    flush_article()
    return blocks


def normalize_spaces(text: str) -> str:
    return " ".join(text.split())


def split_paragraphs(article: ArticleBlock) -> list[dict]:
    body = article.body_raw.strip()
    matches = list(PARAGRAPH_RE.finditer(body))

    if not matches:
        raw_text = body
        return [
            {
                "record_id": f"{SOURCE_ID}:{article.article_id}",
                "source_id": SOURCE_ID,
                "source_title": SOURCE_TITLE,
                "source_path": str(PDF_PATH.relative_to(ROOT_DIR)),
                "chapter_id": CHAPTER_ID,
                "chapter_title": CHAPTER_TITLE,
                "section_id": article.section_id,
                "section_title": article.section_title,
                "article_id": article.article_id,
                "article_title": article.article_title,
                "paragraph_id": None,
                "page_start": article.page_start,
                "raw_text": raw_text,
                "normalized_text": normalize_spaces(raw_text),
                "parse_method": "deterministic_pdf_text_extraction_and_regex_segmentation",
                "manual_verified": False,
            }
        ]

    records: list[dict] = []
    for index, match in enumerate(matches):
        marker = match.group("marker")
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        raw_text = body[start:end].strip()
        records.append(
            {
                "record_id": f"{SOURCE_ID}:{article.article_id}:{marker}",
                "source_id": SOURCE_ID,
                "source_title": SOURCE_TITLE,
                "source_path": str(PDF_PATH.relative_to(ROOT_DIR)),
                "chapter_id": CHAPTER_ID,
                "chapter_title": CHAPTER_TITLE,
                "section_id": article.section_id,
                "section_title": article.section_title,
                "article_id": article.article_id,
                "article_title": article.article_title,
                "paragraph_id": marker,
                "page_start": article.page_start,
                "raw_text": raw_text,
                "normalized_text": normalize_spaces(raw_text),
                "parse_method": "deterministic_pdf_text_extraction_and_regex_segmentation",
                "manual_verified": False,
            }
        )
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_report(path: Path, records: list[dict], page_lookup: list[tuple[int, str]]) -> None:
    article_order: list[str] = []
    article_counts: dict[str, int] = {}
    article_pages: dict[str, int] = {}
    for record in records:
        article_id = record["article_id"]
        if article_id not in article_counts:
            article_order.append(article_id)
            article_counts[article_id] = 0
            article_pages[article_id] = record["page_start"]
        article_counts[article_id] += 1

    lines = [
        "Chapter 4 Parsing Report",
        "========================",
        "",
        f"- source_pdf: `{PDF_PATH.relative_to(ROOT_DIR)}`",
        f"- scope: `{CHAPTER_START_MARKER}` to before `{CHAPTER_END_MARKER}`",
        f"- pdf_pages_used: `{PAGE_FROM}` to `{PAGE_TO}`",
        f"- deterministic_parser_only: `true`",
        f"- gemini_or_llm_used_for_parsing: `false`",
        f"- parsed_record_count: `{len(records)}`",
        "",
        "Articles",
        "--------",
    ]

    for article_id in article_order:
        lines.append(
            f"- `{article_id}`: page_start `{article_pages[article_id]}`, parsed_records `{article_counts[article_id]}`"
        )

    lines.extend(
        [
            "",
            "Scoped Pages",
            "------------",
        ]
    )
    for page_no, _ in page_lookup:
        lines.append(f"- `{page_no}`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_manifest(path: Path, records: list[dict], articles: list[ArticleBlock]) -> None:
    manifest = {
        "dataset_id": "law_fincpa_main_ch4_clause_dataset_v0_1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_pdf": str(PDF_PATH.relative_to(ROOT_DIR)),
        "source_id": SOURCE_ID,
        "source_title": SOURCE_TITLE,
        "scope": {
            "chapter_id": CHAPTER_ID,
            "chapter_title": CHAPTER_TITLE,
            "page_from": PAGE_FROM,
            "page_to": PAGE_TO,
            "chapter_end_marker": CHAPTER_END_MARKER,
        },
        "parsing_method": {
            "llm_used": False,
            "extraction_tool": "pdftotext",
            "segmentation_logic": [
                "chapter_start_marker",
                "chapter_end_marker",
                "section_header_regex",
                "article_header_regex",
                "paragraph_marker_regex",
            ],
        },
        "article_ids": [article.article_id for article in articles],
        "record_count": len(records),
        "output_files": {
            "chapter_text": "data/parsed/ch4_fincpa/law_fincpa_main_ch4_fulltext.txt",
            "clause_records_jsonl": "data/parsed/ch4_fincpa/law_fincpa_main_ch4_clause_records.jsonl",
            "parse_report": "data/parsed/ch4_fincpa/law_fincpa_main_ch4_parse_report.md",
            "manifest": "data/parsed/ch4_fincpa/law_fincpa_main_ch4_manifest.json",
        },
    }
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_pdf_text = run_pdftotext(PDF_PATH, PAGE_FROM, PAGE_TO)
    page_texts = []
    for index, page_text in enumerate(raw_pdf_text.split("\f")):
        page_no = PAGE_FROM + index
        if page_no > PAGE_TO:
            break
        cleaned = clean_page_text(page_text)
        if cleaned:
            page_texts.append((page_no, cleaned))

    chapter_text, scoped_pages = extract_chapter_scope(page_texts)
    page_lookup = build_page_lookup(scoped_pages)
    articles = collect_article_blocks(chapter_text, page_lookup)

    records: list[dict] = []
    for article in articles:
        records.extend(split_paragraphs(article))

    (OUTPUT_DIR / "law_fincpa_main_ch4_fulltext.txt").write_text(chapter_text + "\n", encoding="utf-8")
    write_jsonl(OUTPUT_DIR / "law_fincpa_main_ch4_clause_records.jsonl", records)
    write_report(OUTPUT_DIR / "law_fincpa_main_ch4_parse_report.md", records, page_lookup)
    write_manifest(OUTPUT_DIR / "law_fincpa_main_ch4_manifest.json", records, articles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
