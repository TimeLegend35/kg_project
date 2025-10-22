#!/usr/bin/env python3
"""
BGB AI Assistant CLI with Multiple Model Options

Command-line interface that can use either:
- Local Qwen model via Ollama (qwen_agent_bgb)
- Google Gemini API (gemini_agent_bgb)
"""

import sys
import os
import argparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Main entry point for the BGB assistant with model selection."""
    
    parser = argparse.ArgumentParser(
        description="BGB AI Assistant - Choose between local Qwen or cloud Gemini models"
    )
    parser.add_argument(
        "question", 
        nargs="?", 
        help="Your question about the German Civil Code (BGB) in German"
    )
    parser.add_argument(
        "--model", 
        choices=["qwen", "gemini"], 
        default="qwen",
        help="Choose the AI model: qwen (local) or gemini (cloud). Default: qwen"
    )
    parser.add_argument(
        "--gemini-model",
        default="gemini-2.5-flash",
        help="Specific Gemini model to use (default: gemini-2.5-flash)"
    )
    
    args = parser.parse_args()
    
    if not args.question:
        print("🤖 BGB AI Assistant - Multi-Model")
        print("=" * 50)
        print("Usage: python bgb_ai_multi.py [--model qwen|gemini] '<your question in German>'")
        print("\nModel Options:")
        print("  --model qwen     : Use local Qwen model via Ollama (default)")
        print("  --model gemini   : Use Google Gemini API (requires GOOGLE_API_KEY)")
        print("\nExamples:")
        print("  python bgb_ai_multi.py 'Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?'")
        print("  python bgb_ai_multi.py --model gemini 'Was sind die Statistiken des BGB?'")
        print("  python bgb_ai_multi.py --model qwen 'Informationen über Eheverträge'")
        print("\nFeatures:")
        print("  ✅ Dynamic tool selection")
        print("  ✅ Real-time function execution")
        print("  ✅ Multiple AI model backends")
        print("  ✅ Automatic SPARQL and Solr integration")
        sys.exit(1)
    
    user_question = args.question
    model_choice = args.model
    
    print(f"🧠 BGB AI Assistant - {model_choice.upper()} Model")
    print("=" * 70)
    print(f"Question: {user_question}")
    print(f"Model: {model_choice}")
    print("=" * 70)
    
    try:
        if model_choice == "qwen":
            print("🔄 Initializing Qwen Agent (Local)...")
            from langchain_service.qwen_agent_bgb import create_qwen_agent_bgb
            agent = create_qwen_agent_bgb(enable_thinking=True)
            
        elif model_choice == "gemini":
            print("🔄 Initializing Gemini Agent (Cloud)...")
            from langchain_service.gemini_agent_bgb import create_gemini_agent_bgb
            agent = create_gemini_agent_bgb(model_name=args.gemini_model)
        
        print("🚀 Processing your question...")
        result = agent.chat(user_question)
        
        print("\n" + "=" * 50)
        print("📋 **FINAL ANSWER:**")
        print("=" * 50)
        print(result["final_response"])
        
        print("\n" + "=" * 50)
        print("📊 **EXECUTION SUMMARY:**")
        print("=" * 50)
        print(f"💬 Total messages: {len(result['messages'])}")
        print(f"🤖 Model used: {model_choice}")
        
        if model_choice == "qwen" and result.get("thinking_mode"):
            print(f"🧠 Thinking mode: {'Enabled' if result['thinking_mode'] else 'Disabled'}")
        
        # Count function calls
        function_calls = 0
        for message in result["messages"]:
            if message.get("function_call") or message.get("function_calls"):
                if message.get("function_call"):
                    function_calls += 1
                elif message.get("function_calls"):
                    function_calls += len(message["function_calls"])
        
        print(f"🛠️ Function calls made: {function_calls}")
        
        # Show function call details
        if function_calls > 0:
            print(f"\n🔧 **FUNCTION CALLS MADE:**")
            call_count = 0
            for message in result["messages"]:
                # Qwen format
                if fn_call := message.get("function_call"):
                    call_count += 1
                    print(f"  {call_count}. {fn_call['name']}")
                # Gemini format
                elif fn_calls := message.get("function_calls"):
                    for fn_call in fn_calls:
                        call_count += 1
                        print(f"  {call_count}. {fn_call['name']}")
        
        print("=" * 70)
        
    except ImportError as e:
        if "google.generativeai" in str(e):
            print("❌ Gemini API not available - Install google-generativeai:")
            print("   pipenv install google-generativeai")
            print("   or")
            print("   pip install google-generativeai")
        elif "qwen_agent" in str(e):
            print("❌ Qwen Agent not available - Install qwen-agent:")
            print("   pipenv install qwen-agent")
            print("   or") 
            print("   pip install qwen-agent")
        else:
            print(f"❌ Import Error: {e}")
        sys.exit(1)
        
    except ValueError as e:
        if "GOOGLE_API_KEY" in str(e):
            print("❌ Google API Key Missing:")
            print("   Set your GOOGLE_API_KEY environment variable")
            print("   export GOOGLE_API_KEY='your-api-key-here'")
            print("   or")
            print("   Get an API key from: https://makersuite.google.com/app/apikey")
        else:
            print(f"❌ Configuration Error: {e}")
        sys.exit(1)
        
    except ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        if model_choice == "qwen":
            print("\nMake sure:")
            print("   1. Ollama is running: ollama serve")
            print("   2. Qwen model is available: ollama pull qwen3:14B")
            print("   3. Ollama is on default port 11434")
        elif model_choice == "gemini":
            print("\nMake sure:")
            print("   1. You have internet connection")
            print("   2. Your Google API key is valid")
            print("   3. Gemini API quota is not exceeded")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("\nDebugging tips:")
        print("   1. Check your model configuration")
        print("   2. Verify API keys and service availability")
        print("   3. Check your Solr/SPARQL services are running")
        sys.exit(1)


if __name__ == "__main__":
    main()