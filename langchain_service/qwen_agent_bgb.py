#!/usr/bin/env python3
"""
BGB Agent using Qwen-Agent Framework

This implementation uses Qwen-Agent's native function calling support
instead of manual parsing. Much cleaner and more reliable!
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
        
        # Create function lookup for execution
        self.function_map = {
            "bgb_solr_search": self._call_bgb_solr_search,
            "explore_bgb_entity_with_sparql": self._call_explore_bgb_entity
        }
    
    def _convert_tools_to_functions(self) -> List[Dict]:
        """Convert LangChain tools to Qwen-Agent function format."""
        
        functions = [
            {
                "name": "bgb_solr_search",
                "description": "Searches the Solr index for BGB (German Civil Code) articles and paragraphs based on German search terms.",
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
                "description": """Explores a specific BGB entity using SPARQL queries to get detailed legal information and relationships. This is used after identifying the most relevant entity from search results. And ususally only after bgb_solr_search.
                
BGB Ontology Overview:
=====================
Classes:
- bgb-onto:LegalCode (the BGB itself)
- bgb-onto:Norm (individual paragraphs like § 833)  
- bgb-onto:Paragraph (subsections within norms)
- bgb-onto:LegalConcept (legal terms defined in paragraphs)

Key Properties:
- bgb-onto:hasNorm (LegalCode → Norm)
- bgb-onto:hasParagraph (Norm → Paragraph)
- bgb-onto:defines (Paragraph → LegalConcept)
- bgb-onto:refersTo (Paragraph → other Norms via references)
- bgb-onto:normIdentifier (Norm identifier like "§ 833")
- bgb-onto:textContent (full text of paragraphs)
- rdfs:label (human-readable labels)
- dcterms:title (titles of norms and legal code)

Namespaces:
- bgb-onto: http://example.org/bgb/ontology/
- bgb-data: http://example.org/bgb/data/

Example queries you can craft:
- Count norms: SELECT (COUNT(*) AS ?count) WHERE { ?s a bgb-onto:Norm . }
- Find concept definitions: SELECT ?concept ?label WHERE { ?concept a bgb-onto:LegalConcept ; rdfs:label ?label . }
- Get norm content: SELECT ?content WHERE { <bgb-data:norm_833> bgb-onto:hasParagraph/bgb-onto:textContent ?content . }""",
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
    
    def _call_bgb_solr_search(self, german_query: str) -> Dict[str, Any]:
        """Execute bgb_solr_search tool and return result."""
        try:
            result = bgb_solr_search.invoke({"german_query": german_query})
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _call_explore_bgb_entity(self, entity_uri: str, original_question: str) -> Dict[str, Any]:
        """Execute explore_bgb_entity_with_sparql tool and return result."""
        try:
            result = explore_bgb_entity_with_sparql.invoke({
                "entity_uri": entity_uri,
                "original_question": original_question
            })
            return {"success": True, "data": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_function_by_name(self, function_name: str):
        """Get function by name for execution."""
        return self.function_map.get(function_name)
    
    def chat(self, user_question: str) -> Dict[str, Any]:
        """
        Process a user question with automatic function calling.
        
        Args:
            user_question: User's question in German
            
        Returns:
            Dictionary containing the conversation history and final response
        """
        
        # Initialize conversation with system message
        messages = [
            {
                "role": "system",
                "content": """Du bist ein hilfreicher Assistent für das deutsche Bürgerliche Gesetzbuch (BGB).

Du hast Zugang zu folgenden Funktionen:
- bgb_solr_search: Suche nach BGB-Paragraphen und rechtlichen Konzepten
- explore_bgb_entity_with_sparql: Detailanalyse von spezifischen BGB-Entitäten mit SPARQL-Abfragen

Dein Vorgehen:
1. **Suche**: Verwende bgb_solr_search um relevante BGB-Paragraphen zu finden
2. **Erkunde**: Verwende explore_bgb_entity_with_sparql für Details der relevantesten Entität
3. **Statistiken**: Du kannst explore_bgb_entity_with_sparql mit SPARQL-Abfragen nutzen um Statistiken zu erhalten
4. **Antworte**: Fasse die Ergebnisse auf Deutsch zusammen

