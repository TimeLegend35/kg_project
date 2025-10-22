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
from langchain_service.tools import bgb_solr_search, execute_bgb_sparql_query


class QwenAgentBGB:
    """
    BGB Agent using Qwen-Agent framework with native function calling.
    Following the official documentation patterns.
    """

    def __init__(
        self,
        model_server: str = "http://localhost:11434/v1",
        enable_thinking: bool = True,
    ):
        """
        Initialize the Qwen-Agent BGB assistant.

        Args:
            model_server: OpenAI-compatible API endpoint (Ollama default)
            enable_thinking: Whether to use Qwen's thinking mode for reasoning traces
        """

        # Initialize the Qwen model with function calling support
        self.llm = get_chat_model(
            {
                "model": "qwen3:14B",  # This should match your Ollama model name
                "model_server": model_server,
                "api_key": "EMPTY",  # Ollama doesn't require real API key
                "generate_cfg": {
                    "extra_body": {
                        "chat_template_kwargs": {"enable_thinking": enable_thinking}
                    }
                },
            }
        )

        self.enable_thinking = enable_thinking

        # Convert LangChain tools to Qwen-Agent function format
        self.functions = self._convert_tools_to_functions()

    def _convert_tools_to_functions(self) -> List[Dict]:
        """Convert LangChain tools to Qwen-Agent function format dynamically."""
        
        # Use the already imported tools
        tools = [bgb_solr_search, execute_bgb_sparql_query]
        functions = []
        
        for tool in tools:
            # Extract function schema from LangChain tool
            function_def = {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Extract parameters from the tool's args_schema (Pydantic model)
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.model_json_schema()
                properties = schema.get('properties', {})
                required = schema.get('required', [])
                
                function_def["parameters"]["properties"] = properties
                function_def["parameters"]["required"] = required
            
            functions.append(function_def)
        
        return functions

    def _call_bgb_solr_search(self, german_query: str):
        """Execute bgb_solr_search tool and return result."""
        return bgb_solr_search.invoke({"german_query": german_query})

    def _call_execute_bgb_sparql_query(self, sparql_query: str, query_description: str):
        """Execute execute_bgb_sparql_query tool and return result."""
        return execute_bgb_sparql_query.invoke(
            {"sparql_query": sparql_query, "query_description": query_description}
        )

    def get_function_by_name(self, function_name: str):
        """Get function by name for execution following Qwen-Agent documentation."""
        function_map = {
            "bgb_solr_search": self._call_bgb_solr_search,
            "execute_bgb_sparql_query": self._call_execute_bgb_sparql_query,
        }
        return function_map.get(function_name)

    def chat(self, user_question: str) -> Dict[str, Any]:
        """
        Process a user question with function calling following Qwen-Agent documentation exactly.

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
- bgb_solr_search: Suche nach BGB-Paragraphen und rechtlichen Konzepten freitext suche
- execute_bgb_sparql_query: Führe dynamisch SPARQL-Abfragen gegen die BGB-Wissensbasis aus es hilft mit einer eintität aus der suche zu arbeiten.

Für SPARQL-Abfragen verwende diese Ontologie-Informationen:
- Klassen: bgb-onto:LegalCode, bgb-onto:Norm, bgb-onto:Paragraph, bgb-onto:LegalConcept
- Eigenschaften: bgb-onto:hasNorm, bgb-onto:hasParagraph, bgb-onto:textContent, bgb-onto:defines
- Namespaces: bgb-onto: <http://example.org/bgb/ontology/>, bgb-data: <http://example.org/bgb/data/>

Verwende diese Funktionen um genaue und aktuelle Informationen aus dem BGB zu finden.
Antworte immer auf Deutsch und gib klare, verständliche Antworten basierend auf den gesammelten Informationen.""",
            },
            {"role": "user", "content": user_question},
        ]

        # Process function calls following exact Qwen-Agent documentation pattern
        print("🔄 Getting model response...")
        responses = []
        for responses in self.llm.chat(messages=messages, functions=self.functions):
            pass
        messages.extend(responses)

        # Check and apply function calls exactly as documented
        for message in responses:
            if fn_call := message.get("function_call", None):
                fn_name: str = fn_call['name']
                fn_args: dict = json.loads(fn_call["arguments"])

                print(f"🛠️ Calling function: {fn_name}")
                print(f"📋 Arguments: {fn_args}")

                fn_res: str = json.dumps(self.get_function_by_name(fn_name)(**fn_args))

                print(f"📊 Result: {fn_res[:150]}...")

                messages.append({
                    "role": "function",
                    "name": fn_name,
                    "content": fn_res,
                })

        # Get final response
        print("🔄 Getting final response...")
        final_responses = []
        for final_responses in self.llm.chat(messages=messages, functions=self.functions):
            pass
        messages.extend(final_responses)

        return {
            "messages": messages,
            "final_response": self._extract_final_response(messages),
            "thinking_mode": self.enable_thinking,
        }

    def _extract_final_response(self, messages: List[Dict]) -> str:
        """Extract the final user-facing response."""
        for message in reversed(messages):
            if (
                message.get("role") == "assistant"
                and message.get("content")
                and not message.get("function_call")
            ):
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

    test_question = (
        "Mein Hund hat eine teure Vase zerbrochen. Muss ich den Schaden bezahlen?"
    )

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
