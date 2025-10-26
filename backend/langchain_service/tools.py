from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import sys
import os
import requests

# Add the parent directory to the path to import project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BGBSolrSearchInput(BaseModel):
    """Input schema for BGB Solr search tool."""
    german_query: str = Field(
        description="German search query to find relevant BGB articles and paragraphs"
    )


class BGBSparqlQueryInput(BaseModel):
    """Input schema for dynamic BGB SPARQL query tool."""
    sparql_query: str = Field(
        description="Complete SPARQL query to execute against the BGB knowledge graph. Must include proper prefixes and be syntactically correct."
    )
    query_description: str = Field(
        description="Brief description of what this SPARQL query is intended to find or explore"
    )


def _search_solr(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Internal function to search the BGB Solr index.
    
    Args:
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of search results
    """
    solr_url = "http://localhost:8984/solr/bgb_core"
    select_url = f"{solr_url}/select"
    
    # Build Solr query - search across multiple text fields
    text_fields = ["label", "title", "text_content", "norm_number"]
    field_queries = [f"{field}:({query})" for field in text_fields]
    solr_query = " OR ".join(field_queries)
    
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
        response = requests.get(select_url, params=params, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        docs = result.get("response", {}).get("docs", [])
        highlighting = result.get("highlighting", {})
        
        # Add highlighting information to documents and format for tool output
        formatted_results = []
        for doc in docs:
            doc_id = doc.get("id")
            if doc_id in highlighting:
                doc["highlighting"] = highlighting[doc_id]
            
            # Extract values from arrays if needed
            uri_raw = doc.get("uri", ["no uri"])
            uri = uri_raw[0] if isinstance(uri_raw, list) else uri_raw
            
            label_raw = doc.get("label")
            label = label_raw[0] if isinstance(label_raw, list) and label_raw else ""
            
            title_raw = doc.get("title")  
            title = title_raw[0] if isinstance(title_raw, list) and title_raw else ""
            
            text_content_raw = doc.get("text_content")
            text_content = text_content_raw[0] if isinstance(text_content_raw, list) and text_content_raw else ""
            
            # Create formatted result
            formatted_result = {
                "id": uri,
                "title": title or label,
                "snippet": text_content[:300] + "..." if len(text_content) > 300 else text_content,
                "score": doc.get("score", 0)
            }
            formatted_results.append(formatted_result)
            
        return formatted_results
        
    except requests.RequestException as e:
        error_msg = f"Error connecting to Solr: {e}"
        print(error_msg)
        # Return error information instead of mock data
        return [{
            "id": "error",
            "title": "Solr-Suchfehler",
            "snippet": f"Verbindung zu Solr-Service fehlgeschlagen. Überprüfen Sie, ob Solr auf localhost:8984 läuft.",
            "score": 0,
            "error": True
        }]


def _execute_sparql_query(sparql_query: str, query_description: str) -> str:
    """
    Internal function to execute a custom SPARQL query against the BGB knowledge graph.
    
    Args:
        sparql_query: Complete SPARQL query to execute
        query_description: Description of what the query is intended to find
        
    Returns:
        Formatted results of the SPARQL query execution
    """
    blazegraph_url = "http://localhost:9999/bigdata"
    sparql_endpoint = f"{blazegraph_url}/sparql"
    
    try:
        response = requests.post(
            sparql_endpoint,
            data={"query": sparql_query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=30,
        )
        response.raise_for_status()
        
        result = response.json()
        bindings = result.get("results", {}).get("bindings", [])
        
        if bindings:
            # Format results in a readable way
            formatted_result = f"SPARQL-Ergebnisse für '{query_description}' ({len(bindings)} Treffer):\n"
            
            # Process each result binding
            for i, binding in enumerate(bindings[:10], 1):  # Limit to first 10 results
                formatted_result += f"\n--- Ergebnis {i} ---\n"
                for var, value in binding.items():
                    var_value = value.get("value", "")
                    formatted_result += f"{var}: {var_value}\n"
            
            if len(bindings) > 10:
                formatted_result += f"\n... und {len(bindings) - 10} weitere Ergebnisse (zeige erste 10)"
            
            return formatted_result
        else:
            return f"SPARQL-Ergebnisse: Keine Treffer für '{query_description}'. Abfrage möglicherweise zu spezifisch oder Entity existiert nicht in der Wissensbasis."
            
    except requests.RequestException as e:
        return f"SPARQL-Fehler: Verbindung zu Blazegraph fehlgeschlagen. Überprüfen Sie, ob der Service auf localhost:9999 läuft. Details: {str(e)}"
    except (ValueError, KeyError, TypeError) as e:
        return f"SPARQL-Verarbeitungsfehler: Ungültige Syntax oder JSON-Parsing-Problem. Details: {str(e)}"
@tool("bgb_solr_search", args_schema=BGBSolrSearchInput)
def bgb_solr_search(german_query: str) -> List[Dict[str, Any]]:
    """
    Durchsucht den Solr-Index nach BGB (Bürgerliches Gesetzbuch) Artikeln und Paragraphen.
    
    Dieses Tool durchsucht indexierte BGB-Inhalte, um relevante Rechtsartikel basierend auf 
    deutschen Suchbegriffen zu finden. Es gibt strukturierte Informationen über passende
    Artikel zurück, einschließlich ihrer IDs, Titel und Inhaltsausschnitte.
    
    Args:
        german_query: Deutsche Suchbegriffe zum Finden relevanter BGB-Artikel
        
    Returns:
        Liste von Wörterbüchern mit Artikelinformationen mit folgenden Schlüsseln:
        - id: Artikel-Identifikator (z.B. "bgb:§833")
        - title: Artikeltitel auf Deutsch
        - snippet: Relevanter Inhaltsausschnitt
        - score: Relevanz-Score
    """
    print(f"🔍 TOOL CALL: bgb_solr_search with query: '{german_query}'")
    
    result = _search_solr(german_query)
    
    print(f"🔍 TOOL RESULT: Found {len(result)} articles")
    for article in result:
        print(f"  - {article['id']}: {article['title']} (Score: {article.get('score', 'N/A')})")
    
    return result


@tool("execute_bgb_sparql_query", args_schema=BGBSparqlQueryInput)
def execute_bgb_sparql_query(sparql_query: str, query_description: str) -> str:
    """
    Führt eine benutzerdefinierte SPARQL-Abfrage gegen den BGB (Bürgerliches Gesetzbuch) Wissensgraph aus.
    
    Dieses Tool ermöglicht dynamische Abfragen der BGB-Ontologie mit benutzerdefinierten SPARQL-Queries.
    Das LLM kann spezifische Abfragen schreiben, um Beziehungen zu erkunden, bestimmte Normen zu finden,
    oder komplexe Analysen des rechtlichen Wissensgraphs durchzuführen.
    Dieses Tool ist nicht für Freitextsuche gedacht, sondern sollte auf Ergebnissen der Suche aufbauen.
    Wichtig: Die SPARQL-Abfrage muss vollständig und syntaktisch korrekt sein, einschließlich
    aller notwendigen Präfixe. Häufige Präfixe für die BGB-Ontologie:
    - PREFIX bgb-data: <http://example.org/bgb/data/>
    - PREFIX bgb-onto: <http://example.org/bgb/ontology/>
    - PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    Häufige Klassen: bgb-onto:LegalCode, bgb-onto:Norm, bgb-onto:Paragraph, bgb-onto:LegalConcept
    Häufige Eigenschaften: bgb-onto:hasNorm, bgb-onto:hasParagraph, bgb-onto:textContent, bgb-onto:defines
    
    Args:
        sparql_query: Vollständige SPARQL-Abfrage zur Ausführung (muss Präfixe enthalten)
        query_description: Kurze Beschreibung, was die Abfrage finden soll
        
    Returns:
        Formatierte Ergebnisse der SPARQL-Abfrage-Ausführung mit allen gefundenen Bindungen
    """
    print("🔎 TOOL CALL: execute_bgb_sparql_query")
    print(f"📝 Query Description: {query_description}")
    print(f"🔍 SPARQL Query: {sparql_query[:200]}...")
    
    result = _execute_sparql_query(sparql_query, query_description)
    
    print("🔎 TOOL RESULT: SPARQL query executed")
    return result



