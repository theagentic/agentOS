from agents import discover_agents, create_agent_instance

def test_autoblog_agent():
    print("Testing autoblog agent integration...")
    
    # Test agent discovery
    agents = discover_agents()
    autoblog_agent_class = agents.get('autoblog')
    print(f"Autoblog agent class found: {autoblog_agent_class is not None}")
    
    if autoblog_agent_class:
        # Test agent instantiation
        agent = create_agent_instance('autoblog')
        print(f"Agent instance created: {agent is not None}")
        
        if agent:
            # Test agent capabilities
            print("\nAgent capabilities:")
            for capability in agent.get_capabilities():
                print(f"- {capability}")
            
            # Test help command
            print("\nTesting help command:")
            result = agent.process("help")
            print(result.get('message', 'No help message available'))
    
if __name__ == "__main__":
    test_autoblog_agent() 