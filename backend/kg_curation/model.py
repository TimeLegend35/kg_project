"""Pydantic data model definitions for the BGB ontology.

Ontology summary:
Classes:
  - LegalCode
  - Norm
  - Paragraph
  - LegalConcept

Object Properties (represented through nesting / identifiers):
  - hasNorm (LegalCode -> [Norm])
  - hasParagraph (Norm -> [Paragraph])
  - defines (Paragraph -> [LegalConcept])
  - refersTo (Paragraph -> [Norm] by norm identifier references)

Datatype Properties:
  - dcterms:title (LegalCode.title, Norm.title, LegalConcept.label)
  - bgb-onto:normIdentifier (Norm.norm_identifier)
  - bgb-onto:paragraphIdentifier (Paragraph.paragraph_identifier)
  - bgb-onto:textContent (Paragraph.text_content)
  - bgb-onto:isRepealed (Norm.is_repealed)
  - rdfs:label (LegalConcept.label)

We also include a JSON-LD @context so the produced JSON can be directly consumed
by semantic tooling if desired.
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


NAMESPACES: Dict[str, str] = {
    "bgb-onto": "http://example.org/bgb/ontology/",
    "bgb-data": "http://example.org/bgb/data/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "dcterms": "http://purl.org/dc/terms/",
}


class LegalConcept(BaseModel):
    """Represents a legal concept defined by a paragraph.

    Attributes:
        id: CURIE-like identifier (e.g. bgb-data:concept_Verbraucher)
        label: Human readable label (rdfs:label)
        defined_in: Paragraph identifier that defines the concept.
    """

    id: str = Field(..., description="Global identifier for the concept")
    label: str = Field(..., description="rdfs:label of the concept")
    defined_in: Optional[str] = Field(
        None, description="Paragraph id (bgb-data:norm_13_para_1) that defines the concept"
    )


class ParagraphReference(BaseModel):
    """Represents a reference from a paragraph to another norm."""

    target_norm_id: str = Field(..., description="Identifier of referenced norm (e.g. bgb-data:norm_123)")
    text_snippet: Optional[str] = Field(
        None, description="Snippet of text showing the reference context"
    )


class Paragraph(BaseModel):
    """Represents a paragraph (Absatz / sentence block) inside a norm."""

    id: str = Field(..., description="Global identifier (e.g. bgb-data:norm_13_para_1)")
    paragraph_identifier: str = Field(..., description="Paragraph number within the norm")
    text_content: str = Field(..., description="Full textual content of the paragraph")
    defines_concepts: List[LegalConcept] = Field(
        default_factory=list, description="Concepts defined in this paragraph"
    )
    refers_to: List[ParagraphReference] = Field(
        default_factory=list, description="References to other norms"
    )


class Norm(BaseModel):
    """Represents a single norm (§)."""

    id: str = Field(..., description="Global identifier (e.g. bgb-data:norm_13)")
    norm_identifier: str = Field(..., description="The formal identifier (e.g. § 13)")
    title: Optional[str] = Field(None, description="Title / heading of the norm")
    is_repealed: bool = Field(False, description="Flag if norm is repealed or removed")
    paragraphs: List[Paragraph] = Field(
        default_factory=list, description="List of paragraphs belonging to this norm"
    )


class LegalCode(BaseModel):
    """Represents the entire legal code (the BGB)."""

    id: str = Field("bgb-data:BGB", description="Identifier for the code instance")
    title: str = Field(..., description="Official title, e.g. Bürgerliches Gesetzbuch")
    norms: List[Norm] = Field(default_factory=list, description="Norms contained in this code")
    concepts: List[LegalConcept] = Field(
        default_factory=list,
        description="Global registry of concepts defined anywhere in the code",
    )

    def build_concept_index(self) -> Dict[str, LegalConcept]:
        """Return a dictionary mapping concept id to concept consolidating paragraph-local lists."""
        index: Dict[str, LegalConcept] = {}
        # Add global concepts specified explicitly
        for c in self.concepts:
            index.setdefault(c.id, c)
        # Extract concepts defined inside paragraphs
        for norm in self.norms:
            for para in norm.paragraphs:
                for c in para.defines_concepts:
                    if c.id not in index:
                        index[c.id] = c
        return index

    def to_json_ld(self) -> Dict[str, Any]:
        """Serialize the model to a JSON-LD-like structure with @context."""
        context = {
            "@vocab": NAMESPACES["bgb-onto"],
            "bgb-onto": NAMESPACES["bgb-onto"],
            "bgb-data": NAMESPACES["bgb-data"],
            "rdf": NAMESPACES["rdf"],
            "rdfs": NAMESPACES["rdfs"],
            "dcterms": NAMESPACES["dcterms"],
            # Property mappings
            "title": "dcterms:title",
            "norm_identifier": "bgb-onto:normIdentifier",
            "paragraph_identifier": "bgb-onto:paragraphIdentifier",
            "text_content": "bgb-onto:textContent",
            "is_repealed": "bgb-onto:isRepealed",
            "label": "rdfs:label",
            "defines_concepts": {"@id": "bgb-onto:defines", "@type": "@id"},
            "refers_to": {"@id": "bgb-onto:refersTo", "@type": "@id"},
            "norms": {"@id": "bgb-onto:hasNorm", "@type": "@id"},
            "paragraphs": {"@id": "bgb-onto:hasParagraph", "@type": "@id"},
        }
        data = self.model_dump()
        data["@context"] = context
        data["conceptIndex"] = {k: v.model_dump() for k, v in self.build_concept_index().items()}
        return data


__all__ = [
    "LegalCode",
    "Norm",
    "Paragraph",
    "LegalConcept",
    "ParagraphReference",
    "NAMESPACES",
]

