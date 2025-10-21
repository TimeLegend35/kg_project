#!/usr/bin/env python3
"""
Configure Solr core for BGB indexing
"""

import json
import logging
import requests
import sys
import time
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_solr(solr_base_url: str, timeout: int = 60):
    """Wait for Solr to be ready."""
    logger.info("Waiting for Solr to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{solr_base_url}/admin/cores", timeout=5)
            if response.status_code == 200:
                logger.info("Solr is ready!")
                return True
        except requests.RequestException:
            pass
        time.sleep(1)

    return False


def configure_core_schema(solr_url: str):
    """Configure the Solr core schema."""
    schema_api = urljoin(solr_url, "schema")

    # Field types
    field_types = [
        {
            "name": "text_de",
            "class": "solr.TextField",
            "positionIncrementGap": "100",
            "analyzer": {
                "tokenizer": {"class": "solr.StandardTokenizerFactory"},
                "filters": [
                    {"class": "solr.LowerCaseFilterFactory"},
                    {
                        "class": "solr.StopFilterFactory",
                        "ignoreCase": "true",
                        "words": "lang/stopwords_de.txt",
                    },
                    {"class": "solr.GermanNormalizationFilterFactory"},
                    {"class": "solr.GermanLightStemFilterFactory"},
                ],
            },
        }
    ]

    # Add field types
    for field_type in field_types:
        try:
            response = requests.post(
                schema_api,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"add-field-type": field_type}),
                timeout=10,
            )
            if response.status_code == 200:
                logger.info(f"Added field type: {field_type['name']}")
        except requests.RequestException as e:
            logger.warning(f"Could not add field type {field_type['name']}: {e}")

    # Fields to add
    fields = [
        {
            "name": "uri",
            "type": "string",
            "indexed": True,
            "stored": True,
            "required": True,
        },
        {
            "name": "type",
            "type": "string",
            "indexed": True,
            "stored": True,
            "required": True,
        },
        {
            "name": "rdf_type",
            "type": "string",
            "indexed": True,
            "stored": True,
            "multiValued": True,
        },
        {"name": "label", "type": "text_de", "indexed": True, "stored": True},
        {"name": "title", "type": "text_de", "indexed": True, "stored": True},
        {"name": "text_content", "type": "text_de", "indexed": True, "stored": True},
        {"name": "norm_number", "type": "string", "indexed": True, "stored": True},
        {"name": "paragraph_number", "type": "string", "indexed": True, "stored": True},
        {
            "name": "has_norm",
            "type": "string",
            "indexed": True,
            "stored": True,
            "multiValued": True,
        },
        {
            "name": "has_paragraph",
            "type": "string",
            "indexed": True,
            "stored": True,
            "multiValued": True,
        },
        {"name": "belongs_to_norm", "type": "string", "indexed": True, "stored": True},
        {
            "name": "mentions_concept",
            "type": "string",
            "indexed": True,
            "stored": True,
            "multiValued": True,
        },
        {
            "name": "search_text",
            "type": "text_de",
            "indexed": True,
            "stored": False,
            "multiValued": True,
        },
    ]

    # Add fields
    for field in fields:
        try:
            response = requests.post(
                schema_api,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"add-field": field}),
                timeout=10,
            )
            if response.status_code == 200:
                logger.info(f"Added field: {field['name']}")
        except requests.RequestException as e:
            logger.warning(f"Could not add field {field['name']}: {e}")

    # Copy fields
    copy_fields = [
        {"source": "label", "dest": "search_text"},
        {"source": "title", "dest": "search_text"},
        {"source": "text_content", "dest": "search_text"},
        {"source": "norm_number", "dest": "search_text"},
    ]

    for copy_field in copy_fields:
        try:
            response = requests.post(
                schema_api,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"add-copy-field": copy_field}),
                timeout=10,
            )
            if response.status_code == 200:
                logger.info(
                    f"Added copy field: {copy_field['source']} -> {copy_field['dest']}"
                )
        except requests.RequestException as e:
            logger.warning(f"Could not add copy field {copy_field}: {e}")


def main():
    solr_base_url = "http://localhost:8984/solr"
    core_name = "bgb_core"
    solr_url = f"{solr_base_url}/{core_name}"

    # Wait for Solr
    if not wait_for_solr(solr_base_url):
        logger.error("Solr failed to start")
        sys.exit(1)

    # Check if core exists, if not it was created by docker command
    try:
        response = requests.get(f"{solr_url}/admin/ping", timeout=5)
        if response.status_code == 200:
            logger.info(f"Core {core_name} is ready")
        else:
            logger.error(f"Core {core_name} is not available")
            sys.exit(1)
    except requests.RequestException as e:
        logger.error(f"Cannot access core {core_name}: {e}")
        sys.exit(1)

    # Configure schema
    configure_core_schema(solr_url)

    logger.info("Solr configuration complete!")


if __name__ == "__main__":
    main()
