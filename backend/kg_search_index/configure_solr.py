#!/usr/bin/env python3
"""
Configure Solr core for BGB indexing
"""

import json
import logging
import requests
import sys
import time

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
    schema_api = f"{solr_url}/schema"

    # Add German text field type
    field_type = {
        "name": "text_de",
        "class": "solr.TextField",
        "positionIncrementGap": "100",
        "analyzer": {
            "tokenizer": {"class": "solr.StandardTokenizerFactory"},
            "filters": [
                {"class": "solr.LowerCaseFilterFactory"},
                {"class": "solr.GermanNormalizationFilterFactory"},
                {"class": "solr.GermanLightStemFilterFactory"},
            ],
        },
    }

    try:
        requests.post(
            schema_api,
            headers={"Content-Type": "application/json"},
            data=json.dumps({"add-field-type": field_type}),
            timeout=10,
        )
        logger.info("Added German text field type")
    except requests.RequestException:
        pass  # Field type might already exist

    # Add required fields
    fields = [
        {"name": "label", "type": "text_de", "indexed": True, "stored": True},
        {"name": "title", "type": "text_de", "indexed": True, "stored": True},
        {"name": "text_content", "type": "text_de", "indexed": True, "stored": True},
        {"name": "search_text", "type": "text_de", "indexed": True, "stored": False, "multiValued": True},
    ]

    for field in fields:
        try:
            requests.post(
                schema_api,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"add-field": field}),
                timeout=10,
            )
            logger.info("Added field: %s", field["name"])
        except requests.RequestException:
            pass  # Field might already exist

    # Add copy fields to populate search_text
    copy_fields = [
        {"source": "label", "dest": "search_text"},
        {"source": "title", "dest": "search_text"},
        {"source": "text_content", "dest": "search_text"},
    ]

    for copy_field in copy_fields:
        try:
            requests.post(
                schema_api,
                headers={"Content-Type": "application/json"},
                data=json.dumps({"add-copy-field": copy_field}),
                timeout=10,
            )
            logger.info("Added copy field: %s -> %s", copy_field["source"], copy_field["dest"])
        except requests.RequestException:
            pass  # Copy field might already exist


def main():
    solr_base_url = "http://localhost:8984/solr"
    core_name = "bgb_core"
    solr_url = f"{solr_base_url}/{core_name}"

    # Wait for Solr
    if not wait_for_solr(solr_base_url):
        logger.error("Solr failed to start")
        sys.exit(1)

    # Check if core exists
    try:
        response = requests.get(f"{solr_url}/admin/ping", timeout=5)
        if response.status_code == 200:
            logger.info("Core %s is ready", core_name)
        else:
            logger.error("Core %s is not available", core_name)
            sys.exit(1)
    except requests.RequestException as e:
        logger.error("Cannot access core %s: %s", core_name, e)
        sys.exit(1)

    # Configure schema
    configure_core_schema(solr_url)

    logger.info("Solr configuration complete!")


if __name__ == "__main__":
    main()
