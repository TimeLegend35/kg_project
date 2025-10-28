#!/usr/bin/env python3
"""
BGB AI Assistant CLI using Qwen-Agent

Command-line interface using Qwen-Agent's native function calling.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_service.qwen_agent_bgb import create_qwen_agent_bgb


def main():
    """Main entry point for the Qwen-Agent BGB assistant."""
    if len(sys.argv) < 2:
        print("🤖 BGB AI Assistant (Qwen-Agent)")
        print("=" * 40)
        print("Usage: python bgb_ai_qwen.py '<your question in German>'")
        print("\nExamples:")
        print("  python bgb_ai_qwen.py 'Mein Hund hat eine Vase zerbrochen. Muss ich zahlen?'")
        print("  python bgb_ai_qwen.py 'Was sind die Statistiken des BGB Knowledge Graphs?'")
        print("  python bgb_ai_qwen.py 'Informationen über Eheverträge'")
        print("\nFeatures:")
        print("  ✅ Native Qwen function calling")
        print("  ✅ Reasoning traces (thinking mode)")
        print("  ✅ Automatic tool selection")
        print("  ✅ Real-time function execution")
        sys.exit(1)
    
    user_question = " ".join(sys.argv[1:])
    
    print("🧠 BGB AI Assistant (Qwen-Agent with Function Calling)")
    print("=" * 70)
    print(f"Question: {user_question}")
    print("=" * 70)
    
    # Create the Qwen-Agent
    try:
        print("🔄 Initializing Qwen-Agent...")
        agent = create_qwen_agent_bgb(enable_thinking=True)
        
        print("🚀 Processing your question...")
        result = agent.chat(user_question)
        
        print("\n" + "=" * 50)
        print("📋 **FINAL ANSWER:**")
        print("=" * 50)
        print(result["final_response"])
        
        print("\n" + "=" * 50)
        print("📊 **EXECUTION SUMMARY:**")
        print("=" * 50)
        #print(f"🔄 Iterations: {result['iterations']}")
        print(f"💬 Total messages: {len(result['messages'])}")
        print(f"🧠 Thinking mode: {'Enabled' if result['thinking_mode'] else 'Disabled'}")
        
        # Count function calls
        function_calls = 0
        for message in result["messages"]:
            if message.get("function_call"):
                function_calls += 1
        
        print(f"🛠️ Function calls made: {function_calls}")
        
        # Show function call details
        if function_calls > 0:
            print(f"\n🔧 **FUNCTION CALLS MADE:**")
            call_count = 0
            for message in result["messages"]:
                if fn_call := message.get("function_call"):
                    call_count += 1
                    print(f"  {call_count}. {fn_call['name']}")
        
        print("=" * 70)
        
    except ImportError as e:
        print("❌ Import Error - Qwen-Agent not properly installed:")
        print(f"   {e}")
        print("\nTry:")
        print("   pipenv install qwen-agent")
        print("   or")
        print("   pip install qwen-agent")
        sys.exit(1)
        
    except ConnectionError as e:
        print("❌ Connection Error - Cannot reach Ollama:")
        print(f"   {e}")
        print("\nMake sure:")
        print("   1. Ollama is running: ollama serve")
        print("   2. Qwen model is available: ollama pull qwen3:14B")
        print("   3. Ollama is on default port 11434")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print("\nDebugging tips:")
        print("   1. Check if Ollama is running")
        print("   2. Verify qwen3:14B model is installed")
        print("   3. Check your Solr/SPARQL services are running")
        sys.exit(1)


if __name__ == "__main__":
    main()