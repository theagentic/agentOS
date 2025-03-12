#!/usr/bin/env python3
"""
Test script for verifying the Electron app integration with the autoblog agent.
This simulates how the app would parse and route commands.
"""

from agents import create_agent_instance

def test_commands():
    """Test different command formats and verify agent_id is included."""
    print("\n=== Testing Autoblog Agent Electron Integration ===\n")
    
    # Create agent
    agent = create_agent_instance('autoblog')
    if not agent:
        print("Error: Could not initialize autoblog agent")
        return
    
    # Test commands
    commands = [
        "help",
        "blog-repo test-repo",
        "process-repo test-repo",  # Test backward compatibility
        "autoblog blog-repo test-repo",  # Test with prefix
        "autoblog process-repo test-repo"  # Test with prefix and old command
    ]
    
    for cmd in commands:
        print(f"\nTesting command: '{cmd}'")
        result = agent.process(cmd)
        
        # Extract and print key info
        agent_id = result.get('agent_id', 'MISSING')
        cmd_processed = result.get('command_processed', 'MISSING')
        status = result.get('status', 'MISSING')
        
        print(f"  Agent ID: {agent_id}")
        print(f"  Command Processed: {cmd_processed}")
        print(f"  Status: {status}")
        
        # Verification
        if agent_id != 'autoblog':
            print("  WARNING: Agent ID is incorrect!")
        else:
            print("  ✓ Agent ID is correct")
            
        if cmd_processed == 'MISSING':
            print("  WARNING: command_processed metadata is missing!")
        else:
            print("  ✓ Command processing metadata included")

if __name__ == "__main__":
    test_commands() 