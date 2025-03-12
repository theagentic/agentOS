"""
A simple test script to verify the natural language agent and router fixes work.
This just checks initialization and basic routing to ensure no infinite loops.
"""

import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_router_initialization():
    """Test that the router can initialize without infinite loops."""
    print("Testing router initialization...")
    
    try:
        from core.agent_router import AgentRouter
        
        # Create router instance
        router = AgentRouter()
        print(f"Router loaded with {len(router.agents)} agents")
        
        # Test if natural language agent is loaded
        if "natural_language" in router.agents:
            print("✓ Natural language agent loaded successfully")
        else:
            print("✗ Natural language agent not loaded")
        
        return True
    except Exception as e:
        print(f"✗ Error initializing router: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_natural_language_agent_init():
    """Test that the natural language agent can initialize without issues."""
    print("\nTesting natural language agent initialization...")
    
    try:
        from agents.natural_language.agent import NaturalLanguageAgent
        
        # Create agent instance
        agent = NaturalLanguageAgent()
        print(f"Agent initialized with {len(agent.available_agents)} available agents")
        
        # Test the agent works without Ollama by using fallback
        result = agent.process("What time is it?")
        print(f"Agent test result: {result.get('status')} - {result.get('message')}")
        
        return True
    except Exception as e:
        print(f"✗ Error initializing agent: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_simple_routing():
    """Test simple routing with and without NLP."""
    print("\nTesting simple routing...")
    
    try:
        from core.agent_router import AgentRouter
        
        # Create router instance
        router = AgentRouter()
        
        # Test direct command
        direct_command = "datetime time"
        print(f"Testing direct command: '{direct_command}'")
        result = router.process_command(direct_command)
        print(f"Direct result: {result.get('status')} - {result.get('message')}")
        
        # Test natural language command (should attempt NLP but might fallback)
        nl_command = "What time is it?"
        print(f"Testing natural language command: '{nl_command}'")
        result = router.process_command(nl_command)
        print(f"NL result: {result.get('status')} - {result.get('message')}")
        
        return True
    except Exception as e:
        print(f"✗ Error in routing test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing natural language agent and router fixes...")
    
    # Run tests
    router_ok = test_router_initialization()
    agent_ok = test_natural_language_agent_init()
    routing_ok = test_simple_routing()
    
    # Check results
    if router_ok and agent_ok and routing_ok:
        print("\n✓ All tests passed! The fixes seem to be working.")
        sys.exit(0)
    else:
        print("\n✗ Some tests failed. More debugging may be needed.")
        sys.exit(1) 