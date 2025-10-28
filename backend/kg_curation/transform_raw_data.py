#!/usr/bin/env python
"""Transform the raw BGB XML into a structured JSON representation based on the
Pydantic ontology in `model.py`.

Usage (after installing dependencies via pipenv):
    pipenv run python -m kg_curation.transform_raw_data \
        --input kg_curation/data/BJNR001950896.xml \
        --output kg_curation/output/bgb.json

Improvements in this version:
  - Parses the XML hierarchically by iterating over <norm> tags instead of
    flattening to text. This correctly finds ALL norms (§ 1 to § 2385).
  - Reliably extracts norm ID and Title from <metadaten>.
  - Preserves paragraph structure by extracting text from <P> tags inside <Content>.
  - Improved concept detection regex to support multi-word concepts
    (e.g., "Eingetragener Verein").
  - Corrected main function to ensure global `concepts` list is
    serialized to the output JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from typing import List

# Imports directly from your provided model.py
from model import LegalCode, Norm, Paragraph, LegalConcept, ParagraphReference


# --- Constants ---

# Regex to find norm identifiers like § 1 or § 23a
NORM_IDENT_RE = re.compile(r"§\s*([0-9]+[a-zA-Z]?)")
# Regex to split paragraphs by (1), (2), etc.
PARA_SPLIT_RE = re.compile(r"\((\d+)\)")
# Regex for references to other norms
REFERENCE_RE = re.compile(r"§\s*([0-9]+[a-zA-Z]?)")
# Regex for concept definitions (e.g., "Verbraucher ist..." or "Eingetragener Verein ist...")
CONCEPT_DEF_RE = re.compile(
    # Captures multi-word, capitalized concepts
    r"\b((?:[A-ZÄÖÜ][a-zäöüA-ZÄÖÜ]+)(?:\s+[A-ZÄÖÜ][a-zäöüA-ZÄÖÜ]+)*)\b\s+ist\b"
)


# --- New XML Helper Functions ---

def get_norm_body_text(content_elem: ET.Element | None) -> str:
    """
    Extracts and joins text from <P> tags within a <Content> element,
    preserving paragraph breaks as double newlines.
    """
    if content_elem is None:
        return ""

    paragraphs = []
    # Find all <P> tags, which typically segment the legal text
    for p_elem in content_elem.findall('.//P'):
        # .itertext() correctly gathers all text fragments within <P>
        text = "".join(p_elem.itertext()).strip()
        if text:
            paragraphs.append(text)

    if not paragraphs:
        # Fallback: If no <P> tags, grab all text from the <Content> block
        text = "".join(content_elem.itertext()).strip()
        return text

    # Join paragraphs with double newlines for the split heuristic
    return "\n\n".join(paragraphs)


def parse_norms_from_xml(root: ET.Element) -> List[Norm]:
    """
    Parses Norm objects by iterating over the hierarchical <norm> tags
    in the XML tree.
    """
    norms: List[Norm] = []
    
    # Iterate over every <norm> tag in the document
    for norm_elem in root.findall('.//norm'):
        meta = norm_elem.find('metadaten')
        text_data = norm_elem.find('textdaten')

        if meta is None or text_data is None:
            continue  # Skip if essential blocks are missing

        enbez_elem = meta.find('enbez')  # e.g., <enbez>§ 1</enbez>
        titel_elem = meta.find('titel')  # e.g., <titel>Beginn der Rechtsfähigkeit</titel>

        norm_identifier_text = (
            enbez_elem.text.strip() if enbez_elem is not None and enbez_elem.text else ""
        )
        title_text = (
            titel_elem.text.strip() if titel_elem is not None and titel_elem.text else ""
        )

        ident_match = NORM_IDENT_RE.search(norm_identifier_text)
        if not ident_match:
            ident_match = NORM_IDENT_RE.search(title_text)
            if not ident_match:
                continue  # Cannot reliably identify this norm

        ident = ident_match.group(1)
        norm_identifier = f"§ {ident}"
        full_title = f"{norm_identifier} {title_text}".strip()

        content_elem = text_data.find('.//Content')
        norm_body = get_norm_body_text(content_elem)

        is_repealed = '(weggefallen)' in title_text.lower() or \
                      '(weggefallen)' in norm_body.lower()

        current_norm = Norm(
            id=f"bgb-data:norm_{ident}",
            norm_identifier=norm_identifier,
            title=full_title,
            is_repealed=is_repealed,
            paragraphs=[],  # Will be populated below
        )

        current_norm.paragraphs = build_paragraphs(norm_body, current_norm)
        norms.append(current_norm)

    return norms


# --- Kept/Modified Functions ---

def build_paragraphs(text: str, norm: Norm) -> List[Paragraph]:
    """Splits norm body into paragraphs using (1) markers or double-newline fallback."""
    paragraphs: List[Paragraph] = []
    parts = PARA_SPLIT_RE.split(text)

    if len(parts) > 1:
        # PARA_SPLIT_RE produces: ['', '1', ' rest', '2', ' rest', ...]
        it = iter(parts)
        leading_text = next(it).strip()  # Text before the first (1)

        if leading_text:
            # Handle text before the first (1) as paragraph "0"
            paragraphs.append(build_paragraph(norm, "0", leading_text))

        seen_numbers = set()
        for number, body in zip(it, it):
            body_clean = body.strip()
            if not body_clean:
                continue

            orig_number = number
            counter = 1
            while number in seen_numbers:
                number = f"{orig_number}_{counter}"
                counter += 1
            seen_numbers.add(number)

            paragraphs.append(build_paragraph(norm, orig_number, body_clean))
    else:
        # No (1) markers, use double-newline split
        chunks = [c.strip() for c in re.split(r"\n\n+", text) if c.strip()]
        if not chunks and text:  # Handle single, non-empty block
            chunks = [text]

        for idx, chunk in enumerate(chunks, start=1):
            paragraphs.append(build_paragraph(norm, str(idx), chunk))
    return paragraphs


def build_paragraph(norm: Norm, number: str, body: str) -> Paragraph:
    """Builds a single Paragraph object, finding references and concepts."""
    para_id = f"bgb-data:{norm.id.split(':')[1]}_para_{number}"

    # Find references
    references: List[ParagraphReference] = []
    for m in REFERENCE_RE.finditer(body):
        ref_num = m.group(1)
        target_id = f"bgb-data:norm_{ref_num}"
        references.append(
            ParagraphReference(target_norm_id=target_id, text_snippet=m.group(0))
        )

    # Find concept definitions
    concepts: List[LegalConcept] = []
    for m in CONCEPT_DEF_RE.finditer(body):
        label = m.group(1).strip()
        # Create a stable ID from the label
        concept_id_label = label.replace(' ', '_')
        concept_id = f"bgb-data:concept_{concept_id_label}"
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
    """Main transformation logic."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Use the new, robust XML-parsing function
    norms = parse_norms_from_xml(root)
    
    # Create the LegalCode object based on model.py definition
    # (id, title, norms)
    code = LegalCode(
        id="bgb-data:BGB",
        title="Bürgerliches Gesetzbuch",
        norms=norms,
    )
    return code


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Transform BGB XML into structured JSON")
    parser.add_argument("--input", required=True, help="Path to raw BGB XML file")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    parser.add_argument("--jsonld", action="store_true", help="Emit JSON-LD with @context")
    args = parser.parse_args(argv)

    try:
        code = transform(args.input)
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file at {args.input}.")
        print(f"Details: {e}")
        return 1
    except FileNotFoundError:
        print(f"Error: Input file not found at {args.input}")
        return 1

    # --- Concept Aggregation and Serialization ---
    # We call build_concept_index() here, as intended by your model.
    concept_index = code.build_concept_index()
    concepts_list = list(concept_index.values())

    data = code.to_json_ld() if args.jsonld else code.model_dump()

    # **FIX**: If not using JSON-LD, model_dump() won't include concepts
    # because `concepts` isn't a field on the LegalCode model.
    # We manually add it to the output dict to match the ontology.
    if not args.jsonld:
        # We must dump the concept models to dicts as well
        data['concepts'] = [c.model_dump() for c in concepts_list]
    # -----------------------------------------------
    
    out_dir = os.path.dirname(args.output)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"Error: Could not write to output file at {args.output}.")
        print(f"Details: {e}")
        return 1

    # This print statement will now work correctly
    print(
        f"Wrote {args.output} containing {len(code.norms)} norms and "
        f"{len(concepts_list)} concepts."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())