Antworte immer auf Deutsch und verwende die verfügbaren Funktionen um aktuelle, genaue Informationen zu liefern."""
            },
            {
                "role": "user", 
                "content": user_question
            }
        ]
        
        conversation_history = []
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Iteration {iteration} (Qwen-Agent)")
            
            # Get model response with potential function calls
            try:
                responses_generator = self.llm.chat(
                    messages=messages,
                    functions=self.functions
                )
                
                # Collect all responses from this iteration
                responses = []
                for response_batch in responses_generator:
                    # Handle streaming responses - wait for complete function calls
                    if isinstance(response_batch, list):
                        # Only add complete responses
                        for resp in response_batch:
                            if self._is_complete_response(resp):
                                responses.append(resp)
                    else:
                        if self._is_complete_response(response_batch):
                            responses.append(response_batch)
                
                # If no complete responses, take the last one from the stream
                if not responses and response_batch:
                    responses = [response_batch] if not isinstance(response_batch, list) else response_batch[-1:]
                
            except Exception as e:
                print(f"❌ Error in LLM call: {e}")
                break
            
            if not responses:
                print("⚠️ No responses received")
                break
            
            # Add responses to conversation
            messages.extend(responses)
            conversation_history.extend(responses)
            
            # Check for function calls and execute them
            function_calls_made = False
            
            for message in responses:
                if self.enable_thinking and message.get("reasoning_content"):
                    print(f"🧠 Reasoning: {message['reasoning_content'][:200]}...")
                
                if fn_call := message.get("function_call", None):
                    # Check if function call is complete
                    if not fn_call.get("arguments") or fn_call["arguments"] == "":
                        print("⚠️ Incomplete function call, waiting...")
                        continue
                        
                    function_calls_made = True
                    fn_name = fn_call['name']
                    
                    try:
                        fn_args = json.loads(fn_call["arguments"])
                    except json.JSONDecodeError:
                        print(f"⚠️ Invalid JSON in function arguments: {fn_call['arguments']}")
                        continue
                    
                    print(f"🛠️ Calling function: {fn_name}")
                    print(f"📋 Arguments: {fn_args}")
                    
                    # Execute the function
                    function_impl = self.get_function_by_name(fn_name)
                    if function_impl:
                        fn_result = function_impl(**fn_args)
                        fn_result_str = json.dumps(fn_result, ensure_ascii=False)
                        
                        print(f"📊 Result: {fn_result_str[:150]}...")
                        
                        # Add function result to messages
                        function_result_message = {
                            "role": "function",
                            "name": fn_name,
                            "content": fn_result_str
                        }
                        
                        messages.append(function_result_message)
                        conversation_history.append(function_result_message)
                    else:
                        print(f"❌ Unknown function: {fn_name}")
            
            # If no function calls were made, we're done
            if not function_calls_made:
                break
        
        # Get final response after all function calls
        if function_calls_made:
            print("\n🔄 Final Response Generation")
            try:
                final_responses_generator = self.llm.chat(
                    messages=messages,
                    functions=self.functions
                )
                
                final_responses = []
                for response_batch in final_responses_generator:
                    if isinstance(response_batch, list):
                        for resp in response_batch:
                            if resp.get("content") and not resp.get("function_call"):
                                final_responses.append(resp)
                    else:
                        if response_batch.get("content") and not response_batch.get("function_call"):
                            final_responses.append(response_batch)
                
                if final_responses:
                    messages.extend(final_responses)
                    conversation_history.extend(final_responses)
                    
            except Exception as e:
                print(f"⚠️ Error getting final response: {e}")
        
        return {
            "messages": conversation_history,
            "final_response": self._extract_final_response(conversation_history),
            "thinking_mode": self.enable_thinking,
            "iterations": iteration
        }
    
    def _is_complete_response(self, response: Dict) -> bool:
        """Check if a response is complete (has content or complete function call)."""
        if response.get("content"):
            return True
        
        fn_call = response.get("function_call")
        if fn_call and fn_call.get("name") and fn_call.get("arguments"):
            # Check if arguments is valid JSON
            try:
                json.loads(fn_call["arguments"])
                return True
            except json.JSONDecodeError:
                return False
        
        return False
    
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
    print(f"🧠 Thinking Mode: Enabled")
    
    try:
        result = agent_thinking.chat(test_question)
        
        print(f"\n✅ Final Response:")
        print("-" * 40)
        print(result["final_response"])
        
        print(f"\n📊 Summary:")
        print(f"- Iterations: {result['iterations']}")
        print(f"- Total messages: {len(result['messages'])}")
        print(f"- Thinking mode: {result['thinking_mode']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure Ollama is running and qwen3:14B model is available")