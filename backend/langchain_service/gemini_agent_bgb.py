#!/usr/bin/env python3
"""
BGB Agent using Google Gemini API

This implementation uses Google's Gemini API for function calling with proper
message handling and response collection, providing an alternative to the local Qwen model.
"""

import json
import os
from typing import List, Dict, Any
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool

# Import our tools
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.langchain_service.tools import bgb_solr_search, execute_bgb_sparql_query
from backend.langchain_service.prompts import BGB_SYSTEM_PROMPT

# Try to import checkpointer - it's optional
try:
    from backend.langchain_service.checkpointer import get_postgres_checkpointer, get_checkpointer_config
    CHECKPOINTER_AVAILABLE = True
except ImportError:
    CHECKPOINTER_AVAILABLE = False
    get_postgres_checkpointer = None
    get_checkpointer_config = None

class GeminiAgentBGB:
    """
    BGB Agent using Google Gemini API with native function calling.
    """

    def __init__(
        self,
        api_key: str = None,
        use_checkpointer: bool = True,
        model_name: str = "gemini-1.5-pro",
    ):
        """
        Initialize the Gemini BGB assistant.

        Args:
            api_key: Google API key for Gemini (can also be set via GOOGLE_API_KEY env var)
            use_checkpointer: Whether to use PostgresSaver for automatic persistence
            model_name: Gemini model to use (gemini-1.5-pro, gemini-1.5-flash, etc.)
        """
        
        # Configure Gemini API
        api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass api_key parameter.")
        
        genai.configure(api_key=api_key)
        
        # Initialize the Gemini model with function calling support
        self.functions = self._convert_tools_to_gemini_functions()
        self.tools = [Tool(function_declarations=self.functions)]
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=self.tools,
            system_instruction=BGB_SYSTEM_PROMPT
        )

        # Initialize PostgresSaver for automatic persistence
        self.checkpointer = None
        if use_checkpointer:
            if not CHECKPOINTER_AVAILABLE:
                print("⚠️ Warning: langgraph.checkpoint.postgres not available")
                print("   Continuing without automatic persistence")
                print("   To enable: pip install langgraph-checkpoint-postgres")
            else:
                try:
                    self.checkpointer = get_postgres_checkpointer()
                    print("✅ PostgresSaver initialized for automatic persistence")
                except Exception as e:
                    print(f"⚠️ Warning: Could not initialize PostgresSaver: {e}")
                    print("   Continuing without automatic persistence")

    def _convert_tools_to_gemini_functions(self) -> List[FunctionDeclaration]:
        """Convert LangChain tools to Gemini function declarations."""
        
        # Use the already imported tools
        tools = [bgb_solr_search, execute_bgb_sparql_query]
        functions = []
        
        for tool in tools:
            # Extract parameters from the tool's args_schema (Pydantic model)
            parameters = {"type": "object", "properties": {}, "required": []}
            
            if hasattr(tool, 'args_schema') and tool.args_schema:
                schema = tool.args_schema.model_json_schema()
                properties = schema.get('properties', {})
                required = schema.get('required', [])
                
                # Convert Pydantic schema to Gemini format
                gemini_properties = {}
                for prop_name, prop_info in properties.items():
                    gemini_properties[prop_name] = {
                        "type": prop_info.get("type", "string"),
                        "description": prop_info.get("description", "")
                    }
                
                parameters["properties"] = gemini_properties
                parameters["required"] = required
            
            # Create Gemini function declaration
            function_declaration = FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=parameters
            )
            
            functions.append(function_declaration)
        
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
        """Get function by name for execution."""
        function_map = {
            "bgb_solr_search": self._call_bgb_solr_search,
            "execute_bgb_sparql_query": self._call_execute_bgb_sparql_query,
        }
        return function_map.get(function_name)

    def chat(self, user_question: str, message_history: List[Dict[str, str]] = None, thread_id: str = None) -> Dict[str, Any]:
        """
        Process a user question with function calling using Gemini API.

        Args:
            user_question: The user's question
            message_history: Previous messages in the conversation (optional)
            thread_id: Thread ID for conversation persistence (optional)

        Returns:
            Dictionary containing the conversation history and final response
        """

        # If checkpointer is enabled and thread_id provided, load from checkpointer
        if self.checkpointer and thread_id:
            print(f"💾 Using PostgresSaver for thread: {thread_id}")
            config = get_checkpointer_config(thread_id)

            # Load existing conversation state from checkpointer
            state = self.checkpointer.get(config)
            if state and "messages" in state.get("values", {}):
                saved_messages = state["values"]["messages"]
                # Convert saved messages back to message_history format
                message_history = [
                    msg for msg in saved_messages
                    if msg.get("role") in ["user", "assistant", "model"]
                ]
                print(f"📜 Loaded {len(message_history)} messages from PostgresSaver")


        print("🔄 Getting Gemini response...")

        # Convert message history to Gemini format if provided
        gemini_history = []
        if message_history:
            print(f"📜 Loading {len(message_history)} messages from history...")
            for msg in message_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                # Convert roles to Gemini format (user/model)
                if role == "assistant":
                    role = "model"
                elif role == "system":
                    continue  # Skip system messages as they're in system_instruction
                
                gemini_history.append({
                    "role": role,
                    "parts": [content]
                })

        # Start chat session with history
        chat = self.model.start_chat(history=gemini_history)
        
        # Send new message
        response = chat.send_message(user_question)

        messages = [
            {"role": "user", "content": user_question},
        ]

        # Track function calls made
        function_calls_made = []

        # Handle function calls in a loop
        while True:
            has_function_calls = False
            
            # Check each part of the response for function calls
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        has_function_calls = True
                        fn_call = part.function_call
                        fn_name = fn_call.name
                        fn_args = dict(fn_call.args)

                        print(f"🛠️ Calling function: {fn_name}")
                        print(f"📋 Arguments: {fn_args}")

                        # Execute the function
                        try:
                            fn_result = self.get_function_by_name(fn_name)(**fn_args)
                            
                            # Convert result to string if it's not already
                            if isinstance(fn_result, (list, dict)):
                                fn_result_str = json.dumps(fn_result, ensure_ascii=False)
                            else:
                                fn_result_str = str(fn_result)

                            print(f"📊 Result: {fn_result_str[:150]}...")

                            # Store function call info
                            function_calls_made.append({
                                "name": fn_name,
                                "args": fn_args,
                                "result": fn_result_str
                            })

                            # Send function result back to model
                            # Create a function response using the genai.protos structure
                            function_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=fn_name,
                                    response={"result": fn_result_str}
                                )
                            )
                            response = chat.send_message([function_response])
                            
                        except Exception as e:
                            print(f"❌ Error executing function {fn_name}: {e}")
                            # Send error response back to model
                            error_response = genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=fn_name,
                                    response={"error": f"Fehler beim Ausführen der Funktion: {str(e)}"}
                                )
                            )
                            response = chat.send_message([error_response])
                        
                        break  # Only handle one function call per iteration
            
            if not has_function_calls:
                break

        # Add the final response to messages
        final_text = response.text if response.text else "Keine Antwort generiert."
        messages.append({
            "role": "model", 
            "content": final_text,
            "function_calls": function_calls_made
        })

        print("✅ Final response ready")
        
        # Save to checkpointer if enabled
        if self.checkpointer and thread_id:
            try:
                config = get_checkpointer_config(thread_id)

                # Prepare all messages for storage
                all_messages = []
                if message_history:
                    all_messages.extend(message_history)
                all_messages.extend(messages)

                checkpoint_data = {
                    "values": {
                        "messages": all_messages,
                        "final_response": final_text,
                    }
                }
                self.checkpointer.put(config, checkpoint_data, {})
                print(f"💾 Conversation saved to PostgresSaver")
            except Exception as e:
                print(f"⚠️ Warning: Could not save to checkpointer: {e}")

        return {
            "messages": messages,
            "final_response": final_text,
            "model": "gemini",
        }

    def _extract_final_response(self, messages: List[Dict]) -> str:
        """Extract the final user-facing response."""
        for message in reversed(messages):
            if (
                message.get("role") == "model"
                and message.get("content")
                and not message.get("function_calls")
            ):
                return message["content"]
        return "No final response generated."


def create_gemini_agent_bgb(api_key: str = None, model_name: str = "gemini-2.5-flash"):
    """Create a Gemini BGB assistant."""
    return GeminiAgentBGB(api_key=api_key, model_name=model_name)


if __name__ == "__main__":
    # Test the Gemini implementation
    print("🚀 Testing Gemini BGB Implementation")
    print("=" * 60)

    try:
        # Test with Gemini
        agent = create_gemini_agent_bgb()

        test_question = (
            "Mein Hund hat eine teure Vase zerbrochen. Muss ich den Schaden bezahlen?"
        )

        print(f"❓ Question: {test_question}")
        print("🤖 Model: Google Gemini")

        result = agent.chat(test_question)

        print("\n✅ Final Response:")
        print("-" * 40)
        print(result["final_response"])

        print("\n📊 Summary:")
        print(f"- Total messages: {len(result['messages'])}")
        print(f"- Model: {result['model']}")

    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("Please set your GOOGLE_API_KEY environment variable")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have a valid Google API key and internet connection")