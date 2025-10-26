#!/usr/bin/env python3
"""
BGB Solr Query Interface

A simple interface to query the BGB Solr index with natural language queries.
This script helps find URI nodes in the knowledge graph based on text searches.

Usage:
    python query_bgb.py "search terms"
    python query_bgb.py --interactive
"""

import argparse
import json
import sys
from typing import Dict, List
import requests


class BGBQueryInterface:
    """
    Interface for querying the BGB Solr index.
    """

    def __init__(self, solr_url: str = "http://localhost:8984/solr/bgb_core"):
        self.solr_url = solr_url
        self.select_url = f"{solr_url}/select"

        # Check Solr connection
        self._check_solr_connection()

    def _check_solr_connection(self):
        """Check if Solr is available."""
        try:
            response = requests.get(f"{self.solr_url}/admin/ping", timeout=5)
            response.raise_for_status()
            print(f"✓ Connected to Solr at {self.solr_url}")
        except requests.RequestException as e:
            print(f"✗ Cannot connect to Solr at {self.solr_url}: {e}")
            print(
                "Make sure Solr is running: docker-compose -f docker-compose.bgb-solr.yml up -d"
            )
            sys.exit(1)

    def search(
        self, query: str, max_results: int = 10, document_type: str = None
    ) -> List[Dict]:
        """
        Search the BGB index with natural language query.

        Args:
            query: Natural language search query
            max_results: Maximum number of results to return
            document_type: Filter by document type (legal_concept, norm, paragraph, legal_code)

        Returns:
            List of search results
        """
        # Build Solr query - search across multiple text fields
        text_fields = ["label", "title", "text_content", "norm_number"]
        field_queries = [f"{field}:({query})" for field in text_fields]
        solr_query = " OR ".join(field_queries)

        # Add type filter if specified
        if document_type:
            solr_query += f" AND type:{document_type}"

        params = {
            "q": solr_query,
            "wt": "json",
            "rows": max_results,
            "fl": "id,uri,type,label,title,norm_number,paragraph_number,text_content,score",
            "sort": "score desc",
            "hl": "true",
            "hl.fl": "label,title,text_content",
            "hl.simple.pre": "<b>",
            "hl.simple.post": "</b>",
            "hl.fragsize": 200,
        }

        try:
            response = requests.get(self.select_url, params=params, timeout=10)
            response.raise_for_status()

            result = response.json()
            docs = result.get("response", {}).get("docs", [])
            highlighting = result.get("highlighting", {})

            # Add highlighting information to documents
            for doc in docs:
                doc_id = doc.get("id")
                if doc_id in highlighting:
                    doc["highlighting"] = highlighting[doc_id]

            return docs

        except requests.RequestException as e:
            print(f"Error searching Solr: {e}")
            return []

    def print_results(self, results: List[Dict], query: str):
        """Print search results in a user-friendly format."""
        if not results:
            print(f"No results found for query: '{query}'")
            return

        print(f"\nFound {len(results)} results for query: '{query}'\n")
        print("=" * 80)

        for i, doc in enumerate(results, 1):
            doc_type_raw = doc.get("type", ["unknown"])
            doc_type = (
                (doc_type_raw[0] if isinstance(doc_type_raw, list) else doc_type_raw)
                .replace("_", " ")
                .title()
            )

            uri_raw = doc.get("uri", ["no uri"])
            uri = uri_raw[0] if isinstance(uri_raw, list) else uri_raw

            score = doc.get("score", 0)

            print(f"{i}. {doc_type} (Score: {score:.3f})")
            print(f"   URI: {uri}")

            # Show relevant text content
            label_raw = doc.get("label")
            if label_raw:
                label = label_raw[0] if isinstance(label_raw, list) else label_raw
                print(f"   Label: {label}")

            title_raw = doc.get("title")
            if title_raw:
                title = title_raw[0] if isinstance(title_raw, list) else title_raw
                print(f"   Title: {title}")

            norm_number_raw = doc.get("norm_number")
            if norm_number_raw:
                norm_number = (
                    norm_number_raw[0]
                    if isinstance(norm_number_raw, list)
                    else norm_number_raw
                )
                print(f"   Norm: §{norm_number}")

            paragraph_number_raw = doc.get("paragraph_number")
            if paragraph_number_raw:
                paragraph_number = (
                    paragraph_number_raw[0]
                    if isinstance(paragraph_number_raw, list)
                    else paragraph_number_raw
                )
                print(f"   Paragraph: {paragraph_number}")

            # Show text content (truncated)
            text_content_raw = doc.get("text_content")
            if text_content_raw:
                text_content = (
                    text_content_raw[0]
                    if isinstance(text_content_raw, list)
                    else text_content_raw
                )
                if len(text_content) > 200:
                    text_content = text_content[:197] + "..."
                print(f"   Content: {text_content}")

            # Show highlighting if available
            if doc.get("highlighting"):
                for field, highlights in doc["highlighting"].items():
                    if highlights:
                        print(f"   Highlight: {highlights[0]}")
                        break

            print()

    def interactive_mode(self):
        """Run in interactive mode for multiple queries."""
        print("BGB Knowledge Graph Query Interface")
        print("===================================")
        print("Enter natural language queries to search the BGB knowledge graph.")
        print("Type 'help' for commands or 'quit' to exit.\n")

        while True:
            try:
                query = input("BGB> ").strip()

                if not query:
                    continue

                if query.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break

                if query.lower() == "help":
                    self.print_help()
                    continue

                # Handle special commands
                if query.startswith("/"):
                    self.handle_command(query)
                    continue

                # Regular search
                results = self.search(query)
                self.print_results(results, query)

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

    def handle_command(self, command: str):
        """Handle special commands in interactive mode."""
        parts = command.split()
        cmd = parts[0].lower()

        if cmd == "/type":
            if len(parts) < 3:
                print("Usage: /type <document_type> <query>")
                print("Types: legal_concept, norm, paragraph, legal_code")
                return

            doc_type = parts[1]
            query = " ".join(parts[2:])
            results = self.search(query, document_type=doc_type)
            self.print_results(results, f"{query} (type: {doc_type})")

        elif cmd == "/uri":
            if len(parts) < 2:
                print("Usage: /uri <partial_uri>")
                return

            uri_part = parts[1]
            results = self.search(f"uri:*{uri_part}*")
            self.print_results(results, f"URI containing: {uri_part}")

        else:
            print(f"Unknown command: {cmd}")
            print("Type 'help' for available commands.")

    def print_help(self):
        """Print help information."""
        print(
            """
Available commands:
  help                    - Show this help
  quit, exit, q          - Exit the program
  
  /type <type> <query>   - Search within specific document type
                          Types: legal_concept, norm, paragraph, legal_code
  /uri <partial_uri>     - Search for URIs containing the given text
  
Examples:
  Ehegatte               - Search for content about spouses
  Vertrag                - Search for content about contracts
  /type norm Eigentum    - Search for norms about property
  /uri 1357              - Find URIs containing "1357"
        """
        )


def main():
    parser = argparse.ArgumentParser(description="Query BGB Solr index")
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query (if not provided, starts interactive mode)",
    )
    parser.add_argument(
        "--solr-url",
        default="http://localhost:8984/solr/bgb_core",
        help="Solr core URL (default: http://localhost:8984/solr/bgb_core)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of results to return (default: 10)",
    )
    parser.add_argument(
        "--type",
        help="Filter by document type (legal_concept, norm, paragraph, legal_code)",
    )
    parser.add_argument(
        "--interactive", "-i", action="store_true", help="Start in interactive mode"
    )

    args = parser.parse_args()

    # Create query interface
    interface = BGBQueryInterface(args.solr_url)

    if args.interactive or not args.query:
        # Interactive mode
        interface.interactive_mode()
    else:
        # Single query mode
        results = interface.search(args.query, args.max_results, args.type)
        interface.print_results(results, args.query)


if __name__ == "__main__":
    main()
