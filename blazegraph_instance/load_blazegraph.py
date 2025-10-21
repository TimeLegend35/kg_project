#!/usr/bin/env python3
"""
BGB Blazegraph Data Loader

This script loads the BGB TTL file into Blazegraph and sets up SPARQL querying.
"""

import argparse
import logging
import requests
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlazegraphLoader:
    """
    Loads RDF data into Blazegraph and manages SPARQL queries.
    """

    def __init__(self, blazegraph_url: str = "http://localhost:9999/bigdata"):
        self.blazegraph_url = blazegraph_url
        self.sparql_endpoint = f"{blazegraph_url}/sparql"
        self.update_endpoint = f"{blazegraph_url}/sparql"

        # Check Blazegraph connection
        self._check_blazegraph_connection()

    def _check_blazegraph_connection(self):
        """Check if Blazegraph is available."""
        try:
            response = requests.get(f"{self.blazegraph_url}/status", timeout=10)
            if response.status_code == 200:
                logger.info("Connected to Blazegraph at %s", self.blazegraph_url)
            else:
                # Try the main page if status endpoint doesn't exist
                response = requests.get(self.blazegraph_url, timeout=10)
                response.raise_for_status()
                logger.info("Connected to Blazegraph at %s", self.blazegraph_url)
        except requests.RequestException as e:
            logger.error(
                "Cannot connect to Blazegraph at %s: %s", self.blazegraph_url, e
            )
            logger.error(
                "Make sure Blazegraph is running: docker-compose -f docker-compose.bgb-solr.yml up -d"
            )
            sys.exit(1)

    def wait_for_blazegraph(self, timeout: int = 60):
        """Wait for Blazegraph to be ready."""
        logger.info("Waiting for Blazegraph to be ready...")
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                response = requests.get(self.blazegraph_url, timeout=5)
                if response.status_code == 200:
                    logger.info("Blazegraph is ready!")
                    return True
            except requests.RequestException:
                pass
            time.sleep(2)

        logger.error("Blazegraph failed to start within %d seconds", timeout)
        return False

    def clear_database(self):
        """Clear all data from the Blazegraph database."""
        logger.info("Clearing Blazegraph database...")

        clear_query = """
        DELETE WHERE {
            ?s ?p ?o .
        }
        """

        try:
            response = requests.post(
                self.update_endpoint,
                data={"update": clear_query},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            response.raise_for_status()
            logger.info("Blazegraph database cleared successfully")
        except requests.RequestException as e:
            logger.error("Error clearing Blazegraph database: %s", e)
            raise

    def load_ttl_file(self, ttl_file_path: str):
        """Load a TTL file into Blazegraph."""
        ttl_path = Path(ttl_file_path)

        if not ttl_path.exists():
            logger.error("TTL file not found: %s", ttl_file_path)
            sys.exit(1)

        logger.info("Loading TTL file: %s", ttl_file_path)

        try:
            with open(ttl_path, "rb") as f:
                ttl_content = f.read()

            # Load data via POST to SPARQL endpoint
            response = requests.post(
                self.sparql_endpoint,
                data=ttl_content,
                headers={"Content-Type": "text/turtle", "Accept": "application/xml"},
                timeout=120,  # TTL files can be large
            )
            response.raise_for_status()

            logger.info("Successfully loaded TTL file into Blazegraph")

        except requests.RequestException as e:
            logger.error("Error loading TTL file: %s", e)
            if hasattr(e, "response") and e.response is not None:
                logger.error("Response content: %s", e.response.text)
            raise

    def get_triple_count(self):
        """Get the total number of triples in the database."""
        count_query = """
        SELECT (COUNT(*) AS ?count) WHERE {
            ?s ?p ?o .
        }
        """

        try:
            response = requests.post(
                self.sparql_endpoint,
                data={"query": count_query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            count = int(result["results"]["bindings"][0]["count"]["value"])
            logger.info("Database contains %d triples", count)
            return count

        except requests.RequestException as e:
            logger.error("Error getting triple count: %s", e)
            return 0

    def test_sparql_query(self, limit: int = 5):
        """Test SPARQL querying with a sample query."""
        logger.info("Testing SPARQL query...")

        test_query = f"""
        PREFIX bgb-data: <http://example.org/bgb/data/>
        PREFIX bgb-onto: <http://example.org/bgb/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?concept ?label WHERE {{
            ?concept a bgb-onto:LegalConcept ;
                     rdfs:label ?label .
        }} LIMIT {limit}
        """

        try:
            response = requests.post(
                self.sparql_endpoint,
                data={"query": test_query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            bindings = result.get("results", {}).get("bindings", [])

            logger.info("Found %d legal concepts:", len(bindings))
            for i, binding in enumerate(bindings, 1):
                concept = binding["concept"]["value"]
                label = binding["label"]["value"]
                logger.info("%d. %s - %s", i, label, concept)

        except requests.RequestException as e:
            logger.error("Error testing SPARQL query: %s", e)

    def test_paragraph_query(self, search_term: str = "Ehegatte", limit: int = 3):
        """Test querying for paragraphs containing a specific term."""
        logger.info("Testing paragraph search for: %s", search_term)

        paragraph_query = f"""
        PREFIX bgb-data: <http://example.org/bgb/data/>
        PREFIX bgb-onto: <http://example.org/bgb/ontology/>
        
        SELECT ?paragraph ?content WHERE {{
            ?paragraph a bgb-onto:Paragraph ;
                       bgb-onto:textContent ?content .
            FILTER(CONTAINS(LCASE(?content), LCASE("{search_term}")))
        }} LIMIT {limit}
        """

        try:
            response = requests.post(
                self.sparql_endpoint,
                data={"query": paragraph_query},
                headers={"Accept": "application/sparql-results+json"},
                timeout=30,
            )
            response.raise_for_status()

            result = response.json()
            bindings = result.get("results", {}).get("bindings", [])

            logger.info(
                "Found %d paragraphs containing '%s':", len(bindings), search_term
            )
            for i, binding in enumerate(bindings, 1):
                paragraph = binding["paragraph"]["value"]
                content = binding["content"]["value"]
                # Truncate long content
                if len(content) > 100:
                    content = content[:97] + "..."
                logger.info("%d. %s", i, paragraph)
                logger.info("   Content: %s", content)
                logger.info("")

        except requests.RequestException as e:
            logger.error("Error testing paragraph query: %s", e)


def wait_for_blazegraph(blazegraph_url: str, timeout: int = 60):
    """Wait for Blazegraph to be ready."""
    logger.info("Waiting for Blazegraph to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(blazegraph_url, timeout=5)
            if response.status_code == 200:
                logger.info("Blazegraph is ready!")
                return True
        except requests.RequestException:
            pass
        time.sleep(2)

    return False


def main():
    parser = argparse.ArgumentParser(description="Load BGB TTL file into Blazegraph")
    parser.add_argument(
        "--ttl-file",
        default="kg_curation/output/bgb.ttl",
        help="Path to the TTL file (default: kg_curation/output/bgb.ttl)",
    )
    parser.add_argument(
        "--blazegraph-url",
        default="http://localhost:9999/bigdata",
        help="Blazegraph URL (default: http://localhost:9999/bigdata)",
    )
    parser.add_argument(
        "--clear-database",
        action="store_true",
        help="Clear the database before loading",
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for Blazegraph to be ready before loading",
    )
    parser.add_argument(
        "--test-query", help="Test search with the given term after loading"
    )

    args = parser.parse_args()

    # Wait for Blazegraph if requested
    if args.wait:
        if not wait_for_blazegraph(args.blazegraph_url):
            logger.error("Blazegraph failed to start")
            sys.exit(1)

    # Create loader
    loader = BlazegraphLoader(args.blazegraph_url)

    # Clear database if requested
    if args.clear_database:
        loader.clear_database()

    # Load TTL file
    start_time = time.time()
    loader.load_ttl_file(args.ttl_file)
    end_time = time.time()

    logger.info("Loading completed in %.2f seconds", end_time - start_time)

    # Get and display statistics
    triple_count = loader.get_triple_count()

    # Test queries
    loader.test_sparql_query()

    if args.test_query:
        loader.test_paragraph_query(args.test_query)
    else:
        loader.test_paragraph_query("Ehegatte")

    logger.info("Blazegraph is ready for SPARQL queries!")
    logger.info("Web interface: %s", args.blazegraph_url)
    logger.info("SPARQL endpoint: %s/sparql", args.blazegraph_url)


if __name__ == "__main__":
    main()
