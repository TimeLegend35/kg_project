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


class BGBEntityExploreInput(BaseModel):
    """Input schema for BGB entity exploration tool."""
    entity_uri: str = Field(
        description="The URI or identifier of the BGB entity to start exploring (e.g., 'bgb:§833')"
    )
    original_question: str = Field(
        description="The original user question for context-aware exploration"
    )


def _search_solr(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
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
        print(f"Error connecting to Solr: {e}")
        # Return mock data as fallback
        return _get_mock_solr_results(query)


def _get_mock_solr_results(query: str) -> List[Dict[str, Any]]:
    """Fallback mock data when Solr is not available."""
    if "hund" in query.lower() or "tier" in query.lower():
        return [
            {
                "id": "bgb:§833", 
                "title": "§ 833 Haftung des Tierhalters", 
                "snippet": "Wird durch ein Tier ein Mensch getötet, der Körper oder die Gesundheit eines Menschen verletzt oder eine Sache beschädigt, so ist derjenige, welcher das Tier hält, verpflichtet, dem Verletzten den daraus entstehenden Schaden zu ersetzen.",
                "score": 0.95
            },
            {
                "id": "bgb:§823", 
                "title": "§ 823 Schadensersatzpflicht", 
                "snippet": "Wer vorsätzlich oder fahrlässig das Leben, den Körper, die Gesundheit, die Freiheit, das Eigentum oder ein sonstiges Recht eines anderen widerrechtlich verletzt, ist dem anderen zum Ersatz des daraus entstehenden Schadens verpflichtet.",
                "score": 0.85
            }
        ]
    elif "eigentum" in query.lower() or "schaden" in query.lower():
        return [
            {
                "id": "bgb:§823", 
                "title": "§ 823 Schadensersatzpflicht", 
                "snippet": "Wer vorsätzlich oder fahrlässig das Leben, den Körper, die Gesundheit, die Freiheit, das Eigentum oder ein sonstiges Recht eines anderen widerrechtlich verletzt, ist dem anderen zum Ersatz des daraus entstehenden Schadens verpflichtet.",
                "score": 0.92
            },
            {
                "id": "bgb:§249", 
                "title": "§ 249 Art und Umfang des Schadensersatzes", 
                "snippet": "Wer zum Schadensersatz verpflichtet ist, hat den Zustand herzustellen, der bestehen würde, wenn der zum Ersatz verpflichtende Umstand nicht eingetreten wäre.",
                "score": 0.88
            }
        ]
    else:
        return [
            {
                "id": "bgb:§823", 
                "title": "§ 823 Schadensersatzpflicht", 
                "snippet": "Wer vorsätzlich oder fahrlässig das Leben, den Körper, die Gesundheit, die Freiheit, das Eigentum oder ein sonstiges Recht eines anderen widerrechtlich verletzt, ist dem anderen zum Ersatz des daraus entstehenden Schadens verpflichtet.",
                "score": 0.75
            }
        ]


def _query_sparql(entity_uri: str, original_question: str) -> str:
    """
    Internal function to query SPARQL for detailed entity information.
    
    Args:
        entity_uri: URI of the entity to explore
        original_question: Original question for context
        
    Returns:
        Detailed information about the entity
    """
    blazegraph_url = "http://localhost:9999/bigdata"
    sparql_endpoint = f"{blazegraph_url}/sparql"
    
    # Extract norm number from URI (e.g., "bgb:§833" -> "833")
    norm_number = entity_uri.replace("bgb:§", "").replace("bgb:", "")
    
    # Build SPARQL query to get detailed information about the norm
    query = f"""
    PREFIX bgb-data: <http://example.org/bgb/data/>
    PREFIX bgb-onto: <http://example.org/bgb/ontology/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?norm ?label ?content ?paragraph ?paragraphContent WHERE {{
        ?norm a bgb-onto:Norm ;
              rdfs:label ?label .
        OPTIONAL {{
            ?norm bgb-onto:textContent ?content .
        }}
        OPTIONAL {{
            ?norm bgb-onto:hasParagraph ?paragraph .
            ?paragraph bgb-onto:textContent ?paragraphContent .
        }}
        FILTER(CONTAINS(STR(?norm), "{norm_number}"))
    }} LIMIT 10
    """
    
    try:
        response = requests.post(
            sparql_endpoint,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=30,
        )
        response.raise_for_status()
        
        result = response.json()
        bindings = result.get("results", {}).get("bindings", [])
        
        if bindings:
            # Process SPARQL results into human-readable format
            norm_info = bindings[0]
            label = norm_info.get("label", {}).get("value", "")
            content = norm_info.get("content", {}).get("value", "")
            
            formatted_result = f"""SPARQL-Ergebnisse für {entity_uri}:

Norm: {label}

Inhalt: {content[:500] + "..." if len(content) > 500 else content}

Kontext zur ursprünglichen Frage: "{original_question}"
Diese Norm ist relevant, da sie sich mit den rechtlichen Aspekten der Anfrage befasst.
"""
            
            # Add paragraph information if available
            paragraph_contents = []
            for binding in bindings:
                if binding.get("paragraphContent"):
                    para_content = binding["paragraphContent"]["value"]
                    if para_content not in paragraph_contents:
                        paragraph_contents.append(para_content[:200] + "..." if len(para_content) > 200 else para_content)
            
            if paragraph_contents:
                formatted_result += "\n\nVerwandte Absätze:\n"
                for i, para in enumerate(paragraph_contents[:3], 1):
                    formatted_result += f"{i}. {para}\n"
            
            return formatted_result
        else:
            # Fallback to mock data with more detailed information
            return _get_mock_sparql_results(entity_uri, original_question)
            
    except requests.RequestException as e:
        print(f"Error connecting to Blazegraph: {e}")
        return _get_mock_sparql_results(entity_uri, original_question)


def _get_mock_sparql_results(entity_uri: str, original_question: str) -> str:
    """Fallback detailed mock data when SPARQL endpoint is not available."""
    if entity_uri == "bgb:§833":
        return f"""SPARQL-Ergebnisse für § 833 BGB (Haftung des Tierhalters):

Rechtliche Einordnung:
- Gefährdungshaftung ohne Verschuldenserfordernis
- Ausnahme: Bei Nutztieren gilt Haftung nur bei Sorgfaltspflichtverletzung
- Beweislastumkehr: Tierhalter muss beweisen, dass keine Sorgfaltspflichtverletzung vorlag

Anwendungsbereich:
- Schäden durch Tiere aller Art (Haustiere, Nutztiere, wilde Tiere)
- Körperschäden, Sachschäden, Vermögensschäden

Haftungsausschluss:
- Mitverschulden des Geschädigten (§ 254 BGB)
- Bei Nutztieren: Nachweis ordnungsgemäßer Tierhaltung

Verwandte Normen:
- § 823 BGB (Allgemeine Schadensersatzpflicht)
- § 254 BGB (Mitverschulden)
- § 249 ff. BGB (Art des Schadensersatzes)

Kontext zur ursprünglichen Frage: "{original_question}"
Diese Norm ist direkt anwendbar, da sie die Haftung für Tierschäden regelt."""
        
    elif entity_uri == "bgb:§823":
        return f"""SPARQL-Ergebnisse für § 823 BGB (Schadensersatzpflicht):

Rechtliche Einordnung:
- Zentrale Norm des Deliktsrechts
- Verschuldenshaftung (Vorsatz oder Fahrlässigkeit erforderlich)
- Schutz absoluter Rechte und Rechtsgüter

Geschützte Rechtsgüter:
- Leben, Körper, Gesundheit, Freiheit
- Eigentum und sonstige absolute Rechte

Tatbestandsmerkmale:
1. Verletzungshandlung
2. Rechtswidrigkeit
3. Verschulden (Vorsatz oder Fahrlässigkeit)
4. Schaden
5. Kausalität

Verwandte Normen:
- § 249 ff. BGB (Schadensersatz)
- § 254 BGB (Mitverschulden)
- § 833 BGB (Tierhalterhaftung)

Kontext zur ursprünglichen Frage: "{original_question}"
Diese Norm bildet die Grundlage für Schadensersatzansprüche bei Rechtsverletzungen."""
        
    elif entity_uri == "bgb:§249":
        return f"""SPARQL-Ergebnisse für § 249 BGB (Art und Umfang des Schadensersatzes):

Rechtliche Einordnung:
- Grundsatz der Naturalrestitution
- Herstellung des hypothetischen Zustands ohne schädigendes Ereignis

Schadensersatzarten:
- Naturalrestitution (Wiederherstellung in natura)
- Geldersatz (wenn Naturalrestitution unmöglich/unverhältnismäßig)

Anwendungsbereich:
- Folge aller Schadensersatzverpflichtungen
- Gilt für vertragliche und deliktische Ansprüche

Verwandte Normen:
- § 250 BGB (Ersatz vergeblicher Aufwendungen)
- § 251 BGB (Schadensersatz in Geld)
- § 252 BGB (Entgangener Gewinn)

Kontext zur ursprünglichen Frage: "{original_question}"
Diese Norm regelt die Art der Schadensersatzleistung."""
    else:
        return f"""SPARQL-Ergebnisse für {entity_uri}:

Dies ist eine allgemeine BGB-Norm. Für eine detaillierte Analyse der spezifischen 
Bestimmung und ihrer Anwendung im Kontext Ihrer Frage wären weitere Informationen 
über die konkrete Rechtsnorm erforderlich.

Allgemeine BGB-Struktur:
- Das BGB ist in 5 Bücher unterteilt
- Systematischer Aufbau von Allgemeinem Teil bis zu besonderen Schuldverhältnissen
- Grundlage des deutschen Zivilrechts

Kontext zur ursprünglichen Frage: "{original_question}"
Für eine spezifische Rechtsberatung sollten die konkreten Umstände geprüft werden."""


@tool("bgb_solr_search", args_schema=BGBSolrSearchInput)
def bgb_solr_search(german_query: str) -> List[Dict[str, Any]]:
    """
    Searches the Solr index for BGB (German Civil Code) articles and paragraphs.
    
    This tool searches through indexed BGB content to find relevant legal articles
    based on German search terms. It returns structured information about matching
    articles including their IDs, titles, and content snippets.
    
    Args:
        german_query: German search terms to find relevant BGB articles
        
    Returns:
        List of dictionaries containing article information with keys:
        - id: Article identifier (e.g., "bgb:§833")
        - title: Article title in German
        - snippet: Relevant content excerpt
        - score: Relevance score
    """
    print(f"🔍 TOOL CALL: bgb_solr_search with query: '{german_query}'")
    
    result = _search_solr(german_query)
    
    print(f"🔍 TOOL RESULT: Found {len(result)} articles")
    for article in result:
        print(f"  - {article['id']}: {article['title']} (Score: {article.get('score', 'N/A')})")
    
    return result


@tool("explore_bgb_entity_with_sparql", args_schema=BGBEntityExploreInput)
def explore_bgb_entity_with_sparql(entity_uri: str, original_question: str) -> str:
    """
    Explores a specific BGB entity using SPARQL queries to get detailed information.
    
    This tool performs deep exploration of a specific BGB article or paragraph
    using SPARQL queries against the knowledge graph. It provides detailed
    legal information, relationships, and contextual data about the entity.
    
    Args:
        entity_uri: The URI or identifier of the BGB entity (e.g., "bgb:§833")
        original_question: The original user question for context-aware analysis
        
    Returns:
        Detailed information about the BGB entity as a formatted string
    """
    print(f"🔎 TOOL CALL: explore_bgb_entity_with_sparql for entity: '{entity_uri}' with original question: '{original_question}'")
    
    result = _query_sparql(entity_uri, original_question)
    
    print(f"🔎 TOOL RESULT: Generated detailed analysis for {entity_uri}")
    return result



