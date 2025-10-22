#!/usr/bin/env python3
"""
BGB Agent using Qwen-Agent Framework

This implementation follows the official Qwen-Agent documentation patterns
for function calling with proper message handling and response collection.
"""

import json
from typing import List, Dict, Any
from qwen_agent.llm import get_chat_model

# Import our tools
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langchain_service.tools import bgb_solr_search, explore_bgb_entity_with_sparql


class QwenAgentBGB:
    """
    BGB Agent using Qwen-Agent framework with native function calling.
    Following the official documentation patterns.
    """
    
    def __init__(self, model_server: str = "http://localhost:11434/v1", enable_thinking: bool = True):
        """
        Initialize the Qwen-Agent BGB assistant.
        
        Args:
            model_server: OpenAI-compatible API endpoint (Ollama default)
            enable_thinking: Whether to use Qwen's thinking mode for reasoning traces
        """
        
        # Initialize the Qwen model with function calling support
        self.llm = get_chat_model({
            "model": "qwen3:14B",  # This should match your Ollama model name
            "model_server": model_server,
            "api_key": "EMPTY",  # Ollama doesn't require real API key
            "generate_cfg": {
                "extra_body": {
                    "chat_template_kwargs": {"enable_thinking": enable_thinking}
                }
            }
        })
        
        self.enable_thinking = enable_thinking
        
        # Convert LangChain tools to Qwen-Agent function format
        self.functions = self._convert_tools_to_functions()
    
    def _convert_tools_to_functions(self) -> List[Dict]:
        """Convert LangChain tools to Qwen-Agent function format."""
        
        functions = [
            {
                "name": "bgb_solr_search",
                "description": "Searches the Solr index for BGB (German Civil Code) articles and paragraphs based on German search terms. Maximal 3 Aufrufe pro Funktion pro Anfrage!",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "german_query": {
                            "type": "string",
                            "description": "German search terms to find relevant BGB articles and paragraphs"
                        }
                    },
                    "required": ["german_query"]
                }
            },
            {
                "name": "explore_bgb_entity_with_sparql",
                "description": """Explores a specific BGB entity using SPARQL queries to get detailed legal information and relationships. Usually called after bgb_solr_search to explore specific entities.

BGB Ontology Overview:
Classes: bgb-onto:LegalCode, bgb-onto:Norm, bgb-onto:Paragraph, bgb-onto:LegalConcept
Properties: bgb-onto:hasNorm, bgb-onto:hasParagraph, bgb-onto:defines, bgb-onto:refersTo
Namespaces: bgb-onto: http://example.org/bgb/ontology/, bgb-data: http://example.org/bgb/data/""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "entity_uri": {
                            "type": "string",
                            "description": "The URI or identifier of the BGB entity to explore (e.g., 'bgb:§833' or full URI)"
                        },
                        "original_question": {
                            "type": "string",
                            "description": "The original user question for context-aware analysis"
                        }
                    },
                    "required": ["entity_uri", "original_question"]
                }
            }
        ]
        
        return functions
    
    def _call_bgb_solr_search(self, german_query: str):
        """Execute bgb_solr_search tool and return result."""
        return bgb_solr_search.invoke({"german_query": german_query})
    
    def _call_explore_bgb_entity(self, entity_uri: str, original_question: str):
        """Execute explore_bgb_entity_with_sparql tool and return result."""
        return explore_bgb_entity_with_sparql.invoke({
            "entity_uri": entity_uri,
            "original_question": original_question
        })
    
    def get_function_by_name(self, function_name: str):
        """Get function by name for execution following Qwen-Agent documentation."""
        function_map = {
            "bgb_solr_search": self._call_bgb_solr_search,
            "explore_bgb_entity_with_sparql": self._call_explore_bgb_entity
        }
        return function_map.get(function_name)
    
    
    def chat(self, user_question: str) -> Dict[str, Any]:
        """
        Process a user question with function calling following Qwen-Agent documentation.
        
        Args:
            user_question: User's question in German
            
        Returns:
            Dictionary containing the conversation history and final response
        """
        
        # Initialize messages following Qwen-Agent documentation pattern
        messages = [
            {
                "role": "system",
                "content": """Du bist ein hilfreicher Assistent für das deutsche Bürgerliche Gesetzbuch (BGB).

Du hast Zugang zu folgenden Funktionen:
- bgb_solr_search: Suche nach BGB-Paragraphen und rechtlichen Konzepten
- explore_bgb_entity_with_sparql: Detailanalyse von spezifischen BGB-Entitäten

WICHTIGE REGELN:
- Vermeide IDENTISCHE Abfragen: Nutze unterschiedliche Suchbegriffe
- Bei mehreren Aufrufen: Verwende verwandte aber VERSCHIEDENE Begriffe
- Maximal 3 Aufrufe pro Funktion pro Anfrage!

Antworte immer auf Deutsch und nutze die verfügbaren Funktionen für aktuelle, genaue Informationen."""
            },
            {
                "role": "user", 
                "content": user_question
            }
        ]
        
        conversation_history = []
        
        # Step 1: Initial model response with potential function calls
        print("🔄 Getting model response...")
        
        # Use the chat method as shown in Qwen-Agent documentation
        responses = []
        for response_batch in self.llm.chat(messages=messages, functions=self.functions):
            responses = response_batch
        
        # Add responses to messages and track conversation
        messages.extend(responses)
        conversation_history.extend(responses)
        
        # Step 2: Process function calls following the documentation pattern
        for message in responses:
            if self.enable_thinking and message.get("reasoning_content"):
                print(f"🧠 Reasoning: {message['reasoning_content'][:200]}...")
            
            if fn_call := message.get("function_call", None):
                fn_name: str = fn_call['name']
                fn_args: dict = json.loads(fn_call["arguments"])
                
                print(f"🛠️ Calling function: {fn_name}")
                print(f"📋 Arguments: {fn_args}")
                
                # Get function result following documentation pattern
                fn_res: str = json.dumps(self.get_function_by_name(fn_name)(**fn_args))
                
                print(f"📊 Result: {fn_res[:150]}...")
                
                # Add function result following Qwen-Agent format
                messages.append({
                    "role": "function",
                    "name": fn_name,
                    "content": fn_res,
                })
                
                conversation_history.append({
                    "role": "function",
                    "name": fn_name,
                    "content": fn_res,
                })
        
        # Step 3: Get final response following documentation pattern
        print("🔄 Getting final response...")
        final_responses = []
        for response_batch in self.llm.chat(messages=messages, functions=self.functions):
            final_responses = response_batch
        
        # Add final responses
        messages.extend(final_responses)
        conversation_history.extend(final_responses)
        
        return {
            "messages": conversation_history,
            "final_response": self._extract_final_response(conversation_history),
            "thinking_mode": self.enable_thinking
        }
    
    def _extract_final_response(self, conversation_history: List[Dict]) -> str:
        """Extract the final user-facing response."""
        for message in reversed(conversation_history):
            if message.get("role") == "assistant" and message.get("content") and not message.get("function_call"):
                return message["content"]
        return "No final response generated."
    

def create_qwen_agent_bgb(enable_thinking: bool = True):
    """Create a Qwen-Agent BGB assistant."""
    return QwenAgentBGB(enable_thinking=enable_thinking)


if __name__ == "__main__":
    # Test the Qwen-Agent implementation
    print("🚀 Testing Qwen-Agent BGB Implementation")
    print("=" * 60)
    
    # Test with thinking mode enabled
    agent_thinking = create_qwen_agent_bgb(enable_thinking=True)
    
    test_question = "Mein Hund hat eine teure Vase zerbrochen. Muss ich den Schaden bezahlen?"
    
    print(f"❓ Question: {test_question}")
    print("🧠 Thinking Mode: Enabled")
    
    try:
        result = agent_thinking.chat(test_question)
        
        print("\n✅ Final Response:")
        print("-" * 40)
        print(result["final_response"])
        
        print("\n📊 Summary:")
        print(f"- Total messages: {len(result['messages'])}")
        print(f"- Thinking mode: {result['thinking_mode']}")
        
    except (ConnectionError, TimeoutError, json.JSONDecodeError) as e:
        print(f"❌ Error: {e}")
        print("Make sure Ollama is running and qwen3:14B model is available")