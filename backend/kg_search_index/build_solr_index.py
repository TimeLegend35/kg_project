#!/usr/bin/env python3
"""
BGB Knowledge Graph Solr Indexer

This script parses the BGB TTL file and creates a Solr index optimized for
natural language queries to find URI nodes in the knowledge graph.

Usage:
    python build_solr_index.py [--ttl-file PATH] [--solr-url URL] [--batch-size SIZE]
"""

import argparse
import json
import logging
import re
import sys
import time
from typing import Dict, List, Optional, Set, Tuple
import requests
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, DCTERMS


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Define namespaces
BGB_DATA = Namespace("http://example.org/bgb/data/")
BGB_ONTO = Namespace("http://example.org/bgb/ontology/")


class BGBSolrIndexer:
    """
    Indexes BGB knowledge graph data into Solr for natural language search.
    """

    def __init__(self, solr_url: str = "http://localhost:8984/solr/bgb_core"):
        self.solr_url = solr_url
        self.update_url = f"{solr_url}/update"
        self.select_url = f"{solr_url}/select"
        self.graph = Graph()

        # Check Solr connection
        self._check_solr_connection()

    def _check_solr_connection(self):
        """Check if Solr is available."""
        try:
            response = requests.get(f"{self.solr_url}/admin/ping", timeout=5)
            response.raise_for_status()
            logger.info(f"Connected to Solr at {self.solr_url}")
        except requests.RequestException as e:
            logger.error(f"Cannot connect to Solr at {self.solr_url}: {e}")
            sys.exit(1)

    def load_ttl(self, ttl_file: str):
        """Load TTL file into RDFLib graph."""
        logger.info(f"Loading TTL file: {ttl_file}")
        try:
            self.graph.parse(ttl_file, format="turtle")
            logger.info(f"Loaded {len(self.graph)} triples from {ttl_file}")
        except Exception as e:
            logger.error(f"Error loading TTL file: {e}")
            sys.exit(1)

    def clear_index(self):
        """Clear the Solr index."""
        logger.info("Clearing Solr index...")
        try:
            response = requests.post(
                self.update_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"delete": {"query": "*:*"}}),
                timeout=30,
            )
            response.raise_for_status()

            # Commit the deletion
            response = requests.post(
                self.update_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"commit": {}}),
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Solr index cleared successfully")
        except requests.RequestException as e:
            logger.error(f"Error clearing Solr index: {e}")
            sys.exit(1)

    def extract_norm_number(self, uri: str) -> Optional[str]:
        """Extract norm number from URI."""
        match = re.search(r"norm_(\w+)", uri)
        return match.group(1) if match else None

    def extract_paragraph_number(self, uri: str) -> Optional[str]:
        """Extract paragraph number from URI."""
        match = re.search(r"para_(\w+)", uri)
        return match.group(1) if match else None

    def get_related_concepts(self, subject_uri: URIRef) -> List[str]:
        """
        Extract related legal concepts by analyzing text content for concept mentions.
        """
        concepts = []

        # Get text content for this subject
        text_content = None
        for obj in self.graph.objects(subject_uri, BGB_ONTO.textContent):
            text_content = str(obj)
            break

        if text_content:
            # Find concept labels mentioned in the text
            for concept_uri, _, label_obj in self.graph.triples(
                (None, RDFS.label, None)
            ):
                if str(concept_uri).startswith(str(BGB_DATA.concept_)):
                    label = str(label_obj)
                    if label.lower() in text_content.lower():
                        concepts.append(str(concept_uri))

        return concepts

    def create_document(self, subject_uri: URIRef) -> Optional[Dict]:
        """Create a Solr document from an RDF subject."""
        doc = {"id": str(subject_uri), "uri": str(subject_uri), "rdf_type": []}

        # Get RDF types
        for obj in self.graph.objects(subject_uri, RDF.type):
            doc["rdf_type"].append(str(obj))

        # Determine document type and extract relevant information
        if str(BGB_ONTO.LegalCode) in doc["rdf_type"]:
            doc["type"] = "legal_code"

            # Get title
            for obj in self.graph.objects(subject_uri, DCTERMS.title):
                doc["title"] = str(obj)
                break

            # Get related norms
            doc["has_norm"] = [
                str(obj) for obj in self.graph.objects(subject_uri, BGB_ONTO.hasNorm)
            ]

        elif str(BGB_ONTO.LegalConcept) in doc["rdf_type"]:
            doc["type"] = "legal_concept"

            # Get label
            for obj in self.graph.objects(subject_uri, RDFS.label):
                doc["label"] = str(obj)
                break

        elif str(BGB_ONTO.Norm) in doc["rdf_type"]:
            doc["type"] = "norm"

            # Extract norm number
            norm_number = self.extract_norm_number(str(subject_uri))
            if norm_number:
                doc["norm_number"] = norm_number

            # Get related paragraphs
            doc["has_paragraph"] = [
                str(obj)
                for obj in self.graph.objects(subject_uri, BGB_ONTO.hasParagraph)
            ]

        elif str(BGB_ONTO.Paragraph) in doc["rdf_type"]:
            doc["type"] = "paragraph"

            # Extract paragraph and norm numbers
            paragraph_number = self.extract_paragraph_number(str(subject_uri))
            if paragraph_number:
                doc["paragraph_number"] = paragraph_number

            norm_number = self.extract_norm_number(str(subject_uri))
            if norm_number:
                doc["norm_number"] = norm_number
                doc["belongs_to_norm"] = f"{BGB_DATA}norm_{norm_number}"

            # Get text content
            for obj in self.graph.objects(subject_uri, BGB_ONTO.textContent):
                doc["text_content"] = str(obj)
                break

            # Find related concepts mentioned in the text
            doc["mentions_concept"] = self.get_related_concepts(subject_uri)

        else:
            # Skip unknown types or return None to filter out
            return None

        # Ensure required fields are present
        if "type" not in doc:
            return None

        return doc

    def index_documents(self, documents: List[Dict], batch_size: int = 100):
        """Index a batch of documents in Solr."""
        if not documents:
            return

        logger.info(f"Indexing {len(documents)} documents...")

        try:
            response = requests.post(
                self.update_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(documents),
                timeout=60,
            )
            response.raise_for_status()
            logger.info(f"Successfully indexed {len(documents)} documents")
        except requests.RequestException as e:
            logger.error(f"Error indexing documents: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise

    def commit_index(self):
        """Commit changes to Solr index."""
        logger.info("Committing Solr index...")
        try:
            response = requests.post(
                self.update_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"commit": {}}),
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Solr index committed successfully")
        except requests.RequestException as e:
            logger.error(f"Error committing Solr index: {e}")
            raise

    def index_all(self, batch_size: int = 100):
        """Index all subjects from the loaded TTL file."""
        logger.info("Starting indexing process...")

        # Get all unique subjects
        subjects = set(self.graph.subjects())
        logger.info(f"Found {len(subjects)} unique subjects to process")

        documents = []
        processed_count = 0
        indexed_count = 0

        for subject in subjects:
            processed_count += 1

            # Create document
            doc = self.create_document(subject)
            if doc:
                documents.append(doc)
                indexed_count += 1

                # Index in batches
                if len(documents) >= batch_size:
                    self.index_documents(documents, batch_size)
                    documents = []

            # Progress reporting
            if processed_count % 1000 == 0:
                logger.info(
                    f"Processed {processed_count}/{len(subjects)} subjects, indexed {indexed_count}"
                )

        # Index remaining documents
        if documents:
            self.index_documents(documents, batch_size)

        # Commit the index
        self.commit_index()

        logger.info(
            f"Indexing complete! Processed {processed_count} subjects, indexed {indexed_count} documents"
        )

    def test_search(self, query: str = "Ehegatte", rows: int = 5):
        """Test the search functionality."""
        logger.info(f"Testing search with query: '{query}'")

        params = {
            "q": f"text_content:{query} OR label:{query} OR title:{query} OR norm_number:{query}",
            "wt": "json",
            "rows": rows,
            "fl": "id,uri,type,label,title,norm_number,score",
        }

        try:
            response = requests.get(self.select_url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            docs = result.get("response", {}).get("docs", [])

            logger.info(f"Found {len(docs)} results:")
            for i, doc in enumerate(docs, 1):
                logger.info(
                    f"{i}. {doc.get('type', 'unknown')} - {doc.get('uri', 'no uri')}"
                )
                if doc.get("label"):
                    logger.info(f"   Label: {doc['label']}")
                if doc.get("title"):
                    logger.info(f"   Title: {doc['title']}")
                if doc.get("norm_number"):
                    logger.info(f"   Norm: {doc['norm_number']}")
                logger.info(f"   Score: {doc.get('score', 0):.4f}")
                logger.info("")

        except requests.RequestException as e:
            logger.error(f"Error testing search: {e}")


def main():
    parser = argparse.ArgumentParser(description="Index BGB TTL file into Solr")
    parser.add_argument(
        "--ttl-file",
        default="kg_curation/output/bgb.ttl",
        help="Path to the TTL file (default: kg_curation/output/bgb.ttl)",
    )
    parser.add_argument(
        "--solr-url",
        default="http://localhost:8984/solr/bgb_core",
        help="Solr core URL (default: http://localhost:8984/solr/bgb_core)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for indexing (default: 100)",
    )
    parser.add_argument(
        "--clear-index", action="store_true", help="Clear the index before indexing"
    )
    parser.add_argument(
        "--test-search", help="Test search with the given query after indexing"
    )

    args = parser.parse_args()

    # Create indexer
    indexer = BGBSolrIndexer(args.solr_url)

    # Load TTL file
    indexer.load_ttl(args.ttl_file)

    # Clear index if requested
    if args.clear_index:
        indexer.clear_index()

    # Index all documents
    start_time = time.time()
    indexer.index_all(args.batch_size)
    end_time = time.time()

    logger.info(f"Total indexing time: {end_time - start_time:.2f} seconds")

    # Test search if requested
    if args.test_search:
        indexer.test_search(args.test_search)


if __name__ == "__main__":
    main()
