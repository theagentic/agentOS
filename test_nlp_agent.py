"""
Test script for the Natural Language Processing Agent.

This script tests the NaturalLanguageAgent's ability to translate
natural language queries to specific agent commands.
"""

import os
import sys
import logging
from agents.natural_language.agent import NaturalLanguageAgent
from core.agent_router import AgentRouter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_nlp_agent():
    """Test the NaturalLanguageAgent with some example queries."""
    print("Testing Natural Language Processing Agent...")
    
    # Initialize the agent
    agent = NaturalLanguageAgent()
    
    # Check if Ollama is available
    try:
        import requests
        response = requests.get(agent.ollama_api_url + "/api/version", timeout=2)
        if response.status_code == 200:
            print(f"Ollama is running at {agent.ollama_api_url}")
            ollama_available = True
        else:
            print(f"Ollama returned status code {response.status_code}")
            ollama_available = False
    except Exception as e:
        print(f"Ollama is not available: {e}")
        print("\nPlease make sure Ollama is installed and running:")
        print("1. Download Ollama from https://ollama.com/download")
        print("2. Install and run Ollama")
        print("3. Pull the llama3.2:1b model: ollama pull llama3.2:1b")
        print("4. Run this test again")
        ollama_available = False
    
    if not ollama_available:
        print("\nSkipping NLP tests since Ollama is not available.")
        return
    
    # Test queries
    test_queries = [
        "What's the weather like today?",
        "Create a post for Twitter about AI advancements",
        "Open the document called budget report",
        "Play my favorite playlist on Spotify",
        "What time is it?",
        "Help me with file management"
    ]
    
    # Process each query
    for query in test_queries:
        print(f"\nProcessing query: '{query}'")
        result = agent.process(query)
        
        if result.get("status") == "success":
            print(f"✅ Translated to: {result.get('command')}")
            print(f"   Agent: {result.get('agent')}")
        else:
            print(f"❌ Failed: {result.get('message')}")

def test_router_integration():
    """Test the integration of the NLP agent with the router."""
    print("\nTesting Router Integration with NLP...")
    
    # Initialize the router
    router = AgentRouter()
    
    # Check if the natural_language agent is loaded
    if "natural_language" not in router.agents:
        print("❌ Natural language agent not loaded in router")
        return
    
    print("✅ Natural language agent loaded in router")
    
    # Test if natural language processing is enabled
    if not router.use_natural_language:
        print("❌ Natural language processing is disabled in router")
    else:
        print("✅ Natural language processing is enabled in router")
    
    # Test a natural language query through the router
    test_query = "What time is it?"
    print(f"\nRouting query through router: '{test_query}'")
    
    # Skip actual routing test if Ollama is not available
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=2)
        if response.status_code != 200:
            print("Skipping router test since Ollama is not available")
            return
    except Exception:
        print("Skipping router test since Ollama is not available")
        return
    
    try:
        result = router.process_command(test_query)
        print(f"Router result: {result.get('status')}")
        
        if "nlp_processed" in result:
            print(f"✅ Query was processed by NLP agent")
            print(f"   Original query: {result.get('original_query')}")
            if "command" in result:
                print(f"   Translated command: {result.get('command')}")
        else:
            print(f"❌ Query was not processed by NLP agent")
    except Exception as e:
        print(f"❌ Error testing router integration: {e}")

if __name__ == "__main__":
    test_nlp_agent()
    test_router_integration() 