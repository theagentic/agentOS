"""
Utility script to fix missing agent modules
"""
from pathlib import Path

def ensure_agent_files():
    """Create missing agent files with basic templates."""
    agents_dir = Path("agents")
    
    # List of agents that need files
    agents = ["autoblog", "datetime", "filemanage", "spotiauto"]
    
    for agent in agents:
        agent_dir = agents_dir / agent
        
        # Create agent directory if it doesn't exist
        agent_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = agent_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
        
        # Create agent.py with basic template
        agent_file = agent_dir / "agent.py"
        if not agent_file.exists():
            template = f'''
from core.agent_base import AgentBase

class {agent.capitalize()}Agent(AgentBase):
    def __init__(self):
        super().__init__()
        self.agent_id = "{agent}"
    
    def process(self, command: str):
        return {{
            "status": "info",
            "message": "This agent is not yet implemented.",
            "spoke": "This agent is not yet implemented."
        }}
'''
            agent_file.write_text(template.lstrip())
            
        # Create .env file if it doesn't exist
        env_file = agent_dir / ".env"
        if not env_file.exists():
            env_file.write_text(f"# Environment variables for {agent}\n")

if __name__ == "__main__":
    ensure_agent_files()
    print("Created missing agent files")
