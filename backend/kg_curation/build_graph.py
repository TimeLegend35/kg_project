"""Build an RDF knowledge graph (TTL) from the structured JSON produced by
transform_raw_data.py using the ontology defined in model.py.

Usage:
    pipenv run python "kg curation/build_graph.py" \
        --input "kg curation/output/bgb.json" \
        --output "kg curation/output/bgb.ttl"

Generates Turtle serialization plus basic stats.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, DCTERMS


BASE_ONTO = Namespace("http://example.org/bgb/ontology/")
BASE_DATA = Namespace("http://example.org/bgb/data/")


def curie_to_uri(curie: str) -> URIRef:
    if curie.startswith("bgb-data:"):
        return URIRef(BASE_DATA + curie.split(":", 1)[1])
    if curie.startswith("bgb-onto:"):
        return URIRef(BASE_ONTO + curie.split(":", 1)[1])
    return URIRef(curie)


def build_graph(data: Dict[str, Any]) -> Graph:
    g = Graph()
    g.bind("bgb-onto", BASE_ONTO)
    g.bind("bgb-data", BASE_DATA)
    g.bind("dcterms", DCTERMS)
    g.bind("rdfs", RDFS)
    g.bind("rdf", RDF)

    # Classes URIs
    CLASS_LEGAL_CODE = curie_to_uri("bgb-onto:LegalCode")
    CLASS_NORM = curie_to_uri("bgb-onto:Norm")
    CLASS_PARAGRAPH = curie_to_uri("bgb-onto:Paragraph")
    CLASS_CONCEPT = curie_to_uri("bgb-onto:LegalConcept")

    # Property URIs
    PROP_HAS_NORM = curie_to_uri("bgb-onto:hasNorm")
    PROP_HAS_PARAGRAPH = curie_to_uri("bgb-onto:hasParagraph")
    PROP_DEFINES = curie_to_uri("bgb-onto:defines")
    PROP_REFERS_TO = curie_to_uri("bgb-onto:refersTo")
    PROP_NORM_IDENTIFIER = curie_to_uri("bgb-onto:normIdentifier")
    PROP_PARA_IDENTIFIER = curie_to_uri("bgb-onto:paragraphIdentifier")
    PROP_TEXT_CONTENT = curie_to_uri("bgb-onto:textContent")
    PROP_IS_REPEALED = curie_to_uri("bgb-onto:isRepealed")

    # Create LegalCode instance
    code_uri = curie_to_uri(data["id"]) if "id" in data else curie_to_uri("bgb-data:BGB")
    g.add((code_uri, RDF.type, CLASS_LEGAL_CODE))
    g.add((code_uri, DCTERMS.title, Literal(data.get("title"))))

    norms = data.get("norms", [])
    for norm in norms:
        norm_uri = curie_to_uri(norm["id"])
        g.add((norm_uri, RDF.type, CLASS_NORM))
        g.add((code_uri, PROP_HAS_NORM, norm_uri))
        g.add((norm_uri, PROP_NORM_IDENTIFIER, Literal(norm.get("norm_identifier"))))
        if norm.get("title"):
            g.add((norm_uri, DCTERMS.title, Literal(norm["title"])))
        g.add((norm_uri, PROP_IS_REPEALED, Literal(bool(norm.get("is_repealed")))))

        for para in norm.get("paragraphs", []):
            para_uri = curie_to_uri(para["id"])
            g.add((para_uri, RDF.type, CLASS_PARAGRAPH))
            g.add((norm_uri, PROP_HAS_PARAGRAPH, para_uri))
            g.add((para_uri, PROP_PARA_IDENTIFIER, Literal(para.get("paragraph_identifier"))))
            g.add((para_uri, PROP_TEXT_CONTENT, Literal(para.get("text_content"))))

            # --- CONCEPT LOGIC REMOVED FROM HERE ---
            # The concepts are now handled by the global list below.

            for ref in para.get("refers_to", []):
                target_uri = curie_to_uri(ref["target_norm_id"])
                g.add((para_uri, PROP_REFERS_TO, target_uri))

    # --- NEW CONCEPT LOGIC ---
    # Add concepts from the global concept index provided in the JSON
    # The JSON stores concepts in "conceptIndex" as a dictionary (key: id, value: object)
    concept_index = data.get("conceptIndex", {})
    for concept in concept_index.values():
        concept_uri = curie_to_uri(concept["id"])
        g.add((concept_uri, RDF.type, CLASS_CONCEPT))
        g.add((concept_uri, RDFS.label, Literal(concept.get("label"))))
        
        # Link the concept back to the paragraph that defines it
        if concept.get("defined_in"):
            para_uri = curie_to_uri(concept["defined_in"])
            # This creates the triple: [Paragraph] bgb-onto:defines [LegalConcept]
            g.add((para_uri, PROP_DEFINES, concept_uri))

    return g


def main() -> int:
    parser = argparse.ArgumentParser(description="Build RDF graph from BGB JSON")
    parser.add_argument("--input", required=True, help="Path to bgb.json")
    parser.add_argument("--output", required=True, help="Path to output TTL file")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    g = build_graph(data)
    
    # Ensure the output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    ttl = g.serialize(format="turtle")
    output_path.write_text(ttl, encoding="utf-8")
    
    print(f"Graph written to {args.output}. Triples: {len(g)}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())