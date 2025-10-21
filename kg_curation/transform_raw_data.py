"""Transform the raw BGB XML into a structured JSON representation based on the
Pydantic ontology in `model.py`.

Usage (after installing dependencies via pipenv):
    pipenv run python -m kg curation.transform_raw_data \
        --input kg curation/data/BJNR001950896.xml \
        --output kg curation/output/bgb.json

Heuristics:
  - Norm detection: lines beginning with "§" followed by number/letters.
  - Paragraph detection: numbered segments ("(1)", "(2)") or implicit split by double newline.
  - Concepts: pattern like "(\"?)([A-ZÄÖÜ][a-zäöü]+) ist" capturing definition; common German legal definitions often start with "Verbraucher ist..." etc.
    - References: regex for "§\\s*([0-9]+[a-zA-Z]?)" in paragraph text, mapped to existing norms.
  - Repealed: if the norm title or text contains "(weggefallen)" mark is_repealed=True.

Limitations: The official XML structure (gii-norm.dtd) contains richer tagging; here we rely
on text heuristics for simplicity. This can later be replaced by structured tag parsing.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from typing import List

from model import LegalCode, Norm, Paragraph, LegalConcept, ParagraphReference

NORM_START_RE = re.compile(r"^§\s*([0-9]+[a-zA-Z]?)")
PARA_SPLIT_RE = re.compile(r"\((\d+)\)")  # captures paragraph numbers
REFERENCE_RE = re.compile(r"§\s*([0-9]+[a-zA-Z]?)")
CONCEPT_DEF_RE = re.compile(r"\b([A-ZÄÖÜ][a-zäöüA-ZÄÖÜ]+)\b\s+ist\b")


def extract_text_nodes(root: ET.Element) -> List[str]:
    """Flatten text content from XML <Content> nodes inside <text> or <fussnoten>."""
    texts: List[str] = []
    for content in root.findall('.//Content'):
        # concatenate descendant text
        segment = []
        for elem in content.iter():
            if elem.text:
                segment.append(elem.text)
        joined = ' '.join(s.strip() for s in segment if s and s.strip())
        if joined:
            texts.append(joined)
    return texts


def parse_norms(raw_text: str) -> List[Norm]:
    """Parse raw text blob into Norm objects using regex heuristics."""
    lines = [l.strip() for l in raw_text.split('\n') if l.strip()]
    norms: List[Norm] = []
    current_norm: Norm | None = None
    buffer: List[str] = []

    for line in lines:
        norm_match = NORM_START_RE.match(line)
        if norm_match:
            # finalize previous norm
            if current_norm:
                current_norm.paragraphs = current_norm.paragraphs + build_paragraphs('\n'.join(buffer), current_norm)
                norms.append(current_norm)
            ident = norm_match.group(1)
            norm_identifier = f"§ {ident}"
            title = line
            is_repealed = '(weggefallen)' in line.lower()
            current_norm = Norm(
                id=f"bgb-data:norm_{ident}",
                norm_identifier=norm_identifier,
                title=title,
                is_repealed=is_repealed,
                paragraphs=[],
            )
            buffer = []
        else:
            buffer.append(line)

    # finalize last
    if current_norm:
        current_norm.paragraphs = current_norm.paragraphs + build_paragraphs('\n'.join(buffer), current_norm)
        norms.append(current_norm)
    return norms


def build_paragraphs(text: str, norm: Norm) -> List[Paragraph]:
    """Split norm body into paragraphs using PARA_SPLIT_RE markers or fallback."""
    paragraphs: List[Paragraph] = []
    # If there are explicit markers like (1) (2) we'll segment by them
    parts = PARA_SPLIT_RE.split(text)
    if len(parts) > 1:
        # PARA_SPLIT_RE produces: ['', '1', ' rest', '2', ' rest', ...]
        it = iter(parts)
        _ = next(it)  # discard leading before first marker
        seen_numbers = set()
        for number, body in zip(it, it):
            body_clean = body.strip()
            if not body_clean:
                continue
            # Ensure uniqueness if markers repeat due to malformed text
            orig_number = number
            counter = 1
            while number in seen_numbers:
                counter += 1
                number = f"{orig_number}_{counter}"  # append suffix to keep stable base
            seen_numbers.add(number)
            paragraphs.append(build_paragraph(norm, number, body_clean))
    else:
        # single paragraph
        # Split by double newline as secondary segmentation heuristic
        chunks = [c.strip() for c in re.split(r"\n\n+", text) if c.strip()]
        if not chunks:
            return paragraphs
        for idx, chunk in enumerate(chunks, start=1):
            paragraphs.append(build_paragraph(norm, str(idx), chunk))
    return paragraphs


def build_paragraph(norm: Norm, number: str, body: str) -> Paragraph:
    para_id = f"bgb-data:{norm.id.split(':')[1]}_para_{number}"
    # references
    references: List[ParagraphReference] = []
    for m in REFERENCE_RE.finditer(body):
        ref_num = m.group(1)
        target_id = f"bgb-data:norm_{ref_num}"
        references.append(ParagraphReference(target_norm_id=target_id, text_snippet=m.group(0)))
    # concepts
    concepts: List[LegalConcept] = []
    for m in CONCEPT_DEF_RE.finditer(body):
        label = m.group(1)
        concept_id = f"bgb-data:concept_{label}"
        concepts.append(
            LegalConcept(id=concept_id, label=label, defined_in=para_id)
        )
    return Paragraph(
        id=para_id,
        paragraph_identifier=number,
        text_content=body,
        defines_concepts=concepts,
        refers_to=references,
    )


def transform(xml_path: str) -> LegalCode:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    all_text_segments = extract_text_nodes(root)
    # Join segments for simple parsing; real implementation might separate norm blocks
    combined = '\n'.join(all_text_segments)
    norms = parse_norms(combined)
    code = LegalCode(title="Bürgerliches Gesetzbuch", norms=norms)
    # aggregate concepts globally
    concept_index = code.build_concept_index()
    code.concepts = list(concept_index.values())
    return code


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Transform BGB XML into structured JSON")
    parser.add_argument("--input", required=True, help="Path to raw BGB XML file")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    parser.add_argument("--jsonld", action="store_true", help="Emit JSON-LD with @context")
    args = parser.parse_args(argv)

    code = transform(args.input)
    data = code.to_json_ld() if args.jsonld else code.model_dump()
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {args.output} containing {len(code.norms)} norms and {len(code.concepts)} concepts.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
