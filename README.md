# BGB Knowledge Graph Curation

This project transforms the raw XML of the Bürgerliches Gesetzbuch (BGB) downloaded from https://www.gesetze-im-internet.de/bgb/ into a structured JSON (optionally JSON-LD) aligned with a custom ontology.

## Ontology Summary
Classes: LegalCode, Norm, Paragraph, LegalConcept
Properties include normIdentifier, paragraphIdentifier, textContent, isRepealed, defines, refersTo, hasNorm, hasParagraph.
See `kg curation/model.py` for Pydantic schema and JSON-LD context.

## Requirements
- Python 3.11
- pipenv

## Install
```bash
pipenv install
```

## Run Transformation
```bash
pipenv run python "kg_curation/transform_raw_data.py" \
  --input "kg_curation/data/BJNR001950896.xml" \
  --output "kg_curation/output/bgb.json" \
  --jsonld
```
Output file: `kg_curation/output/bgb.json`.

## Build RDF Knowledge Graph
Convert JSON to Turtle using rdflib:
```bash
pipenv run python "kg_curation/build_graph.py" \
  --input "kg_curation/output/bgb.json" \
  --output "kg_curation/output/bgb.ttl"
```
Result: `kg_curation/output/bgb.ttl` (triples count printed after run).
