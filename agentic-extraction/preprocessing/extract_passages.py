"""
Extract paragraph-level passages from paper PDFs with GROBID.

Command-line usage:
- From `code-repo/` for a single PDF:
  `python agentic-extraction/preprocessing/extract_passages.py --pdf agentic-extraction/data/papers/ConceptViz.pdf`
- Batch mode:
  `python agentic-extraction/preprocessing/extract_passages.py --all`

Expected input:
- `../data/papers/*.pdf`

Output:
- `../data/passages/<paper>_passages.json`

Configuration:
- Required: a running GROBID service
- Optional: `--grobid-url` if your service is not at the default local endpoint

Before running this script:
1. Open Docker Desktop.
2. Start GROBID, for example:
   `docker run --rm -it -p 8070:8070 lfoppiano/grobid:0.7.3`

Open-source notes:
- This script uses only relative path examples in documentation.
- The abstract extraction helper is embedded directly in this file.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Iterable, Literal, Optional

import fitz
import requests
from lxml import etree
from pydantic import BaseModel, Field


DEFAULT_GROBID_URL = "http://localhost:8070/api/processFulltextDocument"
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

SCRIPT_DIR = Path(__file__).resolve().parent
AGENTIC_EXTRACTION_ROOT = SCRIPT_DIR.parent
DATA_ROOT = AGENTIC_EXTRACTION_ROOT / "data"
PASSAGES_DIR = DATA_ROOT / "passages"
PAPERS_DIR = DATA_ROOT / "papers"
DEFAULT_PASSAGES_DIR_LABEL = Path("../data/passages")
DEFAULT_PAPERS_DIR_LABEL = Path("../data/papers")

_DASH_CHARS = {
    "\u2010",
    "\u2011",
    "\u2012",
    "\u2013",
    "\u2014",
    "\u2015",
    "\u2212",
    "\u00ad",
}
_ZERO_WIDTH = {
    "\u200b",
    "\u200c",
    "\u200d",
    "\ufeff",
}

ABSTRACT_START_PATTERNS = [
    r"\babstract\b",
    r"^abstract\b",
]

ABSTRACT_END_PATTERNS = [
    r"\bkeywords?\b",
    r"\bkey\s*words?\b",
    r"\bindex\b",
    r"\bindex\s*terms?\b",
    r"\bindexing\s*terms?\b",
    r"\bintroduction\b",
    r"\bbackground\b",
    r"\brelated\s+work\b",
    r"^\s*1\s*[\.\)]\s*",
    r"^\s*i\s*[\.\)]\s*",
    r"^\s*section\s+1\b",
    r"^\s*chapter\s+1\b",
]


class Passage(BaseModel):
    text: str
    passage_type: Literal["paragraph", "caption", "title"] = "paragraph"
    order_index: int = Field(..., description="Reading order index in the final output")


def normalize_text(s: Optional[str]) -> str:
    if not s:
        return ""
    return " ".join(s.split()).strip()


def extract_text_from_first_pages(pdf_path: str, max_pages: int = 4) -> str:
    doc = fitz.open(pdf_path)
    texts: list[str] = []
    try:
        for i in range(min(max_pages, doc.page_count)):
            page = doc.load_page(i)
            texts.append(page.get_text("text"))
    finally:
        doc.close()
    return "\n".join(texts)


def normalize_abstract_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def find_abstract(text: str) -> str | None:
    normalized = normalize_abstract_text(text)
    lines = normalized.split("\n")

    start_idx: Optional[int] = None
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        for pat in ABSTRACT_START_PATTERNS:
            if re.search(pat, line_stripped, flags=re.IGNORECASE):
                start_idx = i
                break
        if start_idx is not None:
            break
    if start_idx is None:
        return None

    after = "\n".join(lines[start_idx:])
    after = re.sub(r"^\s*(abstract|摘要)\s*[:：\-—]*\s*", "", after, flags=re.IGNORECASE)

    end_pos: Optional[int] = None
    for pat in ABSTRACT_END_PATTERNS:
        match = re.search(rf"(?m)^\s*{pat}\b", after, flags=re.IGNORECASE)
        if match:
            end_pos = match.start()
            break

    abstract = after[:end_pos].strip() if end_pos is not None else after.strip()
    abstract = re.sub(r"\n{3,}", "\n\n", abstract).strip()
    abstract = re.sub(r"\s*\n\s*", " ", abstract).strip()
    return abstract if len(abstract) >= 20 else None


def extract_abstract(pdf_path: str) -> Optional[str]:
    text = extract_text_from_first_pages(pdf_path, max_pages=4)
    abstract = find_abstract(text)
    if not abstract:
        print("Abstract not found. Consider increasing max_pages or using OCR.")
    return abstract


def canonicalize_for_compare(s: Optional[str]) -> str:
    if not s:
        return ""

    s = unicodedata.normalize("NFKC", s)
    for ch in _ZERO_WIDTH:
        s = s.replace(ch, "")
    for ch in _DASH_CHARS:
        s = s.replace(ch, "-")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def is_similar_text(a: str, b: str, threshold: float = 0.92) -> bool:
    a2 = canonicalize_for_compare(a)
    b2 = canonicalize_for_compare(b)
    if not a2 or not b2:
        return False

    if abs(len(a2) - len(b2)) / max(len(a2), len(b2)) > 0.25:
        return False

    return SequenceMatcher(None, a2, b2).ratio() >= threshold


def resolve_path_arg(raw_value: str, default_label: Path, default_path: Path) -> Path:
    if raw_value == str(default_label):
        return default_path
    return Path(raw_value).expanduser().resolve()


def resequence_order(passages: list[Passage], start: int = 0) -> None:
    for i, passage in enumerate(passages, start=start):
        passage.order_index = i


def save_passages_json(passages: list[Passage], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [
        {"type": passage.passage_type, "order": passage.order_index, "text": passage.text}
        for passage in passages
    ]
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _iter_text(node: etree._Element) -> str:
    return "".join(node.itertext())


def call_grobid_fulltext(
    pdf_path: str,
    grobid_url: str = DEFAULT_GROBID_URL,
    timeout: int = 600,
) -> str:
    with open(pdf_path, "rb") as f:
        files = {"input": f}
        data = {
            "consolidateHeader": "1",
            "consolidateCitations": "0",
            "includeRawAffiliations": "0",
            "teiCoordinates": "0",
        }
        resp = requests.post(grobid_url, files=files, data=data, timeout=timeout)

    if resp.status_code != 200:
        raise RuntimeError(
            f"GROBID call failed, status={resp.status_code}, response={resp.text[:1000]}"
        )
    return resp.text


def extract_abstract_area_teaser_texts(nodes: Iterable[etree._Element]) -> list[str]:
    results: list[str] = []

    for node in nodes:
        p_nodes = node.xpath(
            ".//tei:p[not(ancestor::tei:figure)]",
            namespaces=TEI_NS,
        )
        if p_nodes:
            for p in p_nodes:
                text = normalize_text(_iter_text(p))
                if text:
                    results.append(text)
            continue

        node_copy = etree.fromstring(etree.tostring(node))
        for fig in node_copy.xpath(".//tei:figure", namespaces=TEI_NS):
            parent = fig.getparent()
            if parent is not None:
                parent.remove(fig)

        text = normalize_text(_iter_text(node_copy))
        if text:
            results.append(text)

    return results


def tei_to_passages(tei_xml: str) -> list[Passage]:
    root = etree.fromstring(tei_xml.encode("utf-8"))

    passages: list[Passage] = []
    seen: set[tuple[str, str]] = set()

    def add(text: str, ptype: Literal["paragraph", "caption", "title"]) -> None:
        normalized = normalize_text(text)
        if not normalized:
            return

        key = (ptype, canonicalize_for_compare(normalized))
        if key in seen:
            return
        seen.add(key)
        passages.append(Passage(text=normalized, passage_type=ptype, order_index=-1))

    abstract_divs = root.xpath(".//tei:text//tei:div[@type='abstract']", namespaces=TEI_NS)
    teaser_texts = extract_abstract_area_teaser_texts(abstract_divs)

    if not teaser_texts:
        header_abstracts = root.xpath(".//tei:teiHeader//tei:abstract", namespaces=TEI_NS)
        teaser_texts = extract_abstract_area_teaser_texts(header_abstracts)

    for teaser_text in teaser_texts:
        add(teaser_text, "paragraph")

    text_node = root.find(".//tei:text", namespaces=TEI_NS)
    if text_node is None:
        resequence_order(passages, start=0)
        return passages

    def walk(node: etree._Element) -> None:
        for child in node:
            tag = etree.QName(child.tag).localname

            if tag == "back":
                continue

            if tag == "head":
                add(_iter_text(child), "title")
                walk(child)
                continue

            if tag == "p":
                add(_iter_text(child), "paragraph")
                continue

            if tag == "figure":
                fig_desc_nodes = child.xpath(".//tei:figDesc", namespaces=TEI_NS)
                if fig_desc_nodes:
                    caption = " ".join(normalize_text(_iter_text(node)) for node in fig_desc_nodes)
                else:
                    caption = _iter_text(child)
                add(caption, "caption")
                continue

            walk(child)

    walk(text_node)
    resequence_order(passages, start=0)
    return passages


def ensure_abstract_prefix(passages: list[Passage], abstract_text: Optional[str]) -> list[Passage]:
    abstract_text = normalize_text(abstract_text)
    if not abstract_text:
        resequence_order(passages, start=0)
        return passages

    new_passages: list[Passage] = [
        Passage(text="Abstract", passage_type="title", order_index=-1)
    ]

    exists = any(is_similar_text(passage.text, abstract_text, threshold=0.92) for passage in passages)
    if not exists:
        new_passages.append(
            Passage(text=abstract_text, passage_type="paragraph", order_index=-1)
        )

    new_passages.extend(passages)
    resequence_order(new_passages, start=0)
    return new_passages


def extract_passages_from_pdf_via_grobid(
    pdf_path: str,
    grobid_url: str = DEFAULT_GROBID_URL,
    timeout: int = 600,
) -> list[Passage]:
    tei_xml = call_grobid_fulltext(pdf_path, grobid_url=grobid_url, timeout=timeout)
    passages = tei_to_passages(tei_xml)
    abstract = extract_abstract(pdf_path)
    passages = ensure_abstract_prefix(passages, abstract)
    return passages


def generate_passages_for_pdf(
    pdf_path: Path,
    passages_dir: Path = PASSAGES_DIR,
    grobid_url: str = DEFAULT_GROBID_URL,
    timeout: int = 600,
    overwrite: bool = False,
) -> Path:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    out_path = passages_dir / f"{pdf_path.stem}_passages.json"
    if out_path.exists() and not overwrite:
        return out_path

    passages = extract_passages_from_pdf_via_grobid(
        str(pdf_path),
        grobid_url=grobid_url,
        timeout=timeout,
    )
    save_passages_json(passages, out_path)
    return out_path


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract passages from scholarly PDFs via GROBID.")
    parser.add_argument("--pdf", type=str, help="Path to a single PDF file.")
    parser.add_argument(
        "--out-dir",
        type=str,
        default=str(DEFAULT_PASSAGES_DIR_LABEL),
        help="Output directory. Defaults to ../data/passages.",
    )
    parser.add_argument(
        "--papers-dir",
        type=str,
        default=str(DEFAULT_PAPERS_DIR_LABEL),
        help="Directory containing input PDFs for batch mode.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process every PDF under --papers-dir.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing passages JSON. By default existing outputs are kept.",
    )
    parser.add_argument("--grobid-url", type=str, default=DEFAULT_GROBID_URL, help="GROBID API endpoint.")
    parser.add_argument("--timeout", type=int, default=600, help="GROBID request timeout in seconds.")
    return parser


def _run_single_pdf(args: argparse.Namespace) -> None:
    if not args.pdf:
        raise ValueError("--pdf is required unless --all is set.")

    pdf_path = Path(args.pdf).expanduser().resolve()
    out_path = generate_passages_for_pdf(
        pdf_path=pdf_path,
        passages_dir=resolve_path_arg(args.out_dir, DEFAULT_PASSAGES_DIR_LABEL, PASSAGES_DIR),
        grobid_url=args.grobid_url,
        timeout=args.timeout,
        overwrite=args.overwrite,
    )
    print(f"{pdf_path.stem}: passages saved -> {out_path}")


def _run_all_papers(args: argparse.Namespace) -> None:
    papers_dir = resolve_path_arg(args.papers_dir, DEFAULT_PAPERS_DIR_LABEL, PAPERS_DIR)
    pdf_paths = sorted(papers_dir.glob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in {papers_dir}")

    for pdf_path in pdf_paths:
        try:
            out_path = generate_passages_for_pdf(
                pdf_path=pdf_path,
                    passages_dir=resolve_path_arg(args.out_dir, DEFAULT_PASSAGES_DIR_LABEL, PASSAGES_DIR),
                grobid_url=args.grobid_url,
                timeout=args.timeout,
                overwrite=args.overwrite,
            )
            print(f"{pdf_path.stem}: passages saved -> {out_path}")
        except Exception as exc:
            print(f"{pdf_path.stem}: failed -> {exc}")


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    if args.all:
        _run_all_papers(args)
        return

    if not args.pdf:
        parser.error("Specify --pdf for a single run, or use --all for batch mode.")
    _run_single_pdf(args)


if __name__ == "__main__":
    main()
